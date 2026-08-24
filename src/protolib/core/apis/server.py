"""
script_path: src/protolib/core/apis/server.py
description: >-
  Serves HTTP requests for protolib and cloned packages by discovering API modules in core
  and app directories at startup. Routes GET and POST requests to the main functions of loaded
  modules, handling JSON responses and HTML rendering. Integrates with the registry client
  for service announcements and heartbeat monitoring.
tags:
- cli
- hook
- infra
"""
import http.server, json, socketserver, os, importlib, re
from urllib.parse import urlparse, parse_qs
import io, contextlib
from colorama import Fore, Style
from ansi2html import Ansi2HTMLConverter
import protolib.core.settings as sts
from protolib.helpers.printing import logprint
from protolib.core.apis.announce import _handle_registration
from protolib.core.registry import RegistryClient, RegistryHost

_API_DIRS = [
    (os.path.join(sts.package_dir, "core", "apis"), f"{sts.package_name}.core.apis"),
    (os.path.join(sts.package_dir, "app", "apis"), f"{sts.package_name}.app.apis"),
]

_ansi2html = Ansi2HTMLConverter(inline=True, dark_bg=True)
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class ProtoControlHandler(http.server.SimpleHTTPRequestHandler):
    """
    description: Request handler — discovers and runs available API modules.
    """
    available_apis = {}

    def __init__(self, *args, **kwargs):
        """description: 'Initialize handler via parent SimpleHTTPRequestHandler.'"""
        super().__init__(*args, **kwargs)

    @classmethod
    def load_apis(cls, *args, **kwargs):
        """
        description: Scan core/apis/ and app/apis/ directories for API modules.
        """
        cls.available_apis = {}
        skip = os.path.splitext(os.path.basename(__file__))[0]
        for apis_dir, pkg_prefix in _API_DIRS:
            cls._scan_dir(*args, apis_dir=apis_dir, pkg_prefix=pkg_prefix, skip=skip, **kwargs)

    @classmethod
    def _scan_dir(cls, *args, apis_dir: str, skip: str, **kwargs):
        """description: 'Walk apis_dir and load each eligible .py file into available_apis.'"""
        if not os.path.isdir(apis_dir):
            return
        for fn in os.listdir(apis_dir):
            mod = cls._try_load_api(fn, skip, *args, **kwargs)
            if mod:
                cls.available_apis[mod[0]] = mod[1]

    @classmethod
    def _try_load_api(cls, filename: str, skip: str, *args, **kwargs):
        """description: 'Filter filename and delegate to _import_api; return (name, mod) or None.'"""
        if not filename.endswith(".py") or filename.startswith(("_", "#")):
            return None
        name = os.path.splitext(filename)[0]
        if name == skip:
            return None
        return cls._import_api(name, *args, **kwargs)

    @classmethod
    def _import_api(cls, name: str, *args, pkg_prefix: str, **kwargs):
        """description: 'Import module by pkg_prefix.name; return (name, mod) if main exists.'"""
        try: mod = importlib.import_module(f"{pkg_prefix}.{name}")
        except Exception as e:
            logprint(f"Failed to load API '{name}': {e}", *args, level="error", **kwargs)
            return None
        if not hasattr(mod, "main"): return None
        logprint(f"Loaded API: '{name}'", *args, **kwargs)
        return name, mod

    def do_GET(self, *args, **kwargs):
        """
        description: Route GET to matching API or list available APIs.
        """
        parsed = urlparse(self.path)
        api_name = parsed.path.strip("/")
        api_mod = self.available_apis.get(api_name)
        if api_mod:
            self._handle_get(api_name, api_mod, parsed, *args, **kwargs)
        else:
            self._list_apis(api_name, *args, **kwargs)

    def _handle_get(self, name, api_mod, parsed, *args, **kwargs):
        """description: 'Run named API module and send response; emit 500 on exception.'"""
        try:
            resp = self.run_api_command(
                *args, api_module=api_mod, parsed_url=parsed, **kwargs)
            self._send_ok_response(resp, *args, **kwargs)
        except Exception as e:
            self.send_error(500, f"Error executing API '{name}': {e}")
            logprint(f"Failed API '{name}': {e}", *args, level="error", **kwargs)

    def _list_apis(self, api_name, *args, **kwargs):
        """description: 'Send plain-text listing of available API names when api_name not found.'"""
        apis = list(self.available_apis.keys())
        content = (f"API '{api_name}' not found.\n"
                   f"Available APIs: {apis}\n"
                   f"Uri: http://localhost:{sts.port}/info/?infos=package")
        self._send_ok_response(content, *args, **kwargs)

    def do_POST(self, *args, **kwargs):
        """
        description: Route POST /announce to registry handler.
        """
        parsed = urlparse(self.path)
        api_name = parsed.path.strip("/")
        if api_name == "announce":
            self._handle_announce(*args, **kwargs)
        else:
            self.send_error(404, f"POST not supported for '{api_name}'")

    def _handle_announce(self, *args, **kwargs):
        """description: 'Wrap _dispatch_announce with a 500 error guard for POST /announce.'"""
        try:
            self._dispatch_announce(*args, **kwargs)
        except Exception as e:
            self.send_error(500, f"POST /announce error: {e}")
            logprint(f"POST /announce error: {e}", *args, level="error", **kwargs)

    def _dispatch_announce(self, *args, **kwargs):
        """description: 'Read body, gate on registry_host_enabled, delegate to _handle_registration.'"""
        body = self._read_body(*args, **kwargs)
        if not getattr(sts, 'registry_host_enabled', False):
            self._send_json_response({"error": "not enabled"}, 403, *args, **kwargs)
            return
        state = _handle_registration(body, *args, **kwargs)
        self._send_json_response(state, 200, *args, **kwargs)

    def _read_body(self, *args, **kwargs) -> dict:
        """description: 'Read and JSON-decode POST body using Content-Length header.'"""
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length > 0 else {}

    def _send_json_response(self, data: dict, code: int, *args, **kwargs):
        """
        description: Send a JSON response.
        """
        response = json.dumps(data, indent=2)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))
        return

    def _run_api(self, *args, api_module, params: dict, **kwargs):
        """
        description: Run API and capture returned output (str, dict, or list).
        """
        with contextlib.redirect_stdout(io.StringIO()):
            rv = api_module.main(*args, **params)
        return rv if isinstance(rv, (str, dict, list)) else ""

    def _send_ok_response(self, content, *args, **kwargs):
        """
        description: Send 200 OK, negotiating JSON or ANSI→HTML output.
        """
        if self._negotiate(*args, **kwargs) == "json":
            self._send_json_response(self._as_json(content, *args, **kwargs), 200, *args, **kwargs)
        else:
            self._send_html_response(content, *args, **kwargs)

    def _negotiate(self, *args, **kwargs) -> str:
        """
        description: Pick output format from ?format override, else Accept header.
        """
        fmt = parse_qs(urlparse(self.path).query).get("format", [None])[0]
        if fmt in ("json", "html"): return fmt
        return "html" if "text/html" in self.headers.get("Accept", "") else "json"

    def _as_json(self, content, *args, **kwargs):
        """
        description: Wrap API output as a JSON-serializable object.
        """
        if isinstance(content, (dict, list)): return content
        return {"result": _strip_ansi(content, *args, **kwargs)}

    def _send_html_response(self, content, *args, **kwargs):
        """
        description: Send 200 OK with ANSI→HTML conversion.
        """
        text = content if isinstance(content, str) else json.dumps(content, indent=2)
        html = _ansi2html.convert(text)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def run_api_command(self, *args, parsed_url, **kwargs):
        """
        description: Parse query string, run API, return output.
        """
        qp = parse_qs(parsed_url.query)
        params = _build_params(qp, *args, **kwargs)
        return self._run_api(*args, params=params, **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "ProtoControlHandler(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Available API names loaded into this handler.'"""
        return f"ProtoControlHandler(apis={list(self.available_apis.keys())})"

def _build_params(query_params: dict, *args, **kwargs) -> dict:
    """
    description: Convert parsed query string dict to typed params for API dispatch.
    """
    result = {}
    for key, vals in query_params.items():
        if not vals or key == "format":
            continue
        result[key] = vals if key == "infos" else _cast_value(vals[0], *args, **kwargs)
    result.setdefault("verbose", 0)
    return result

def _strip_ansi(text: str, *args, **kwargs) -> str:
    """
    description: Remove ANSI color escape codes from a string.
    """
    return _ANSI_RE.sub("", text)

def _cast_value(val: str, *args, **kwargs):
    """
    description: Cast a query string value to int, bool, or str.
    """
    if val.isdigit():
        return int(val)
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    return val

def _start_heartbeat(*args, **kwargs):
    """description: 'Start registry heartbeat loop in a daemon thread; log if unavailable.'"""
    try:
        client = RegistryClient(*args, **kwargs)
        client.start_heartbeat_loop(
            *args, interval=sts.registry_heartbeat_interval, **kwargs)
        logprint("Registry heartbeat started", *args, **kwargs)
    except Exception:
        logprint("Registry heartbeat not started", *args, level="warning", **kwargs)

def _start_sweep(*args, **kwargs):
    """description: 'Start TTL sweep loop when registry_host_enabled; log if unavailable.'"""
    if not getattr(sts, 'registry_host_enabled', False):
        return
    try:
        RegistryHost(*args, **kwargs).start_sweep_loop(*args, **kwargs)
        logprint("Registry host TTL sweep started", *args, **kwargs)
    except Exception:
        logprint("Registry host sweep not started", *args, level="warning", **kwargs)

def _serve(port: int, handler, *args, **kwargs):
    """description: 'Bind TCPServer on port with handler and serve forever.'"""
    with socketserver.TCPServer(("", port), handler) as httpd:
        msg = f"{sts.package_name} server starting on port {port}"
        logprint(msg, *args, **kwargs)
        logprint(f"APIs: {list(handler.available_apis.keys())}", *args, **kwargs)
        httpd.serve_forever()

def run_server(*args, port: int = None, **kwargs):
    """
    description: Set up and run the HTTP server indefinitely.
    """
    port = int(port) if port is not None else sts.port
    ProtoControlHandler.load_apis(*args, **kwargs)
    _start_heartbeat(*args, **kwargs)
    _start_sweep(*args, **kwargs)
    _serve(port, ProtoControlHandler, *args, **kwargs)

def main(*args, **kwargs):
    """description: 'CLI entry point — delegate to run_server.'"""
    run_server(*args, **kwargs)


if __name__ == "__main__":
    main()
