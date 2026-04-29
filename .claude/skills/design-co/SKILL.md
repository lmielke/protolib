---
name: design-co
description: "Use when a blueprint needs module-level design -- class/function contracts, IT scenarios, module manifest. Triggers: 'design the modules', 'write the code contracts', 'plan the IT test scenarios'. Design-only -- does NOT write implementation code."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# Purpose
Module-level design leaf. Writes module + function contracts into the
blueprint and attaches plan steps. Shape of the thing, not the code.
Runs inline — aggregates typically run this inside a `worker` (sonnet)
subagent.

# Rule set
Write module-level design into the blueprint and attach the plan:
@rules/bp.md
@rules/bp_plan.md

Express module and function contracts against governance skeletons:
@rules/module_gov.md
@rules/def_gov.md

Place the module within the package layout (abstract base + Python specialization):
@rules/architecture.md
@rules/architecture_python.md

Test-IT design (scenarios, pytest idioms, testhelper):
@rules/tdd.md
@rules/testing.md
@rules/testing_project.md
@rules/test_style.md
@rules/test_gov.md

Brainstorm gate when invoked cold (no bp-path yet):
@rules/brainstorm.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
0. **Blueprint gate.** Parse `$ARGUMENTS` → second token is `<scope>` or
   `<bp-path>`. If it resolves to an existing file → bp-path in hand, skip to
   step 1. If it's free-text scope → `Skill(brainstorm, args="<scope>")` and
   STOP. Return the brainstorm output verbatim; the user re-invokes this
   skill with the bp-path produced via `mk_blueprint.sh` once the brainstorm
   ripens 4/4. If both missing → fail loud, ask for scope.
1. Parse `$ARGUMENTS` → `<project> <bp-path>` (gate guaranteed bp-path).
2. Read §Architecture from the blueprint — derive the module set from it,
   don't invent.
3. Populate §Modules / §Interfaces **and §Test Coverage (IT)**:
   per-module purpose + inputs + outputs, class/function signatures with
   `*args, **kwargs`; IT scenarios derived from module contracts
   (multi-scenario tables, realistic inputs, independently-derived expected
   outputs, prereq checks). Attach `[open]` steps.
4. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.
