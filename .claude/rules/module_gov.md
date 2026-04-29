---
script_path: /home/lars/repos/protolib/.claude/rules/module_gov.md
paths: ["**/*.py"]
purpose: "Module skeleton conventions for new Python modules — docstring template, import placement, class/function pattern choice, and skeleton components."
description: "Governance-authoritative reference used by test_governance to validate module shape. Keep the minimal module example as the canonical template; every new module should be compared against it. Companion to py_code_style.md (designer summary) and py_def_gov.md (function shape)."
update_rules: "Update requires explicit approval."
---

See also: @rules/code_style_python.md (designer summary), @rules/def_gov.md (function-shape patterns), @rules/architecture.md (package-level architecture).

# Module Base Setup

Your job as architect: define the skeleton so implementers have a clear contract.
Module structure is subject to strict governance validations — see:
`@/home/lars/repos/protolib/src/protolib/test/core/test_governance.py`

## Skeleton Components

### Module Docstring
Strictly adhere to the docstring template (validated at test time):
`@/home/lars/repos/protolib/src/protolib/core/resources/docstring_templates.yml`

### Imports
Add all known package imports at the top. No local imports inside functions.

### Main Classes
Prefer class-based structure. Choose the appropriate pattern:

| Pattern | When |
|---|---|
| Class | Standard backend code — no or little user interaction |
| Function | Stateless helpers meant to be imported frequently |
| Notebook / spaghetti | Code-as-documentation, working scratch files |

## Minimal Module Example

Patterns from `@rules/def_gov.md`: guard → early return, ternary conditional return,
delegation accumulator. No scaffolding locals; no wrappers.

```python
"""
script_path: src/mypackage/core/registry.py
purpose: "Track and look up registered services by name."
description: "Stateful service map; returns error lists on registration failure."
update_rules: "Update when registry schema changes."
governance_exceptions:
  - c2: "exceptions are subject to review"
"""
# note static globals are held in settings or other resources
from mypackage import settings as sts

# for module wide variables
DEFAULT_STATUS = "active"


class Registry:
    """
    purpose: "Maintains a map of named services and their metadata."
    description: "Errors are lists of strings; empty list means registered successfully."
    governance_exceptions:
      - c8: "exceptions are subject to review"
    """

    # for class wide variables
    label = "registry"

    def __init__(self, *args, **kwargs):
        self.services = {}              # for instance wide variables

    def register(self, *args, sid: str, host: str, **kwargs) -> list:
        """
        purpose: "Register one service entry; return error list on failure."
        description: "Guards empty sid; uses sts.some_param as namespace prefix."
        governance_exceptions:
          - c1: "exceptions are subject to review"
        """
        if not sid:
            # directly use sts.var_name to use static globals
            return [f"{sts.port}: sid must not be empty"]
        key = sid.strip() # for method specific variables — mult use only
        self.services[key] = {"host": host, "port": sts.port, "status": DEFAULT_STATUS}
        return [] if key in self.services else [f"{key}: registration failed"]

    def register_all(self, *args, entries: list, **kwargs) -> list:
        """
        purpose: "Register a batch of services; return combined error list."
        description: "Delegates to register() per entry; preserves insertion order."
        governance_exceptions:
          - c1: "exceptions are subject to review"
        """
        errors = []
        for entry in entries:
            errors += self.register(*args, **entry, **kwargs)
        return errors
```
