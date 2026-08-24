"""
script_path: src/protolib/core/registry.py
description: >-
  Defines RegistryClient, RegistryHost, and ApiIntrospector classes for service discovery
  and API introspection. The client sends registration and heartbeat payloads to a remote
  host, while the host stores service state in a JSON file with TTL-based expiration. The
  introspector scans the local apis directory to extract function signatures for capability
  reporting. Consumed by protolib packages needing inter-service communication.
tags:
- infra
- parsing
- settings
update_rules: Do not modify in clones.
"""
import importlib, inspect, json, os, socket
import threading, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

import protolib.core.settings as sts
from protolib.helpers.printing import logprint

PY2JSON = {str: "string", int: "integer", float: "number",
           bool: "boolean", list: "array", dict: "object"}


# ---------------------------------------------------------------------------
# Registry Client
# ---------------------------------------------------------------------------


class RegistryClient:
    """
    description: Sends registration + heartbeat to a registry host.
    """

    def __init__(self, *args, sid: str = None, registry_url: str = None, **kwargs):
        """description: 'Set service id, registry URL, and empty state cache.'"""
        self.sid = sid or sts.package_name
        self.registry_url = registry_url or getattr(sts, 'registry_url', None) \
            or f"http://127.0.0.1:{sts.registry_port}"
        self._cached_state = {}

    def emit(self, data: dict, *args, **kwargs) -> dict:
        """description: 'Wrap data in registry envelope, send to host, cache non-empty reply.'"""
        payload = json.dumps({"id": self.sid, "data": data}).encode()
        req = urllib.request.Request(self.registry_url, data=payload)
        req.add_header("Content-Type", "application/json")
        state = self._send(req, *args, **kwargs)
        if state: self._cached_state = state
        return state

    def _send(self, req, *args, **kwargs) -> dict:
        """description: 'Single network boundary — POST request, return state dict or empty on error.'"""
        try:
            with urllib.request.urlopen(req, timeout=2) as res:
                state = json.loads(res.read() or b'{}')
            return state if "services" in state else self._fetch_state(*args, **kwargs)
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError):
            return {}

    def _fetch_state(self, *args, **kwargs) -> dict:
        """description: 'GET /state from registry host; return parsed JSON or empty on error.'"""
        try:
            url = f"{self.registry_url}/state"
            with urllib.request.urlopen(url, timeout=2) as res:
                return json.loads(res.read())
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError,
                OSError, json.JSONDecodeError):
            return {}

    def heartbeat(self, *args, ttl: int = None, **kwargs) -> dict:
        """description: 'Emit a minimal TTL payload to keep the service registration alive.'"""
        return self.emit({"ttl": ttl or 30}, *args, **kwargs)

    def register_with_capabilities(self, *args, ttl: int = None, **kwargs) -> dict:
        """description: 'Emit registration with host, port, ttl, and introspected API signatures.'"""
        ttl = ttl or 30
        return self.emit({
            "host": getattr(sts, 'service_host', None) or socket.gethostname(),
            "port": getattr(sts, 'port', None),
            "ttl": ttl,
            "apis": ApiIntrospector(*args, **kwargs).get_api_signatures(*args, **kwargs),
        }, *args, **kwargs)

    def discover(self, service_id: str, *args, fresh: bool = False, **kwargs) -> dict | None:
        """description: 'Return cached service entry for service_id; fetch fresh state if requested.'"""
        if fresh:
            self._cached_state = self._fetch_state(*args, **kwargs)
        return self._cached_state.get("services", {}).get(service_id)

    def discover_url(self, service_id: str, *args, **kwargs) -> str | None:
        """description: 'Resolve service_id to an http://host:port URL from cached state.'"""
        svc = self.discover(service_id, *args, **kwargs)
        if svc and svc.get("port"):
            host = svc.get("host") or svc.get("ip") or socket.gethostname()
            return f"http://{host}:{svc['port']}"
        return None

    def start_heartbeat_loop(self, *args, interval=60, ttl=None, **kwargs) -> None:
        """description: 'Launch daemon thread that registers then heartbeats every interval seconds.'"""
        hb_ttl = ttl or interval * 2
        kw = dict(target=self._heartbeat_loop, daemon=True, name="registry-heartbeat")
        threading.Thread(**kw, args=(interval, hb_ttl)).start()

    def _heartbeat_loop(self, interval, hb_ttl, *args, **kwargs):
        """description: 'Register once on start, then send heartbeat every interval seconds.'"""
        self.register_with_capabilities(*args, ttl=hb_ttl, **kwargs)
        while True:
            time.sleep(interval)
            self.heartbeat(*args, ttl=hb_ttl, **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return f"RegistryClient(*args, sid={self.sid!r}, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Service id and registry URL.'"""
        return f"RegistryClient({self.sid} -> {self.registry_url})"


class RegistryHost:
    """
    description: Stores service state, responds with full registry.
    """

    BASE_STATE = {"services": {}, "shared": {}}
    DEFAULT_TTL = 30
    _lock = threading.Lock()

    def __init__(self, *args, state_file: str = None, **kwargs):
        """description: 'Resolve state file path and ensure it exists on disk.'"""
        self.state_file = Path(state_file or sts.registry_state_file)
        self._ensure_state_file(*args, **kwargs)

    @property
    def now(self, *args, **kwargs) -> str:
        """description: 'Current UTC timestamp as ISO 8601 string.'"""
        return datetime.now(timezone.utc).isoformat()

    def _ensure_state_file(self, *args, **kwargs) -> None:
        """description: 'Create state file with BASE_STATE if it does not yet exist.'"""
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_state(dict(self.BASE_STATE), *args, **kwargs)

    def read_state(self, *args, **kwargs) -> dict:
        """description: 'Load state under lock, ensuring services and shared keys present.'"""
        with self._lock:
            state = self._load_state(*args, **kwargs)
            state.setdefault("services", {})
            state.setdefault("shared", {})
            return state

    def _load_state(self, *args, **kwargs) -> dict:
        """description: 'Read and parse state file; return BASE_STATE on missing or corrupt file.'"""
        try:
            raw = self.state_file.read_text()
            return json.loads(raw) if raw.strip() else dict(self.BASE_STATE)
        except (json.JSONDecodeError, FileNotFoundError):
            return dict(self.BASE_STATE)

    def _write_state(self, state: dict, *args, **kwargs) -> None:
        """description: 'Stamp last_update, write via tmp rename under lock — atomic single boundary.'"""
        with self._lock:
            state["last_update"] = self.now
            tmp = self.state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2))
            tmp.rename(self.state_file)

    def register_service(self, sid: str, data: dict, *args, **kwargs) -> dict:
        """description: 'Route sid to shared or service slot, persist state, return updated state.'"""
        state = self.read_state(*args, **kwargs)
        if sid.startswith("__shared_"):
            self._register_shared(state, sid, data, *args, **kwargs)
        else:
            self._register_svc(state, sid, data, *args, **kwargs)
        self._write_state(state, *args, **kwargs)
        return state

    def _register_shared(self, state, sid, data, *args, **kwargs):
        """description: 'Write data into state["shared"] keyed by sid stripped of __shared_ prefix.'"""
        key = sid.replace("__shared_", "")
        state["shared"][key] = {**data, "last_update": self.now}

    def _register_svc(self, state, sid, data, *args, **kwargs):
        """description: 'Upsert service entry with data, stamp last_seen, run TTL check.'"""
        entry = state["services"].get(sid, {})
        entry.update(data)
        entry["last_seen"] = self.now
        entry["status"] = "active"
        state["services"][sid] = entry
        self._check_all_ttl(state, *args, **kwargs)

    def _check_all_ttl(self, state: dict, now: str = None, *args, **kwargs) -> None:
        """description: 'Run TTL check on every service entry in state.'"""
        for svc in state.get("services", {}).values():
            self._check_ttl(svc, now or self.now, *args, **kwargs)

    def _check_ttl(self, svc: dict, now: str = None, *args, **kwargs) -> None:
        """description: 'Skip already-inactive entries; delegate elapsed-time check to _apply_ttl.'"""
        if svc.get("status") in ("inactive", "missing"):
            return
        last_seen = svc.get("last_seen", "")
        if not last_seen:
            return
        self._apply_ttl(svc, last_seen, now or self.now, *args, **kwargs)

    def _apply_ttl(self, svc, last_seen, now: str = None, *args, **kwargs):
        """description: 'Mark svc status stale when elapsed seconds exceed its ttl value.'"""
        try:
            end = datetime.fromisoformat(now or self.now)
            start = datetime.fromisoformat(last_seen)
            if (end - start).total_seconds() > svc.get("ttl", self.DEFAULT_TTL):
                svc["status"] = "stale"
        except ValueError:
            pass

    def start_sweep_loop(self, *args, interval: int = 10, **kwargs) -> None:
        """description: 'Launch daemon thread that runs TTL sweep every interval seconds.'"""
        kw = dict(target=self._sweep_loop, daemon=True, name="ttl-sweep")
        threading.Thread(**kw, args=(interval,)).start()

    def _sweep_loop(self, interval, *args, **kwargs):
        """description: 'Sleep interval seconds then call _run_sweep in a perpetual loop.'"""
        while True:
            time.sleep(interval)
            self._run_sweep(*args, **kwargs)

    def _run_sweep(self, *args, **kwargs):
        """description: 'Read state, check all TTLs, write result; log error on exception.'"""
        try:
            state = self.read_state(*args, **kwargs)
            self._check_all_ttl(state, *args, **kwargs)
            self._write_state(state, *args, **kwargs)
        except Exception:
            logprint("sweep error", *args, level="error", **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return f"RegistryHost(*args, state_file={str(self.state_file)!r}, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'State file path for this registry host.'"""
        return f"RegistryHost({self.state_file})"


class ApiIntrospector:
    """
    description: Inspects this package's APIs and returns their signatures.
    """

    def __init__(self, *args, **kwargs):
        """description: 'No instance state — all work done via method calls.'"""
        pass

    def _read_signature(self, func, *args, **kwargs) -> dict:
        """description: 'Extract named parameter schemas from func signature via inspect.'"""
        props = {}
        for name, p in inspect.signature(func).parameters.items():
            if name in {"self", "cls"} or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue
            props[name] = _param_schema(p, *args, **kwargs)
        return props

    def _scan_api_dir(self, *args, apis_dir: str, apis: dict, **kwargs):
        """description: 'Walk apis_dir and load each eligible module signature into apis dict.'"""
        if not os.path.isdir(apis_dir):
            return
        for filename in os.listdir(apis_dir):
            entry = self._load_api(filename, *args, **kwargs)
            if entry:
                apis[entry[0]] = entry[1]

    def get_api_signatures(self, *args, **kwargs) -> dict:
        """description: 'Scan all api_packages dirs and return merged name→signature dict.'"""
        apis = {}
        for apis_dir, pkg_prefix in sts.api_packages:
            self._scan_api_dir(*args, apis_dir=apis_dir,
                pkg_prefix=pkg_prefix, apis=apis, **kwargs)
        return apis

    def _load_api(self, filename, *args, **kwargs):
        """description: 'Filter filename and delegate to _import_api; skip server module.'"""
        if not filename.endswith(".py") or filename.startswith(("_", "#")):
            return None
        api_name = os.path.splitext(filename)[0]
        if api_name == "server":
            return None
        return self._import_api(api_name, *args, **kwargs)

    def _import_api(self, api_name, *args, pkg_prefix: str, **kwargs):
        """description: 'Import api_name module and return (name, signature dict) or None on failure.'"""
        try:
            mod = importlib.import_module(f"{pkg_prefix}.{api_name}")
            if not hasattr(mod, "main"):
                return None
            sig = self._read_signature(mod.main, *args, **kwargs)
            return api_name, {"parameters": sig, "docstring": (mod.main.__doc__ or "").strip()}
        except Exception:
            return None

    def get_service_info(self, *args, **kwargs) -> dict:
        """description: 'Return service identity dict with id, host, port, and API signatures.'"""
        return {
            "id": sts.package_name,
            "host": getattr(sts, 'service_host', None) or socket.gethostname(),
            "port": getattr(sts, 'port', None),
            "apis": self.get_api_signatures(*args, **kwargs),
        }

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "ApiIntrospector(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Package whose APIs this introspector scans.'"""
        return f"ApiIntrospector({sts.package_name})"


# ---------- module-level helpers ----------

def _param_schema(p, *args, **kwargs):
    """description: 'Map inspect.Parameter to JSON schema dict with type, default, required.'"""
    ann = p.annotation if p.annotation is not inspect._empty else object
    return {
        "type": PY2JSON.get(ann, "object"),
        "default": None if p.default is inspect._empty else p.default,
        "required": p.default is inspect._empty,
    }
