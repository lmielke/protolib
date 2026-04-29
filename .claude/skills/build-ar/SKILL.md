---
name: build-ar
description: "Use when a blueprint's architecture steps are approved and need execution -- file creates, moves, ref rewrites, UAT/EtE scripts. Triggers: 'execute the architecture plan', 'move the files per blueprint', 'build the structure'. Closes with green suite."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Purpose
Architecture execution leaf. Performs the structural moves listed as
`[open]` in the implementation plan's §Architecture steps, and writes the
host-level UAT/EtE scripts listed under §Test Coverage (UAT/EtE). Refactor
discipline applies — find references first, then move. Runs inline —
aggregates typically run this inside a `worker` subagent.

# Rule set
Execute steps against the implementation plan:
@rules/bp_plan.md

Refactor discipline — find-refs-first, minimal change:
@rules/code_refactor.md

Package architecture placement (abstract base + Python specialization):
@rules/architecture.md
@rules/architecture_python.md

TDD + host-level UAT/EtE scripts:
@rules/tdd.md
@rules/testing.md
@rules/testing_project.md
@rules/test_style.md
@rules/test_gov.md

Preferred tools — use existing commands over manual work:
@rules/tools.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + implementation plan. List the `[open]`
   §Architecture **and §Test Coverage (UAT/EtE)** steps.
3. Execute §Architecture in order: creates → moves → ref rewrites →
   deletes. After each step run a targeted ref sweep (`fdc`) to confirm
   no breaks.
4. Execute §Test Coverage (UAT/EtE): write host-level scripts under
   `~/scripts/testing/` (or project equivalent); validate prereqs inside
   each script; realistic inputs; independently-derived expected outputs.
5. Mark each step `[done]` in the implementation plan as it completes.
6. Mandatory close — run the suite green:
   1. `uv run pytest` (or project equivalent) + any EtE scripts written.
   2. Fix root cause on any failure; re-run.
   3. Do not return until green.
7. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.
