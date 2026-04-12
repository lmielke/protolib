# registry.py
"""
Registry connector classes for service discovery and API introspection.

RegistryClient  — outbound registration + heartbeat + service discovery.
RegistryHost    — passive host that stores service state in a JSON file.
ApiIntrospector — scans this package's apis/ directory and returns signatures.
"""

# Standard library imports in alphabetical order
import importlib
import inspect
import json
import logging
import os
import socket
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Local application imports in alphabetical order
import protolib.settings as sts

log = logging.getLogger("registry")


def _resolve_host(*args, **kwargs) -> str:
    """Return this machine's hostname. In Docker, returns the container name for DNS resolution."""
    return socket.gethostname()


# ---------------------------------------------------------------------------
# Registry Client
# ---------------------------------------------------------------------------

class RegistryClient:
    """Outbound registry client. Sends registration + heartbeat to a registry host."""

    def __init__(self, *args, sid: str = None, registry_url: str = None, **kwargs):
        self.sid = sid or sts.package_name
        self.registry_url = registry_url or getattr(sts, 'registry_url', None) \
            or f"http://127.0.0.1:{sts.registry_port}"
        self._cached_state = {}

    def emit(self, data: dict, *args, **kwargs) -> dict:
        """POST registration to registry. Returns full registry state or {} on failure."""
        payload = json.dumps({"id": self.sid, "data": data}).encode()
        req = urllib.request.Request(self.registry_url, data=payload)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=2) as res:
                body = res.read()
                state = json.loads(body) if body else {}
                # Backwards compat: old registry returns {"ok": true} without state.
                # Fetch full state via GET /state if response lacks "services".
                if "services" not in state:
                    state = self._fetch_state(*args, **kwargs)
                self._cached_state = state
                return state
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError):
            return {}

    def _fetch_state(self, *args, **kwargs) -> dict:
        """GET /state from registry. Fallback for registries that don't return state on POST."""
        try:
            url = f"{self.registry_url}/state"
            with urllib.request.urlopen(url, timeout=2) as res:
                return json.loads(res.read())
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError,
                json.JSONDecodeError):
            return {}

    def heartbeat(self, *args, ttl: int = None, **kwargs) -> dict:
        """Lightweight liveness ping. Returns registry state."""
        return self.emit({"ttl": ttl or 30}, *args, **kwargs)

    def register_with_capabilities(self, *args, ttl: int = None, **kwargs) -> dict:
        """Full registration including API capabilities from ApiIntrospector."""
        ttl = ttl or 30
        introspector = ApiIntrospector(*args, **kwargs)
        data = {
            "host": getattr(sts, 'service_host', None) or _resolve_host(),
            "port": getattr(sts, 'port', None),
            "ttl": ttl,
            "apis": introspector.get_api_signatures(*args, **kwargs),
        }
        return self.emit(data, *args, **kwargs)

    def discover(self, service_id: str, *args, fresh: bool = False, **kwargs) -> dict | None:
        """Look up a service from cached registry state. Use fresh=True for live lookup."""
        if fresh:
            self._cached_state = self._fetch_state(*args, **kwargs)
        return self._cached_state.get("services", {}).get(service_id)

    def discover_url(self, service_id: str, *args, **kwargs) -> str | None:
        """Look up a service and return its base URL, or None if not found."""
        svc = self.discover(service_id, *args, **kwargs)
        if svc and svc.get("port"):
            host = svc.get("host") or svc.get("ip") or _resolve_host()
            return f"http://{host}:{svc['port']}"
        return None

    def start_heartbeat_loop(self, *args, interval: int = 60, **kwargs) -> None:
        """Background thread: initial register_with_capabilities, then heartbeat every interval."""
        loop_kwargs = dict(kwargs, ttl=kwargs.get('ttl') or interval * 2)
        def _loop():
            self.register_with_capabilities(*args, **loop_kwargs)
            while True:
                time.sleep(interval)
                self.heartbeat(*args, **loop_kwargs)

        t = threading.Thread(target=_loop, daemon=True, name="registry-heartbeat")
        t.start()


# ---------------------------------------------------------------------------
# Registry Host
# ---------------------------------------------------------------------------

class RegistryHost:
    """Passive registry host. Stores service state, responds with full registry."""

    BASE_STATE = {"services": {}, "shared": {}}
    DEFAULT_TTL = 30
    _lock = threading.Lock()

    def __init__(self, *args, state_file: str = None, **kwargs):
        self.state_file = Path(state_file or sts.registry_state_file)
        self._ensure_state_file(*args, **kwargs)

    def _ensure_state_file(self, *args, **kwargs) -> None:
        """Create state file with base state if it does not exist."""
        if not self.state_file.exists():
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_state(dict(self.BASE_STATE), *args, **kwargs)

    def _read_state(self, *args, **kwargs) -> dict:
        """Read current state from file under lock."""
        with self._lock:
            try:
                raw = self.state_file.read_text()
                state = json.loads(raw) if raw.strip() else dict(self.BASE_STATE)
            except (json.JSONDecodeError, FileNotFoundError):
                state = dict(self.BASE_STATE)
            state.setdefault("services", {})
            state.setdefault("shared", {})
            return state

    def _write_state(self, state: dict, *args, **kwargs) -> None:
        """Write state to file under lock (atomic via tmp + rename)."""
        with self._lock:
            state["last_update"] = datetime.now(timezone.utc).isoformat()
            tmp = self.state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2))
            tmp.rename(self.state_file)

    def register_service(self, sid: str, data: dict, *args, **kwargs) -> dict:
        """Store/update a service entry. Returns full state."""
        now = datetime.now(timezone.utc).isoformat()
        state = self._read_state(*args, **kwargs)
        if sid.startswith("__shared_"):
            key = sid.replace("__shared_", "")
            state["shared"][key] = {**data, "last_update": now}
        else:
            entry = state["services"].get(sid, {})
            entry.update(data)
            entry["last_seen"] = now
            entry["status"] = "active"
            state["services"][sid] = entry
            self._check_all_ttl(state, now, *args, **kwargs)
        self._write_state(state, *args, **kwargs)
        return state

    def get_state(self, *args, **kwargs) -> dict:
        """Read and return current registry state."""
        return self._read_state(*args, **kwargs)

    def _check_all_ttl(self, state: dict, now: str, *args, **kwargs) -> None:
        """Check TTL for all services in state."""
        for svc in state.get("services", {}).values():
            self._check_ttl(svc, now, *args, **kwargs)

    def _check_ttl(self, svc: dict, now: str, *args, **kwargs) -> None:
        """Mark a service as stale if last_seen exceeds TTL."""
        status = svc.get("status")
        if status in ("inactive", "missing"):
            return
        last_seen = svc.get("last_seen", "")
        if not last_seen:
            return
        ttl = svc.get("ttl", self.DEFAULT_TTL)
        try:
            delta = (
                datetime.fromisoformat(now) - datetime.fromisoformat(last_seen)
            ).total_seconds()
            if delta > ttl:
                svc["status"] = "stale"
        except ValueError:
            pass

    def start_sweep_loop(self, *args, interval: int = 10, **kwargs) -> None:
        """Background thread: periodic TTL sweep."""
        def _sweep():
            while True:
                time.sleep(interval)
                try:
                    now = datetime.now(timezone.utc).isoformat()
                    state = self._read_state(*args, **kwargs)
                    self._check_all_ttl(state, now, *args, **kwargs)
                    self._write_state(state, *args, **kwargs)
                except Exception:
                    log.exception("sweep: error in TTL sweep")

        t = threading.Thread(target=_sweep, daemon=True, name="ttl-sweep")
        t.start()


# ---------------------------------------------------------------------------
# API Introspector
# ---------------------------------------------------------------------------

class ApiIntrospector:
    """Inspects this package's APIs and returns their signatures."""

    PY2JSON = {str: "string", int: "integer", float: "number",
               bool: "boolean", list: "array", dict: "object"}

    def __init__(self, *args, **kwargs):
        pass

    def _read_signature(self, func, *args, **kwargs) -> dict:
        """Build a parameter map from a function's signature."""
        props = {}
        for name, p in inspect.signature(func).parameters.items():
            if name in {"self", "cls"} or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue
            ann = p.annotation if p.annotation is not inspect._empty else object
            json_type = self.PY2JSON.get(ann, "object")
            props[name] = {
                "type": json_type,
                "default": None if p.default is inspect._empty else p.default,
                "required": p.default is inspect._empty,
            }
        return props

    def get_api_signatures(self, *args, **kwargs) -> dict:
        """Scan apis/ directory, return signatures for all modules with main()."""
        apis = {}
        apis_dir = sts.apis_dir
        if not os.path.isdir(apis_dir):
            return apis
        for filename in os.listdir(apis_dir):
            if not filename.endswith(".py") or filename.startswith(("_", "#")):
                continue
            api_name = os.path.splitext(filename)[0]
            if api_name == "server":
                continue
            try:
                pkg_import_name = os.path.basename(sts.package_dir)
                module_path = f"{pkg_import_name}.apis.{api_name}"
                module = importlib.import_module(module_path)
                if hasattr(module, "main"):
                    sig = self._read_signature(module.main, *args, **kwargs)
                    apis[api_name] = {
                        "parameters": sig,
                        "docstring": (module.main.__doc__ or "").strip(),
                    }
            except Exception:
                pass
        return apis

    def get_service_info(self, *args, **kwargs) -> dict:
        """Full service descriptor: id, host, port, apis."""
        return {
            "id": sts.package_name,
            "host": getattr(sts, 'service_host', None) or _resolve_host(),
            "port": getattr(sts, 'port', None),
            "apis": self.get_api_signatures(*args, **kwargs),
        }
