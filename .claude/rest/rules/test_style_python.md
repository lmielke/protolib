---
script_path: .claude/rules/test_style_python.md
description: >-
  Defines the layout, runner, and fixture conventions for Python integration tests in the
  protolib package. Agents read it before writing tests to ensure one test file per module
  and use of the @test_setup helper. The c18 check enforces the file pairing it describes.
tags:
- python
- rule
- testing
update_rules: Update requires explicit approval.
paths:
- '**/*.py'
---

See also:
Lazy read (only if relevant).
@rules/testing.md (philosophy + host-level),
@rules/tdd.md (TDD discipline),
@rules/testing_project.md (project layout, `@test_setup`),
@rules/test_gov.md,

Mandatory read:
@rules/code_style_python.md (style rules tests must also obey).

# Python Test Style

## Layout

One `test_<module>.py` per production module, mirroring the source tree:

```
src/<pkg>/
├── core/registry.py            → src/<pkg>/test/core/test_registry.py
├── helpers/utils.py            → src/<pkg>/test/helpers/test_utils.py
└── app/<pkg>.py                → src/<pkg>/test/app/test_<pkg>.py
```

Pairing is enforced by `c18`. Tests outside `src/<pkg>/test/` aren't
collected — `test file location` check fires.

Tests are integration tests (IT) by default. End-to-end shell scripts live
at host level: `~/scripts/testing/*.sh` per @rules/testing.md.

## Runner

`uv run pytest`. Pytest also runs `unittest.TestCase` subclasses unchanged —
prefer pytest functions for new tests; keep existing TestCase suites as-is.

## Fixture Pattern

Use `@test_setup` — never hand-roll `setUp` for tmpdir / chdir / file copy.
Read `src/<pkg>/test/testhelper.py` first. (Convention only — a `testhelper
candidates` check to enforce it is planned, not yet wired into the scanner.)

Pattern + example: @rules/testing_project.md §Package test module layout.

## IT Example

Multi-scenario IT for the `RegistryHost` / `RegistryClient` classes from
@rules/code_style_python.md. Each scenario is one line in a parametrize
list; a new case = one new line.

```python
"""
script_path: src/mypackage/test/core/test_registry.py
description: "Parametrized scenarios for RegistryHost.register_service() and RegistryClient.discover_url()."
"""
import pytest
from mypackage.core.registry import RegistryClient, RegistryHost


@pytest.fixture
def host(tmp_path, *args, **kwargs):
    return RegistryHost(state_file=tmp_path / "state.json")


@pytest.mark.parametrize("inp", [
    {"sid": "auth", "data": {"host": "alpha", "port": 8001}},  # normal
    {"sid": "db",   "data": {"host": "beta",  "port": 8002}},  # second service
])
def test_register_service_persists(host, inp, *args, **kwargs):
    state = host.register_service(**inp)
    assert state["services"][inp["sid"]]["status"] == "active"
    assert "last_update" in state


def test_register_service_merges_partial(host, *args, **kwargs):
    host.register_service("auth", {"host": "alpha", "port": 8001})
    state = host.register_service("auth", {"port": 8009})
    assert state["services"]["auth"] == {
        "host": "alpha", "port": 8009, "status": "active"}


@pytest.mark.parametrize("services,sid,expected", [
    ({"auth": {"url": "http://alpha:8001"}}, "auth", "http://alpha:8001"),  # resolvable
    ({"auth": {"status": "active"}},         "auth", None),                 # url-less
    ({},                                     "auth", None),                 # unknown
])
def test_discover_url(services, sid, expected, *args, **kwargs):
    # seed the cache directly — discover_url reads it without any network call
    client = RegistryClient()
    client._state = {"services": services}
    assert client.discover_url(sid) == expected
```

Inputs are JSON-shaped dicts so they map cleanly to `**kwargs`. Expected
outputs are independently derivable from the contract — not "what the code
returns".

## Closing Checklist

- Tests written alongside the change, not after.
- Suite run before *and* after the change.
- Inputs/outputs encode a real transformation, not a tautology.
- No mocking unless genuinely impossible.
- No red tests left behind.

Enforced check codes (`c1`, `c5`, `c11`, `c15`, `c18`): @rules/test_gov.md
§Mandatory Checks. Named test checks (`mock usage`, `testhelper candidates`,
…) are planned, not yet wired into the scanner.
