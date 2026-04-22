"""
script_path: src/protolib/core/apis/server.py
purpose: HTTP server for protolib and all cloned packages.
description: |-
  Discovers API modules from
  core/apis/ and app/apis/ at startup and dispatches GET/POST requests to their
  main() functions.
"""
import http.server, json, socketserver, os, importlib
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


class ProtoControlHandler(http.server.SimpleHTTPRequestHandler):
    """
    purpose: Request handler — discovers and runs available API modules.
    """
    available_apis = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def load_apis(cls, *args, **kwargs):
        """
        purpose: Scan core/apis/ and app/apis/ directories for API modules.
        """
        cls.available_apis = {}
        skip = os.path.splitext(os.path.basename(__file__))[0]
        for apis_dir, pkg_prefix in _API_DIRS:
            cls._scan_dir(*args, apis_dir=apis_dir, pkg_prefix=pkg_prefix, skip=skip, **kwargs)

    @classmethod
    def _scan_dir(cls, *args, apis_dir: str, pkg_prefix: str, skip: str, **kwargs):
        if not os.path.isdir(apis_dir):
            return
        for fn in os.listdir(apis_dir):
            mod = cls._try_load_api(fn, skip, *args, pkg_prefix=pkg_prefix, **kwargs)
            if mod:
                cls.available_apis[mod[0]] = mod[1]

    @classmethod
    def _try_load_api(cls, filename: str, skip: str, *args, pkg_prefix: str, **kwargs):
        if not filename.endswith(".py") or filename.startswith(("_", "#")):
            return None
        name = os.path.splitext(filename)[0]
        if name == skip:
            return None
        return cls._import_api(name, *args, pkg_prefix=pkg_prefix, **kwargs)

    @classmethod
    def _import_api(cls, name: str, *args, pkg_prefix: str, **kwargs):
        try: mod = importlib.import_module(f"{pkg_prefix}.{name}")
        except Exception as e:
            logprint(f"Failed to load API '{name}': {e}", level="error")
            return None
        if not hasattr(mod, "main"): return None
        logprint(f"Loaded API: '{name}'")
        return name, mod

    def do_GET(self, *args, **kwargs):
        """
        purpose: Route GET to matching API or list available APIs.
        """
        parsed = urlparse(self.path)
        api_name = parsed.path.strip("/")
        api_mod = self.available_apis.get(api_name)
        if api_mod:
            self._handle_get(api_name, api_mod, parsed, *args, **kwargs)
        else:
            self._list_apis(api_name, *args, **kwargs)

    def _handle_get(self, name, api_mod, parsed, *args, **kwargs):
        try:
            resp = self.run_api_command(
                *args, api_module=api_mod, parsed_url=parsed, **kwargs)
            self._send_ok_response(resp, *args, **kwargs)
        except Exception as e:
            self.send_error(500, f"Error executing API '{name}': {e}")
            logprint(f"Failed API '{name}': {e}", level="error")

    def _list_apis(self, api_name, *args, **kwargs):
        apis = list(self.available_apis.keys())
        content = (f"API '{api_name}' not found.\n"
                   f"Available APIs: {apis}\n"
                   f"Uri: http://localhost:{sts.port}/info/?infos=package")
        self._send_ok_response(content, *args, **kwargs)

    def do_POST(self, *args, **kwargs):
        """
        purpose: Route POST /announce to registry handler.
        """
        parsed = urlparse(self.path)
        api_name = parsed.path.strip("/")
        if api_name == "announce":
            self._handle_announce(*args, **kwargs)
        else:
            self.send_error(404, f"POST not supported for '{api_name}'")

    def _handle_announce(self, *args, **kwargs):
        try:
            self._dispatch_announce(*args, **kwargs)
        except Exception as e:
            self.send_error(500, f"POST /announce error: {e}")
            logprint(f"POST /announce error: {e}", level="error")

    def _dispatch_announce(self, *args, **kwargs):
        body = self._read_body(*args, **kwargs)
        if not getattr(sts, 'registry_host_enabled', False):
            self._send_json_response({"error": "not enabled"}, 403)
            return
        state = _handle_registration(body, *args, **kwargs)
        self._send_json_response(state, 200, *args, **kwargs)

    def _read_body(self, *args, **kwargs) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length > 0 else {}

    def _send_json_response(self, data: dict, code: int, *args, **kwargs):
        """
        purpose: Send a JSON response.
        """
        response = json.dumps(data, indent=2)
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def _run_api(self, *args, api_module, params: dict, **kwargs) -> str:
        """
        purpose: Run API and capture returned output.
        """
        with contextlib.redirect_stdout(io.StringIO()):
            rv = api_module.main(*args, **params)
        return rv if isinstance(rv, str) else ""

    def _send_ok_response(self, content: str, *args, **kwargs):
        """
        purpose: Send 200 OK with ANSI→HTML conversion.
        """
        html = _ansi2html.convert(content)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def run_api_command(self, *args, api_module, parsed_url, **kwargs) -> str:
        """
        purpose: Parse query string, run API, return output.
        """
        qp = parse_qs(parsed_url.query)
        params = _build_params(qp)
        return self._run_api(*args, api_module=api_module, params=params, **kwargs)

def _build_params(query_params: dict, *args, **kwargs) -> dict:
    """
    purpose: Convert parsed query string dict to typed params for API dispatch.
    """
    result = {}
    for key, vals in query_params.items():
        if not vals:
            continue
        result[key] = vals if key == "infos" else _cast_value(vals[0])
    result.setdefault("verbose", 0)
    return result

def _cast_value(val: str, *args, **kwargs):
    """
    purpose: Cast a query string value to int, bool, or str.
    """
    if val.isdigit():
        return int(val)
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    return val

def _start_heartbeat(*args, **kwargs):
    try:
        client = RegistryClient(*args, **kwargs)
        client.start_heartbeat_loop(
            *args, interval=sts.registry_heartbeat_interval, **kwargs)
        logprint("Registry heartbeat started")
    except Exception:
        logprint("Registry heartbeat not started", level="warning")

def _start_sweep(*args, **kwargs):
    if not getattr(sts, 'registry_host_enabled', False):
        return
    try:
        RegistryHost(*args, **kwargs).start_sweep_loop(*args, **kwargs)
        logprint("Registry host TTL sweep started")
    except Exception:
        logprint("Registry host sweep not started", level="warning")

def _serve(port: int, handler, *args, **kwargs):
    with socketserver.TCPServer(("", port), handler) as httpd:
        msg = f"{sts.package_name} server starting on port {port}"
        logprint(msg)
        logprint(f"APIs: {list(handler.available_apis.keys())}")
        httpd.serve_forever()

def run_server(*args, port: int = None, verbose: int = 1, **kwargs):
    """
    purpose: Set up and run the HTTP server indefinitely.
    """
    port = int(port) if port is not None else sts.port
    ProtoControlHandler.load_apis(*args, **kwargs)
    _start_heartbeat(*args, **kwargs)
    _start_sweep(*args, **kwargs)
    _serve(port, ProtoControlHandler, *args, **kwargs)

def main(*args, **kwargs):
    run_server(*args, **kwargs)


if __name__ == "__main__":
    main()
