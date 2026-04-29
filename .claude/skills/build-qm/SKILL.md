---
name: build-qm
description: "Use when a built blueprint needs final verification before sign-off. Triggers: 'verify the build is clean', 'QM check after implementation', 'confirm tests pass and refs resolve'. Read-only -- flags blockers, does NOT fix them."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Glob, Grep, Bash
---

# Purpose
Read-only QM review of a built blueprint. Verifies structural moves landed,
tests pass, governance is clean, every `@rules/` and `@skills/` ref
resolves. No writes — blockers surface in the memo. Runs inline —
aggregates typically run this inside a `detective` subagent.

# Rule set
Implementation plan expectations:
@rules/bp_plan.md

Refactor discipline for ref sweeps:
@rules/code_refactor.md

Governance skeletons to check against:
@rules/module_gov.md
@rules/def_gov.md
@rules/test_gov.md

Preferred tools for sweeps and suite runs:
@rules/tools.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + implementation plan. Confirm every `[done]`
   matches reality on disk.
3. Run the test suite via `uv run pytest` (or the project's runner).
4. Ref sweep: `fdc "@rules/"` and `fdc "@skills/"` — every hit must
   resolve.
5. Return `MEMO: <2-3 lines — clean or list of blockers>\nPATH: <bp-path>`.
