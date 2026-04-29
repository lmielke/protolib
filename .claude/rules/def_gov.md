---
script_path: /home/lars/repos/protolib/.claude/rules/def_gov.md
paths: ["**/*.py"]
purpose: "Catalogue of named refactoring patterns for shrinking Python functions — gold-standard exemplars and step-by-step transforms for the c1 (≤7 lines) and c11 (≤95 chars) checks."
description: "Governance-authoritative reference. Apply the patterns in sequencing order (Trust → Fail Loud → Put in Place → ... → Sweeten) until the function fits. Each pattern includes a real protolib before/after; preservation invariant: every move keeps behaviour."
update_rules: "Append new patterns with a name, heuristic, and real protolib example."
---

See also: @rules/code_style_python.md (designer summary), @rules/module_gov.md (module skeleton).

# Definition Rules — Patterns for Shrinking Functions

Methods/functions must be shorter than 7 code lines (comments and docstrings
excluded). Rule `c1` enforces this at test time and is mandatory-fix — no
docstring suppression. Rule `c11` (line length ≤ 95) is also mandatory-fix,
so compacting must not push a line over 95 chars.

**Core principle:** long functions grow through scaffolding, not real work.
Remove scaffolding first; extract only as a last resort.

**Preservation invariant:** every move preserves behavior. If tests change,
it's a design change.

**Hard no:** never `;`-join statements (`c6`). Split or extract.

---

## Gold-Standard Exemplars

Real protolib functions that already fit. All from
`src/protolib/test/core/test_governance.py`.

### Single-expression ternary return

```python
def _compose(*args, technical, display, **kwargs) -> str:
    """Canonical print form: '(tech) - display'. Omits display if empty."""
    return f"({technical}) - {display}" if display else f"({technical})"
```

One purpose, one return, no locals. Two branches collapse into a ternary.

### Factory with named kwargs as schema

```python
def _rec(*args, line, scope, technical, display="", level, **kwargs) -> dict:
    """Governance record. level is 'warn' or 'error'."""
    return {"line": line, "scope": scope, "level": level,
            "technical_message": technical, "display_message": display}
```

Signature *is* the contract. Missing required kwarg → TypeError at boundary.

### Early-return then ternary

```python
def _dfmt_script_path(meta, rel, line, *args, **kwargs) -> list:
    got = meta.get('script_path')
    if got is None: return []
    want = f"src/{PKG}/{rel.replace(os.sep, '/')}"
    return [] if got == want else [f"line {line}: [module] script_path {got!r} != {want!r}"]
```

5 code lines. One guard, one comparison, one formatted error. No nesting.

---

## Refactor Patterns

### # Trust the Invariant

Delete guards that defend against conditions that cannot occur. Can't name
the code path that produces it → delete.

```python
# before — init creates the file unconditionally; guard is dead
if not os.path.exists(user_settings_path): return {}
with open(user_settings_path) as f: return yaml.safe_load(f) or {}

# after
with open(user_settings_path) as f: return yaml.safe_load(f) or {}
```

### # Fail Loud

Don't wrap logic in `try/except` that silently swallows real corruption.
Reserve it for expected failure modes (network, optional file, race).

```python
# before — hides corrupted user config
try:
    with open(path) as f: return yaml.safe_load(f) or {}
except yaml.YAMLError as e:
    sys.stderr.write(f"...{e}\n"); return {}

# after — corruption visible at the boundary
with open(path) as f: return yaml.safe_load(f) or {}
```

### # Put It in Its Place

Data (paths, prefixes, allowed-key sets) belongs in `settings.py` or as
module/class constants, not inline in consumer methods.

```python
# after — real protolib pattern from test_governance.py
_DOC_ALLOWED = {
    'module': {'script_path', 'purpose', 'description',
               'update_rules', 'governance_exceptions'},
    'class':  {'purpose', 'description', 'governance_exceptions'},
    'def':    {'purpose', 'description', 'governance_exceptions'},
}
```

Mutable accumulators can't become constants — use **Property not Parameter**.

### # Single Source of Truth

After hoisting, grep for the literal. Any other definition is a fossil.

```python
# before — duplicate of core.settings.api_packages
_API_PACKAGES = [f"{sts.package_name}.core.apis", f"{sts.package_name}.app.apis"]

# after
import protolib.core.settings as core_sts
for _, pkg in core_sts.api_packages: ...
```

### # Delete the Pass-Through

A method whose body is a single call to another is cognitive overhead.
Rename the implementation to the public name; delete the wrapper.

```python
# before → after: rename _read_state → read_state, delete get_state
def _read_state(self, *args, **kwargs): ...
def get_state(self, *args, **kwargs): return self._read_state(*args, **kwargs)
```

### # Decouple — Make Two Out of One

Function does two things joined by *and* → split at the seam. See
`_c_dfmt_check` → `_dfmt_validate` → `_dfmt_script_path` in
test_governance.py — each ≤6 lines because work is layered, not concatenated.
Extract reset preludes into `_reset_buffers()` to avoid `;`-joined clears.

### # Delegate — Push Up or Push Down

Push up: step needs caller context → caller does it. Push down: step always
pairs with a specific call → fold into callee.

```python
# before — run() owns parsing, validation, dispatch
def run(self, *args, **kwargs):
    self._check_governance(*args, **kwargs)
    kw = arguments.mk_args().__dict__
    kw = contracts.checks(*args, **kw)
    mod = _import_api(kw.get("api", "help"))
    mod.main(*args, **kw)

# after — dispatch pushed down
def run(self, *args, **kwargs):
    self._check_governance(*args, **kwargs)
    self._dispatch(*args, **contracts.checks(*args, **arguments.mk_args().__dict__))
```

### # Lift the Side Effect

Keep the core focused on transformation; hoist side effects (cache writes,
logging) to the caller.

```python
# after — _send returns; caller caches
def _send(self, req, ...): return state
def emit(self, data, ...):
    state = self._send(req, ...)
    if state: self._cached_state = state
    return state
```

### # Property not Parameter

When a value is conceptually an attribute (time, user, buffer), expose as
`self.x`. Don't thread through N signatures. Same move for accumulators: a
`tree = [...]` threaded through helpers becomes `self._out` — two channels
(param + attr) for one buffer is always wrong. For test determinism, accept
an override on the test-surface method only.

```python
# before — now threads through every call
def register_service(self, sid, data, ...):
    now = datetime.now(timezone.utc).isoformat()
    self._register_svc(state, sid, data, now, ...)

# after
class Registry:
    def __init__(self, *args, **kwargs):
        self.now = datetime.now(timezone.utc).isoformat()
    def _register_svc(self, state, sid, data, ...):
        entry["last_seen"] = self.now
```

### # Skip the Throwaway Local

Assigned once, used next line, never again → inline. Keep the local only
when the name genuinely clarifies intent.

```python
# before → after
host = RegistryHost(*args, **kwargs); host.start_sweep_loop(*args, **kwargs)
RegistryHost(*args, **kwargs).start_sweep_loop(*args, **kwargs)
```

### # Inline the Micro-Function

Module-level one-liner used ≤2 times → inline the stdlib call.

```python
# before → after
def _resolve_host(): return socket.gethostname()
host = socket.gethostname()
```

### # Syntactic Sweetening

Compact Python idioms when the expression fits on one line and stays readable.

- Ternary return: `return x if cond else y` (see `_compose` above)
- Inline assignment: `if state: self._cached_state = state`
- Fallback: `value or default`
- List comprehension instead of loop + append

```python
# before
if "services" not in state: state = self._fetch_state(*args, **kwargs)
return state

# after
return state if "services" in state else self._fetch_state(*args, **kwargs)
```

**Watch:** c6 (no `;`), c11 (≤ 95 chars) — both mandatory-fix. c15
(nesting): if compaction pushes indent over 16 spaces, bind the
comprehension to a local first.

---

## Sequencing

Apply in order; stop once the function fits under 7 code lines. Trust → Fail
Loud → Put in Its Place → Single Source of Truth → Delete Pass-Through →
Decouple → Delegate → Lift Side Effect → Property not Parameter → Skip
Throwaway Local → Inline Micro-Function → Sweeten.
