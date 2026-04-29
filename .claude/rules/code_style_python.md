---
script_path: /home/lars/repos/protolib/.claude/rules/code_style_python.md
paths: ["**/*.py"]
purpose: "Designer-facing Python style summary — structure-first rules, function shape, args/kwargs convention, module shape, idioms, and imports."
description: "Day-to-day Python style reference on t1000. Governance-authoritative rules live in the _gov files; this is the lightweight, readable version used while writing new code. Read first when designing or writing any Python; defer to py_def_gov.md and py_module_gov.md for edge cases."
update_rules: "Update requires explicit approval."
---

See also: @rules/developer_guidelines.md (general dev guidelines),
@rules/def_gov.md (strict function-shape reference),
@rules/module_gov.md (strict module-skeleton reference).

# Python Coding Style — Designer Summary

Lightweight guide for writing new Python code on t1000. Governance-authoritative
rules live in the `_gov` files — this file is the day-to-day reference.

---

## Structure First

- Classes before functions. Start modules with classes.
- Functions for stateless helpers only.
- One process/purpose per module.

## Function Shape

- 3–6 lines per body. >6 → refactor. 1-line → inline.
- Always `def func(*args, ..., **kwargs):` — forwarding is the default.
- Simple type annotations: `str`, `int`, `list[str]`. Avoid the `typing` module.
- No `;`-joined statements. Line length ≤ 95.

**Core principle:** long functions grow through scaffolding, not real work.
Remove scaffolding first; extract only as a last resort. Full pattern catalogue
in @rules/def_gov.md — quick triage:

1. **Trust the invariant** — delete guards for impossible conditions.
2. **Fail loud** — no `try/except` that swallows real corruption.
3. **Put it in its place** — hoist constants to `settings.py` or module level.
4. **Skip the throwaway local** — inline assign-and-use.
5. **Sweeten** — ternary return, `x or default`, list comprehension.

## args / kwargs Convention

```python
# forwarding — default
def my_func(*args, **kwargs):
    sub_func(*args, **kwargs)

# consuming — explicit param becomes the contract
def sub_func(*args, my_param: str, **kwargs):
    print(my_param)
```

- **No `kwargs.get(...)`** — ever. `kwargs` is transport; named params are contract.
- Local as positional: `path = build_path(*args, **kwargs); process(path, *args, **kwargs)`.
- Missing required kwarg → TypeError at boundary. That's the feature.

## Module Shape

- Docstring with `script_path:` and `purpose:` (required).
- Imports at top. No local imports inside functions.
- Package-static data in `settings.py`; module-static as a `MODULE_CONST`;
  user-dynamic in `~/.<pkg>/`.
- Full skeleton + docstring template in @rules/module_gov.md.

## Idioms

- Prefer `a, b = b, a`, list comprehensions, f-strings.
- Built-ins over custom: `any()`, `all()`, `getattr()`, `setattr()`.
- Avoid `eval()`, `exec()`, single-use temp variables.
- Conditional assignment:
  ```python
  return state if "ok" in state else self._fetch_state(*args, **kwargs)
  ```

## Imports

```python
import os, sys, json
from module import x
from module import y
```

---

## Best-Practice Example

One class, two methods, each ≤6 lines. Docstring front-matter, `*args/**kwargs`
forwarding, settings-module for constants, no scaffolding.

```python
"""
script_path: src/mypackage/core/registry.py
purpose: "Track and look up registered services by name."
"""
from mypackage import settings as sts

DEFAULT_STATUS = "active"


class Registry:
    """purpose: 'Maintains a map of named services and their metadata.'"""

    def __init__(self, *args, **kwargs):
        self.services = {}

    def register(self, *args, sid: str, host: str, **kwargs) -> list:
        """purpose: 'Register one service; return error list on failure.'"""
        if not sid:
            return [f"{sts.port}: sid must not be empty"]
        self.services[sid] = {"host": host, "port": sts.port, "status": DEFAULT_STATUS}
        return [] if sid in self.services else [f"{sid}: registration failed"]

    def register_all(self, *args, entries: list, **kwargs) -> list:
        """purpose: 'Register a batch; return combined error list.'"""
        errors = []
        for entry in entries:
            errors += self.register(*args, **entry, **kwargs)
        return errors
```
