---
script_path: .claude/rules/code_skeleton_python.md
description: >-
  Defines the mandatory structure for Python module skeletons produced by the build-ar agent.
  It specifies that designs must be OOP-first, capturing class composition, state, and method
  contracts in docstrings while deferring bodies to build-co. The file enforces concrete schema
  examples for complex objects to ensure cross-module data consistency among parallel agents.
tags:
- blueprint
- parsing
- rule
update_rules: Update requires explicit approval.
paths:
- '**/*.py'
---

Mandatory Read:
@rules/bp.md (blueprint owns the 200+ word module header source),

See also:
@rules/architecture_python.md (package shape),
@rules/test_gov.md (governance + def-patterns).


# Python Module Skeleton

OOP-first (@rules/developer_guidelines.md): the
design is **classes** — composition, state, method contracts — fixing the
module's **shape** without logic. Design lives in the module file, not the
blueprint: class and method docstrings carry the intent; `build-co` fills bodies.

Workflow:
1. Review, update or create global/package fixtures, schemas, settings
1. Create the empty module files at their `src/<pkg>/...` path.
3. Add the module headers — carry full `description:` from the blueprint.
4. Review header against blueprint — the description is the contract; fix gaps now.
5. Add class definitions and skeletons.

This should result in empty class skeletons each containing 4 to 5 method skeletons (__init__, core, __str__, __repr__).

## What a skeleton contains
NOTE: The OOP-shaped module skeleton is validated (see @rules/test_gov)
- Module docstring: take from blueprint, I/O, schemas if exist.
- Imports — relevant __package imports__, alphabetical. `build-co` may add more.
- class definitions: @rule/test_gov complient contract signature
- Module-level constants — design decisions, present now.
- Class definitions with full `description:`, plus class-level constants.
- Full implementation of (__init__ (inst parameters, __str__ (short), __repr__ (instantiation and calling signature))
- Core method (the one method that defines the nature of the class): full signature, `*args/**kwargs`, return annotation, full-intent
  docstring (`schema:` block per complex param/return), body a single `pass`.

## What a skeleton omits

- Method bodies — every core method is `pass` (validated); latter phase `build-co` writes them.
- Secondary / private helpers (`_send`, `_write_state`, …) — they emerge in
  `build-co` when a core method is decomposed to fit `c1`.
- Module-level functions — a function-shaped module is the rare exception, taken
  only with a perfect reason (pure stateless helper). Default to classes; if the
  blueprint justifies a function module, the skeleton is its signatures +
  docstrings, bodies still deferred.

## Schema examples

Every complex object — `dict`, list-of-dict, or nested — carries a concrete
shape at skeleton time. Scalars (`str`, `int`, `bool`, `Path`) and `None` are
self-describing and need none. The shape **is** the contract: parallel `build-mo`
agents read these off each other's skeletons to agree on cross-boundary data, so
an opaque `dict` is a consistency hole.

Placements:
- **Params + returns** → a `schema:` block in the docstring, one line per complex
  param plus `return:`. Map field to type, e.g. `{"status": str, "url": str}`;
  key-type for open maps, e.g. `{sid(str): {...}}`.
- **Assignments** (instance state, constants) → inline `# shape:` comment (no
  docstring there).
- **Embedded cross-module objects** → reference the producer with
  `<Class.method()>` instead of re-spelling its fields; the literal shape lives
  once, in the producer's skeleton (§Internal module use). A method forwarding a
  sibling's result whole never re-spells it.

Keep examples minimal and type-mapped, not real data — one representative entry
per container, nesting only as deep as the contract requires.

## Skeleton

Same `registry.py` as @rules/code_style_python.md, frozen at the skeleton stage.
Descriptions here are abbreviated for the doc — in a real skeleton they are full:
the description **is** the contract `build-co` implements.

```python
"""
script_path: src/mypackage/core/registry.py
description: "Two cooperating classes form a minimal service registry ... (200+ words as written in blueprint)"
"""
# placeholder specific library imports (only specifically decided and locked)
# tbd in buid-co
# package-static globals belong in settings.py, not inline literals
from mypackage import settings as sts
# sibling class from another package module — built by its own agent (see Internal module use)
from mypackage.core.introspect import ApiIntrospector

# module-level constant: shared across this module only, not a settings entry
ACTIVE_STATUS = "active"


class RegistryClient:
    """
    description: "Owns the registry URL and a cache of the last state the host returned ... (50+ words)"
    """

    # class-wide constant: same content type for every instance, immutable label
    content_type = "application/json"

    def __init__(self, *args, sid: str = None, port: int = None, **kwargs):
        # instance state fixed at skeleton time — the class's data shape is the design
        self.sid = sid or sts.package_name
        self.url = f"http://{sts.ip}:{port or sts.registry_port}"
        # shape: {sid(str): {"status": str, "url": str}}
        self._state = {}

    def register_with_capabilities(self, *args, ttl: int = None, **kwargs) -> dict:
        """
        description: "Emit a registration enriched with this service's API signatures ... (10+ words)"
        schema:
            emits:  {"sid": str, "status": str, "url": str, "ttl": int,
                     "apis": <ApiIntrospector.get_api_signatures()>}
            return: {"ok": bool, "services": {sid(str): {...}}}
        """
        # forwards get_api_signatures() whole — shape referenced, not re-spelled (§Internal module use)
        pass

    def __str__(self, action_required: "complete the example")

    def __repr__(self, action_required: "complete the example")
    
    """ build-ar note: build-co will add methods and complete the write """
    ...


class RegistryHost:
    """
    description: "Holds the registry in memory and mirrors it to a JSON file ... (50+ words) following @rules/test_gov"
    """

    # class-wide default: the empty shape every fresh host starts from
    # shape: {"services": {sid(str): {"status": str, "url": str}}}
    base_state = {"services": {}}

    def __init__(self, *args, state_file: str = None, **kwargs):
        # instance state fixed at skeleton time — defines what the host owns
        self.state_file = Path(state_file or sts.registry_state_file)
        self._state = dict(self.base_state)  # shape: see base_state

    def register_service(self, sid: str, data: dict, *args, **kwargs) -> dict:
        """
        description: "Coordinator only: it delegates the per-entry merge and the durability ... (10+ words)"
        schema:
            data:   {"status": str, "url": str, "ttl": int}
            return: {"services": {sid(str): {"status": str, "url": str}}}
        """
        pass

    def __str__(self, action_required: "complete the example")

    def __repr__(self, action_required: "complete the example")
    
    """ build-ar note: build-co will add methods and complete the write """
    ...
```

Lets Go! rules/act.md