---
script_path: /home/lars/repos/protolib/.claude/rules/architecture_python.md
paths: ["**/*.py"]
purpose: "Python specialization of pr_architecture.md — concrete layout, resources, tests, code, and docs for Python packages."
description: "Applied when designing or modifying Python packages under src/. Specialization of the abstract pr_architecture.md contract; sibling to glob_developer_guidelines.md for code-style fundamentals. Cites the py_* governance chain."
update_rules: "Update requires explicit approval."
---

See also: @rules/architecture.md (abstract base), @rules/developer_guidelines.md (cross-cutting code), @rules/module_gov.md (module skeleton), @rules/def_gov.md (function shape), @rules/code_style_python.md (designer summary), @rules/test_style.md (test playbook), @rules/test_gov.md (test skeleton).

# Python Package Architecture

Python specialization of `pr_architecture.md`. Each section opens with the
inheritance line; the body carries the Python delta. For abstract contracts,
read `pr_architecture.md` first.

## Structure
inherits `pr_architecture.md` §Structure; delta: `src/<pkg>/` layout with `app/`, `apis/`, `helpers/`, `core/`, `resources/`, `test/` subdirs; **protolib** is the canonical template.

```
src/<pkg>/
├── app/             # entry points; top-level orchestration
│   ├── __init__.py
│   └── <pkg>.py     # main module (imports helpers + apis)
├── apis/            # outward-facing surface (HTTP, CLI subcommands)
├── helpers/         # stateless utilities, shared across app/apis
├── core/            # framework boundary — settings, contracts, framework code
│   ├── settings.py
│   └── resources/   # static atomic resource files (yml, json, templates)
└── test/            # mirrors module tree (test_<module>.py per module)
    └── core/        # test framework boundary
        └── helpers/ # test utilities (testhelper.py, etc.)
```

New packages: `proto clone -i <name>` (never scaffold manually). Existing
packages must follow the protolib template; deviations require explicit
justification.

## Resources
inherits `pr_architecture.md` §Resources; delta: `settings.py` for static params (extension `.py`), `core/resources/` for static atomic files, `~/.<pkg>/setup.yml` for user-dynamic, `~/.<pkg>/resources/` for user-dynamic files, `/etc/environment` for secrets.

|  Tier             |  Location                          |  Mutability       |  Format       |
| ----------------- | ---------------------------------- | ----------------- | ------------- |
| package-static    | `src/<pkg>/core/settings.py`       | static            | `.py`         |
| package-static    | `src/<pkg>/core/resources/`        | static            | `.yml/.json`  |
| app-static        | `src/<pkg>/app/settings.py`        | static            | `.py`         |
| app-static        | `src/<pkg>/app/resources/`         | static            | `.yml/.json`  |
| user-dynamic      | `~/.<pkg>/setup.yml`               | user-editable     | `.yml`        |
| user-dynamic      | `~/.<pkg>/resources/`              | user-editable     | `.yml/.json`  |
| system-secret     | `/etc/environment`                 | host-managed      | shell env     |

Use `sts.<param>` import style: `from <pkg> import settings as sts`. Never
duplicate constants — single source of truth in `settings.py`.

## Tests
inherits `pr_architecture.md` §Tests; delta: `uv run pytest`; tests in `src/<pkg>/test/test_<module>.py`; `testhelper.@test_setup` decorator for fixtures; governance suite in `test/core/test_governance.py`.

- Per-module IT: every `app/foo.py` has `test/app/test_foo.py` (governance c18).
- Test framework: `pytest` (also runs `unittest.TestCase`).
- No mocks unless unavoidable. Use realistic inputs + `@test_setup`.
- E2E lives at host level (`~/scripts/testing/*.sh`) per `@rules/testing.md`.

Full playbook: `@rules/test_style.md`. Skeleton: `@rules/test_gov.md`.

## Code
inherits `pr_architecture.md` §Code AND `glob_developer_guidelines.md` (sibling foundation); delta: kwargs forwarding (`*args, **kwargs` everywhere); `c1` (≤7 lines/method); `c11` (≤95 chars/line); strict module/class/function shape.

- Function shape: `@rules/def_gov.md` (12 named refactor patterns).
- Module skeleton: `@rules/module_gov.md` (docstring, imports, classes).
- Designer summary: `@rules/code_style_python.md`.
- Package manager: `uv` only — `uv sync`, `uv run`, `uv add`. Never `pip` directly.
- Imports: top of file; alphabetical; no in-function imports.

Mandatory rules (cannot be suppressed): `c1`, `c11`, `c_dfmt`, `c_dscope`, `c_dorph`.

## Docs
inherits `pr_architecture.md` §Docs; delta: docstring front-matter on every module / class / def with `script_path:`, `purpose:`, optional `description:`, `update_rules:`, `governance_exceptions:`.

- Docstring template: `~/repos/protolib/src/protolib/core/resources/docstring_templates.yml`
- README owns user-facing surface; blueprint owns internal end state.
- Workdocs writeback per `@rules/docs_workflow.md` (`docs ma/pr/ch/ka`).
