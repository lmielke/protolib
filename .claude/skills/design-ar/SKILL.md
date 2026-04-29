---
name: design-ar
description: "Use when a blueprint needs its architecture section -- strategic placement, module manifest, directory shape, UAT/EtE test plan. Triggers: 'design the architecture', 'plan the package structure', 'write the architecture section'. Design-only -- does NOT execute structural moves."
argument-hint: "[project] [scope|bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# Purpose
Architect-level design leaf. Produces §Architecture and §Test Coverage
(UAT/EtE), and attaches `[open]` steps to the paired implementation plan.
Strategic framing first, structure second, host-level test plan last.
Runs inline — aggregates typically run this inside a `leader` (opus)
subagent for the strategic weight.

# Rule set
Write the blueprint end-state and the paired implementation plan:
@rules/bp.md
@rules/bp_plan.md

Place the change strategically in the package:
@rules/architecture.md

Host-level UAT/EtE test planning:
@rules/testing.md
@rules/testing_project.md

Brainstorm gate before any design work:
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
2. Read the paired `_implementation_plan.md`; confirm the blueprint type
   matches the work (master / feature).
3. Populate §Architecture **and §Test Coverage (UAT/EtE)**: module manifest
   (table), directory structure, strategic placement rationale; UAT/EtE
   scripts covering the public contract (host-level, prereq-validated).
   Attach `[open]` steps to the `_implementation_plan.md`.
4. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.
