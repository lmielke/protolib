---
script_path: /home/lars/repos/protolib/.claude/rules/test_gov.md
paths: ["**/*.py"]
purpose: "Governance-authoritative test-module skeleton — docstring, imports, shape choice (unittest vs pytest), main guard, and check catalog."
description: "Covers both unittest.TestCase and pytest function shapes with worked examples. Lists the package-level checks that fire on test modules with their fix hints. Use alongside py_test_style.md (day-to-day designer summary) and pr_testing.md (project layout)."
update_rules: "Update requires explicit approval."
---

See also: @rules/test_style.md (designer summary), @rules/testing_project.md (project test conventions).

# Test Module — Governance Reference

Every code file must be accompanied by a `test_<module_name>.py`.
Tests are integration tests (IT) or end-to-end (E2E) — no unit tests.

**Runner:** `uv run pytest`. Pytest runs both `unittest.TestCase` subclasses and
plain pytest functions. Both shapes are legal; see "Shape Choice" below.

## Skeleton Components

### Test Module Docstring
Same template as production modules — `script_path:` and `purpose:` are required.
Reference template: `@/home/lars/repos/protolib/src/protolib/core/resources/docstring_templates.yml`

### Imports
- `pytest` for parametrize/fixtures; `unittest` when using class form
- The module under test, imported directly (no mocking unless unavoidable)
- `testhelper` for temp-dir setup — read `testhelper.py` before writing new tests.
  **Using `@test_setup` is not optional** when your fixture needs a tmpdir, chdir,
  or file copy; manual `setUp` for any of these fires the `testhelper candidates`
  check and is treated as a structural violation, not a style preference.

### Shape Choice
| Shape | When |
|---|---|
| `unittest.TestCase` class | Stateful IT with shared setup; porting-friendly for existing suites |
| `pytest` function + parametrize | Multi-scenario IT over one contract; new tests by default |
| `pytest` function + fixtures | E2E with composed setup (temp dir + service + fixture data) |

### Test Classes (unittest shape)
One `unittest.TestCase` subclass per logical concern. Group by behaviour, not method name.
Each class docstring states what contract it is verifying.

### Test Methods / Functions
- Name: `test_<scenario>` — describes the input condition or expected outcome
- Always include `*args, **kwargs` on the signature (governance c5)
- Use `assert` (pytest) or `self.assert*` (unittest) — prefer the most specific form
- Inputs must be realistic; expected outputs must be independently derivable

### Main Guard (unittest shape only)
```python
if __name__ == '__main__':
    unittest.main()
```
Pytest discovery needs no main guard.

## Governance Checks — Test Related

Authoritative source: `@/home/lars/repos/protolib/src/protolib/test/core/helpers/gov/pkg.py`.
Strictly adhere to every check below — each one catches real structural drift
that compounds into flaky suites and hidden coupling when ignored. Resolution
is cheaper when done at write-time than during a refactor.

| Check | Why | Fix |
|---|---|---|
| `mock usage` | Mocking hides real behavior; IT loses signal | Remove mocks; use realistic inputs + `@test_setup` |
| `testhelper candidates` | Manual tmpdir / chdir / cleanup duplicates the decorator | Replace `setUp` with `@test_setup` from `test/core/helpers/setup.py` |
| `test file location` | `test_*.py` outside `test/` is not collected; can shadow real modules | Move under `src/<pkg>/test/` mirroring the module it tests |
| `sync drift` | Framework files modified after `last_synced` drift from upstream | Run `proto-admin sync` or push the change upstream first |
| `test core helper location` | Non-test files in `test/core/` bypass the helpers boundary | Move under `test/core/helpers/` and update imports |
| `test imports test file` | `test_*.py` importing another `test_*.py` creates hidden coupling | Extract shared code to `test/core/helpers/` |

Def-level checks also apply inside tests:
- `c1` — method body ≤ 7 code lines
- `c5` — `*args, **kwargs` in every signature
- `c11` — line length ≤ 95
- `c8` — `TestCase.setUp` replaces `__init__` (declare as a `governance_exception`)

## Minimal Test Module — unittest shape

For stateful IT with shared `setUp`. Paired with the `Registry` example in
`@rules/module_gov.md`. Covers normal path, edge cases, failure modes.

```python
"""
script_path: src/mypackage/test/core/test_registry.py
purpose: "Integration tests for core/registry.py — service registration contract."
description: "Covers register() and register_all() across valid, invalid, and batch inputs."
update_rules: "Append scenarios. Never remove existing tests."
governance_exceptions:
  - c8: "test module — unittest.TestCase replaces __init__"
"""
import unittest
from mypackage.core.registry import Registry

SVC = {"sid": "auth", "host": "localhost", "port": 8080}


class TestRegister(unittest.TestCase):
    """
    purpose: "register() stores the service and returns empty on success."
    description: "Covers valid entry, empty sid, stored metadata, default status."
    governance_exceptions:
      - c2: "reason"
    """

    def setUp(self, *args, **kwargs):
        self.r = Registry()

    def test_valid_entry_returns_empty(self, *args, **kwargs):
        """purpose: 'Valid sid produces no errors.'"""
        self.assertEqual(self.r.register(**SVC), [])

    def test_service_stored_after_register(self, *args, **kwargs):
        """purpose: 'Service is present in the map after registration.'"""
        self.r.register(**SVC)
        self.assertIn("auth", self.r.services)

    def test_empty_sid_returns_error(self, *args, **kwargs):
        """purpose: 'Empty sid triggers the guard and returns one error.'"""
        self.assertEqual(len(self.r.register(sid="", host="localhost")), 1)


if __name__ == '__main__':
    unittest.main()
```

## Minimal Test Module — pytest shape

For multi-scenario IT over the same contract. Same coverage, one test body.

```python
"""
script_path: src/mypackage/test/core/test_registry.py
purpose: "Integration tests for core/registry.py — service registration contract."
description: "Parametrized scenarios for register() — valid, empty, duplicate."
update_rules: "Append scenarios to the parametrize list."
"""
import pytest
from mypackage.core.registry import Registry


@pytest.fixture
def registry(*args, **kwargs):
    return Registry()


@pytest.mark.parametrize("sid,host,expected", [
    ("auth", "localhost", []),
    ("",     "localhost", ["port: sid must not be empty"]),
    ("db",   "localhost", []),
])
def test_register(registry, sid, host, expected, *args, **kwargs):
    """purpose: 'register() returns expected error list per scenario.'"""
    assert registry.register(sid=sid, host=host) == expected


def test_register_all_aggregates_errors(registry, *args, **kwargs):
    """purpose: 'register_all() returns one error per invalid entry.'"""
    entries = [{"sid": "auth", "host": "x"}, {"sid": "", "host": "x"}]
    assert len(registry.register_all(entries=entries)) == 1
```
