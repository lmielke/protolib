---
script_path: /home/lars/repos/protolib/.claude/rules/test_style.md
paths: ["**/*.py"]
purpose: "Designer-facing Python test playbook — test pyramid, runner choice, file location, multi-scenario parametrize patterns, and governance checks."
description: "Day-to-day reference for writing IT and E2E tests. Strict rules live in py_test_gov.md; this is the readable how-to. Emphasises @pytest.mark.parametrize for multi-scenario IT and the testhelper @test_setup decorator for fixture setup."
update_rules: "Update requires explicit approval."
---

See also: @rules/test_gov.md (strict skeleton reference),
@rules/testing.md (philosophy), @rules/testing_project.md (project layout),
@rules/tdd.md (TDD discipline).

# Python Test Style — Designer Summary

Lightweight guide for writing tests day-to-day. Strict skeleton rules live in
`py_test_gov.md`.

---

## Test Pyramid (what we actually do)

- **IT (default)** — multi-scenario integration tests against real module behavior.
- **E2E** — scripts in `~/scripts/testing/*.sh` for host-level / cross-package.
- **UT** — no new unit tests. Tolerated only for pure helpers where a UT clearly
  isn't tautological (rare). Existing UTs stay; we don't migrate them.

If a test mirrors the code under test, it's a UT-in-disguise — rewrite as IT.

## Runner & Framework

- **Runner:** `uv run pytest` (runs both pytest functions and `unittest.TestCase`).
- **New tests:** prefer pytest idioms — plain `assert`, fixtures, `parametrize`.
- **Existing unittest classes:** keep as-is. Pytest runs them unchanged.
- **Stateful IT with shared setup:** `unittest.TestCase` still fine — class form
  is clearer for multi-method shared state than a pytest fixture chain.

## Location

```
~/repos/<repo>/src/<repo>/test/
├── testhelper.py        — read before writing anything new
├── test_<module>.py     — one test file per production module
└── data/                — fixtures
```

Read `testhelper.py` first. **Use `@test_setup` — do not hand-roll setUp.**
Governance check `testhelper candidates` flags any manual `setUp` that
re-implements temp-dir + chdir + cleanup the decorator already provides.

```python
@helpers.test_setup(temp_file='my_fixture.json', temp_chdir='temp_file')
def test_my_feature(self, *args, **kwargs):
    ...
```

Rule of thumb: if your `setUp` creates a tmpdir, copies a fixture, or `os.chdir`s,
it's a testhelper candidate — replace it.

Host-level scripts: `~/scripts/testing/*.sh`.

## Writing the Test

1. **Inputs**: realistic, semantic names, prefer JSON, check if data already exists.
2. **Expected outputs**: independently derivable — not just "what the code returns".
3. **Scenarios**: normal path + edge cases + failure modes in one file.
4. **Prerequisites**: validate first (`uv` present, service reachable, model file exists).
   Fail loud with a clear message — not a cryptic downstream error.
5. **No mocking** unless the alternative is genuinely impossible.
6. **Docstrings**: `purpose:` on every class and method. `*args, **kwargs` in every
   signature (governance c5).

## Multi-Scenario Pattern — parametrize

The killer feature for IT. One body, many scenarios:

```python
@pytest.mark.parametrize("sid,host,expected", [
    ("auth", "localhost", []),                               # normal
    ("",     "localhost", ["port: sid must not be empty"]),  # edge
    ("db",   "",          ["db: host required"]),            # failure
])
def test_register(sid, host, expected, *args, **kwargs):
    assert Registry().register(sid=sid, host=host) == expected
```

New scenario = one line in the list. That's the point.

## Best-Practice Example

```python
"""
script_path: src/mypackage/test/core/test_registry.py
purpose: "IT for Registry.register() — multi-scenario contract."
"""
import pytest
from mypackage.core.registry import Registry


@pytest.fixture
def registry(*args, **kwargs):
    return Registry()


@pytest.mark.parametrize("sid,expected", [
    ("auth", []),
    ("",     ["port: sid must not be empty"]),
])
def test_register(registry, sid, expected, *args, **kwargs):
    """purpose: 'register() returns expected error list per scenario.'"""
    assert registry.register(sid=sid, host="localhost") == expected
```

## Governance Checks — Test Related

Package-level checks in `test/core/helpers/gov/pkg.py`. Each fires a warning or
error with a fix hint. Strict adherence is the fastest path to a clean suite —
don't treat these as optional; they catch real structural drift and every
resolved warning is one less cause of flaky tests downstream.

| Check | What it catches | Fix |
|---|---|---|
| `mock usage` | `mock` imports that hide real behavior | Remove mocks; use real inputs + `@test_setup` |
| `testhelper candidates` | manual `setUp` doing tmpdir / chdir / cleanup | Replace with `@test_setup` decorator |
| `test file location` | `test_*.py` outside `test/` (won't be collected) | Move under `src/<pkg>/test/` mirroring the module |
| `sync drift` | framework files modified after last sync | `proto-admin sync` from upstream |
| `test core helper location` | non-test files in `test/core/` | Move into `test/core/helpers/` |
| `test imports test file` | `test_*.py` importing another `test_*.py` | Extract shared code to `test/core/helpers/` |

Plus the def-level checks that apply to every function including tests:
`c1` (≤7 lines), `c5` (`*args, **kwargs` in signature), `c11` (≤95 chars).
`c8` (no `__init__` in classes) is waived for `unittest.TestCase` subclasses
via `governance_exceptions`.

## Closing checklist

- Did you write tests alongside the change, not after?
- Did you run the suite before *and* after?
- Do your inputs/outputs encode a real transformation — not a tautology?
- Did you leave any red tests? Fix before moving on.
