---
script_path: .claude/rules/architecture_python.md
description: >-
  Defines the Python package architecture for protolib and its clones, enforcing an OOP-first
  design with a strict app versus core boundary. It specifies the src layout, resource tier
  locations, and test wiring conventions. Agents read it before scaffolding or modifying Python
  packages; it defers to sibling rules for code style and governance details.
tags:
- blueprint
- infra
- rule
update_rules: Update requires explicit approval.
paths:
- '**/*.py'
---

See also: @rules/architecture.md (abstract base),
@rules/developer_guidelines.md (cross-cutting code),
@rules/resources.md (resource tier semantics),
@rules/code_style_python.md (style rules + gold-standard class),
@rules/test_style_python.md (test playbook),
@rules/test_gov.md (governance + def-patterns).

# Python Package Architecture

OOP-first. Every package starts with classes; functions are reserved for
stateless helpers. Specialization of `@rules/architecture.md` — read that
first for the abstract contract.

## Structure

`src/<pkg>/` layout. **protolib** is the canonical template; all clones
(`bridge`, `speaker`, `whisker`, …) inherit it via `proto clone -i <name>`.

```
src/<pkg>/
├── app/             # entry points; user-owned in clones
│   ├── __init__.py
│   └── <pkg>.py     # main module — orchestrates helpers + apis
├── apis/            # outward-facing surface (HTTP, CLI subcommands)
├── helpers/         # stateless utilities — sync-owned by protolib
├── core/            # framework boundary — sync-owned by protolib
│   ├── settings.py
│   └── resources/   # static atomic files (yml, json, templates)
└── test/            # mirrors module tree (test_<module>.py per module)
    └── core/
        └── helpers/ # testhelper.py, gov/, setup decorators
```

**app vs core:** `app/` is package-specific business logic — clones own and
modify it freely. `core/` and `helpers/` are framework code — kept in sync
with protolib via `proto-admin sync`. Never scaffold a package by hand.

Respect __Seperation of Concern__ and __Subsidiarity__! 
Clear seperation between frontend (presentation) from backend (logic and processing). Seperation of Code and Fixtures (Ressources). Subsidiarity of objects (local vs. global).

## Resources

Per @rules/resources.md, with the Python tier table:

| Tier            | Location                                    | Format       |
| --------------- | ------------------------------------------- | ------------ |
| package-static  | `src/<pkg>/core/settings.py`                | `.py`        |
| package-static  | `src/<pkg>/core/resources/`                 | `.yml/.json` |
| user-dynamic    | `~/.<pkg>/settings.yml` | `.yml/.json` |
| user-dynamic    | `~/repos/<pkg>/src/<pkg>/app/resources`  | `.yml/.json` |
| system-secret   | `/etc/environment`                          | shell env    |

Use `from <pkg> import settings as sts` — never duplicate constants.

## Tests

`uv run pytest`. Per-module IT in `src/<pkg>/test/test_<module>.py`
(governance `c18` enforces 1:1 pairing). Host-level E2E in
`~/scripts/testing/*.sh` per @rules/testing.md.

Playbook: @rules/test_style_python.md. Governance: @rules/test_gov.md.

## Code

OOP-first; kwargs-everywhere (`*args, **kwargs` on every signature);
strict module/class/function shape governed by @rules/test_gov.md.

- Package manager: `uv` only (`uv sync`, `uv run`, `uv add`). No `pip`.
- Imports at top; alphabetical; no in-function imports.
- Style + gold-standard class: @rules/code_style_python.md.

## Docs

Docstring front-matter on every module / class / def per
`~/.governance/docstring_templates.yml` (validated by `c_dfmt`,
`c_dscope`, `c_dorph`).

- README owns user-facing surface; blueprint owns internal end state.
- Workdocs writeback (`docs ma/pr/ch/ka`) per @rules/docs_workflow.md.
