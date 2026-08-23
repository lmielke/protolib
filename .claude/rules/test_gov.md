---
script_path: .claude/rules/test_gov.md
description: >-
  Defines mandatory Python governance check codes and a twelve-pattern function-shrinking
  catalogue. Agents consult it before writing or refactoring code to satisfy c1 and c11 limits.
  The governance test suite enforces these rules at test time, and the file points to governance_python.py
  for concrete refactor examples.
tags:
- governance
- python
- rule
- testing
update_rules: >-
  Append new patterns with name + one-paragraph heuristic. Concrete before/after examples
  live per-step in governance_python.py — do not duplicate them here.
paths:
- '**/*.py'
---

See also: @rules/architecture_python.md (package shape),
@rules/code_style_python.md (designer summary),
@rules/test_style_python.md (test playbook),
@rules/governance_health.md (cleanup contract).

# Python Governance Reference

Strictly enforced at test time by `src/<pkg>/test/core/test_governance.py`.
Target state: zero errors, zero warnings — see @rules/governance_health.md
for severity policy and the action ladder.

## Authoritative Source

Per-step rules and concrete before/after refactor blocks live in
`~/repos/governance/src/governance/app/python/governance_python.py`.
Read a slice without loading the whole file:

```bash
cd ~/repos/governance/src/governance/app/python

# description previews, all steps (≤5 lines each)
awk '/^## c[0-9_]+ /{step=$0} /^[[:space:]]*description: \|-/{print ""; print step; n=0; d=1; next} d && /^[[:space:]]{2}[A-Za-z0-9]/{if(n++<5) print; next} d && n>=5{d=0}' governance_python.py

# single step (replace c1 with target id)
sed -n '/^## c1 /,/^## c[0-9]/p' governance_python.py

# rules bullets, all steps
awk '/^## c[0-9_]+ /{step=$0; r=0} /^[[:space:]]*rules: \|-/{print ""; print step; r=1; next} r==1 && /^[[:space:]]{2}-/{print; next} r==1 {r=0}' governance_python.py

# refactor fences, all steps
awk '/^## c[0-9_]+ /{step=$0; r=0} /^[[:space:]]*refactor: \|-/{print ""; print step; r=1; next} r==1 && /^[^ ]/{r=0} r==1' governance_python.py
```


## Mandatory Checks

Cannot be suppressed. Fix at write-time.

| Code        | Scope    | Rule                                                      |
| ----------- | -------- | --------------------------------------------------------- |
| `c1`        | def      | Method body ≤ 7 code lines                                |
| `c5`        | def      | `*args, **kwargs` in every signature                      |
| `c6`        | def      | No `;`-joined statements                                  |
| `c11`       | line     | Length ≤ 95 chars                                         |
| `c15`       | def      | Indent ≤ 16 spaces (no deep nesting)                      |
| `c18`       | module   | Every `<module>.py` paired with `test_<module>.py`        |
| `c_dfmt`    | docstring| Front-matter present and well-formed                     |
| `c_dscope`  | docstring| `script_path:` + `purpose:` on module/class/def           |
| `c_dorph`   | docstring| No orphan front-matter blocks                             |

Planned test-related checks (named, **not yet wired into the scanner** —
treat as conventions, not enforced gates): `mock usage`, `testhelper
candidates`, `test file location`, `sync drift`, `test core helper
location`, `test imports test file`. Of the test set, only `c18` (pairing,
glob sub) is live today.

`c8` (`__init__` forbidden) is waived for `unittest.TestCase` subclasses
via a `governance_exceptions:` entry in the class docstring.

## Definition Patterns

Apply when a function trips `c1` or `c11`. Concrete before/after blocks
live per-step in `governance_python.py`.

### Gold-Standard Exemplars

Real protolib functions that already fit. All from
`src/protolib/test/core/test_governance.py`.

```python
# single-expression ternary return — one purpose, one return, no locals
def _compose(*args, technical, display, **kwargs) -> str:
    """Canonical print form: '(tech) - display'. Omits display if empty."""
    return f"({technical}) - {display}" if display else f"({technical})"

# factory with named kwargs as schema — signature is the contract
def _rec(*args, line, scope, technical, display="", level, **kwargs) -> dict:
    """Governance record. level is 'warn' or 'error'."""
    return {"line": line, "scope": scope, "level": level,
            "technical_message": technical, "display_message": display}

# early-return then ternary — one guard, one comparison, one error
def _dfmt_script_path(meta, rel, line, *args, **kwargs) -> list:
    got = meta.get('script_path')
    if got is None: return []
    want = f"src/{PKG}/{rel.replace(os.sep, '/')}"
    return [] if got == want else [f"line {line}: [module] script_path {got!r} != {want!r}"]
```

### Refactor Patterns

#### Trust the Invariant
Delete guards that defend against conditions that cannot occur. Can't name
the code path that produces it → delete.

#### Fail Loud
Don't wrap logic in `try/except` that silently swallows real corruption.
Reserve it for expected failure modes (network, optional file, race).

#### Put It in Its Place
Data (paths, prefixes, allowed-key sets) belongs in `settings.py` or as
module/class constants, not inline in consumer methods. Mutable accumulators
can't become constants — use **Property not Parameter**.

#### Single Source of Truth
After hoisting, grep for the literal. Any other definition is a fossil.

#### Delete the Pass-Through
A method whose body is a single call to another is cognitive overhead.
Rename the implementation to the public name; delete the wrapper.

#### Decouple — Make Two Out of One
Function does two things joined by *and* → split at the seam. Each layer
stays under the line budget because work is layered, not concatenated.
Extract reset preludes into `_reset_buffers()` to avoid `;`-joined clears.

#### Delegate — Push Up or Push Down
Push up: step needs caller context → caller does it. Push down: step always
pairs with a specific call → fold into callee.

#### Lift the Side Effect
Keep the core focused on transformation; hoist side effects (cache writes,
logging) to the caller.

#### Property not Parameter
Value is conceptually an attribute (time, user, buffer) → expose as
`self.x`. Don't thread through N signatures. Same move for accumulators: a
`tree = [...]` threaded through helpers becomes `self._out` — two channels
(param + attr) for one buffer is always wrong. For test determinism, accept
an override on the test-surface method only.

#### Skip the Throwaway Local
Assigned once, used next line, never again → inline. Keep the local only
when the name genuinely clarifies intent.

#### Inline the Micro-Function
Module-level one-liner used ≤ 2 times → inline the stdlib call.

#### Syntactic Sweetening
Compact Python idioms when the expression fits on one line and stays
readable: ternary return `return x if cond else y`, inline assignment
`if state: self._cached = state`, fallback `value or default`, list
comprehension instead of loop + append.

**Watch:** `c6` (no `;`), `c11` (≤ 95 chars). If compaction pushes indent
over `c15` (16 spaces), bind the comprehension to a local first.

## Sequencing

Apply in order; stop once the function fits under 7 code lines:
Trust → Fail Loud → Put in Its Place → Single Source of Truth →
Delete Pass-Through → Decouple → Delegate → Lift Side Effect →
Property not Parameter → Skip Throwaway Local → Inline Micro-Function →
Sweeten.
