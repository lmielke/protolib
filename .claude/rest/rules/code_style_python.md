---
script_path: .claude/rules/code_style_python.md
description: >-
  Defines the authoritative Python code style for the protolib repository, including a gold-standard
  class example and single-line rules. It mandates specific patterns like c5 argument forwarding
  and settings imports. Agents consult this file before writing or reviewing Python modules
  to ensure alignment with governance checks.
tags:
- docs
- governance
- rule
update_rules: Update requires explicit approval.
paths:
- '**/*.py'
---

See also: 
@rules/developer_guidelines.md,
@rules/test_gov.md

# Python Code Style

## Gold-Standard Class

Write every new module using this style and format. Every choice is annotated
with the why — copy the pattern, not just the syntax.

```python
"""
script_path: src/mypackage/core/registry.py
description: "Two cooperating classes form a minimal service registry with no
  external broker. RegistryClient is the outbound side: it emits a registration
  payload over HTTP and turns discovered records into base URLs. RegistryHost is
  the passive side: it merges service data into a persisted JSON state file and
  stamps each write. The HTTP transport and the file are the only moving parts... (80+ words)"
"""
# imports at top, alphabetical, no in-function imports — c_dorph + c5 hygiene
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path
# package-static globals belong in settings.py, not inline literals
from mypackage import settings as sts
# sibling class from another module — composed in register_with_capabilities
from mypackage.core.introspect import ApiIntrospector

# module-level constant: shared across this module only, not a settings entry
ACTIVE_STATUS = "active"


class RegistryClient:
    """
    description: "Owns the registry URL and a cache of the last state the host returned. emit() ... (50+ words)"
    """

    # class-wide constant: same content type for every instance, immutable label
    content_type = "application/json"

    def __init__(self, *args, sid: str = None, port: int = None, **kwargs):
        # named kwargs consume the contract; `value or default` falls back to settings
        self.sid = sid or sts.package_name
        self.url = f"http://{sts.ip}:{port or sts.registry_port}"
        # shape: {sid(str): {"status": str, "url": str}}
        self._state = {}

    def emit(self, data: dict, *args, **kwargs) -> dict:
        """
        description: "Wraps the caller's data in the registry envelope, sends it, and keeps the reply only ... (20+ words)"
        """
        # envelope built inline — no throwaway local just to be passed once
        payload = json.dumps({"id": self.sid, "data": data}).encode()
        # NOTE: this could be shortened even more, by inlining the payload definition inside the call
        state = self._send(payload, *args, **kwargs)
        # guard: cache only a real reply, never an empty error response
        if state: self._state = state
        return state

    def register_with_capabilities(self, *args, ttl: int = None, **kwargs) -> dict:
        """
        description: "Emit a registration enriched with this service's introspected API map, forwarding it ... (20+ words)"
        """
        # forward the API map whole — emit() wraps it; never index a field of it
        return self.emit({
            "sid": self.sid, "status": ACTIVE_STATUS, "url": self.url,
            "ttl": ttl or sts.registry_ttl,
            "apis": ApiIntrospector(*args, **kwargs).get_api_signatures(*args, **kwargs)},
            *args, **kwargs)

    def _send(self, payload: bytes, *args, **kwargs) -> dict:
        """
        description: "The single network boundary. try/except is scoped to the expected transport failures (Fail Loud everywhere ... (20+ words)"
        """
        req = urllib.request.Request(self.url, data=payload)
        req.add_header("Content-Type", self.content_type)
        try:
            with urllib.request.urlopen(req, timeout=2) as res:
                return json.loads(res.read() or b"{}")
        except (urllib.error.URLError, TimeoutError, OSError):
            return {}

    def discover_url(self, service_id: str, *args, **kwargs) -> str | None:
        """
        description: "Returns the base URL a prior registration stored for service_id, or None when ... (20+ words)"
        """
        # value-or-None: the entry already carries its url — no host/port recomposition
        return (self._state.get("services", {}).get(service_id) or {}).get("url")


class RegistryHost:
    """
    description: "Holds the registry in memory and mirrors it to a JSON file, stamping every write ... (50+ words)"
    """

    # class-wide default: the empty shape every fresh host starts from
    # shape: {"services": {sid(str): {"status": str, "url": str}}}
    base_state = {"services": {}}

    def __init__(self, *args, state_file: str = None, **kwargs):
        # path resolved once; settings supplies the default location
        self.state_file = Path(state_file or sts.registry_state_file)
        self._state = dict(self.base_state)

    def register_service(self, sid: str, data: dict, *args, **kwargs) -> dict:
        """
        description: "Coordinator only: it delegates the per-entry merge to _register_svc and the durability to _write_state, so ... (20+ words)"
        """
        # linear flow: delegate the merge, then persist and return the result
        self._register_svc(self._state, sid, data, *args, **kwargs)
        return self._write_state(self._state, *args, **kwargs)

    def _register_svc(self, state: dict, sid: str, data: dict, *args, **kwargs) -> None:
        """
        description: "Starts from any existing entry so a partial update never wipes prior fields, layers the ... (20+ words)"
        """
        # upsert: seed from the current entry so partial updates don't clobber
        entry = state["services"].get(sid, {})
        entry.update(data)
        entry["status"] = ACTIVE_STATUS
        state["services"][sid] = entry

    def _write_state(self, state: dict, *args, **kwargs) -> dict:
        """
        description: "The single source of truth for what reaches disk: it sets last_update to a fresh ... (20+ words)"
        """
        # timestamp read at the write boundary, not passed down through signatures
        state["last_update"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))
        return state
```

## Single-Line Rules

- Always `def f(self, *args, **kwargs)` — `c5` is mandatory.
- Forward `*args, **kwargs` on every internal call.
- Named kwargs *consume* the contract; `kwargs.get(...)` is forbidden.
- Chain calls: `f(g(h(x, **kw), **kw), **kw)` over intermediate locals.
- Use comprehensions, not `for x: append`. Bind to a local only past `c15`.
- Use syntactic sugar: ternary return, `value or default`, when it pays.
- No pipe-through unpacking — don't unpack only to repack the same dict.
- No single-use locals. Inline assign-and-use.
- No in-function imports. Top of file, alphabetical.
- One return per function where readable; early-return guards allowed.
- Static globals → `settings.py`, imported as `sts`.
- Module-level constants for module-only data; class attributes for class-wide.
- Instance state in `__init__`, never as a class attribute.
- Method chaining via composition; pass-through wrappers are deleted.
- Built-ins over custom: `any()`, `all()`, `getattr()`, `setattr()`, `zip()`.
- f-strings, tuple unpacking (`a, b = b, a`), no `eval()` / `exec()`.
- Simple type annotations: `str`, `int`, `list[str]`. Avoid the `typing` module.
- No empty rows inside a function/method. (disturbs def selector tool)

## Module Skeleton

Docstring template: `~/.governance/docstring_templates.yml` (validated by
`c_dfmt`, `c_dscope`, `c_dorph`).

| Pattern              | When                                                    |
| -------------------- | ------------------------------------------------------- |
| Class                | Standard backend code — stateful, low user interaction  |
| Function             | Stateless helpers meant to be imported frequently       |
| Notebook / spaghetti | Code-as-documentation, working scratch files            |

Function-shrinking patterns and check-code reference: @rules/test_gov.md
§Definition Patterns.
