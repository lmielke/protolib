---
name: build-qm
description: "Final verification of a BUILT blueprint before sign-off -- confirms tests pass and references resolve, and flags any blockers. Read-only: it reports problems but does NOT fix them. Use when implementation is done and needs a clean bill of health: 'verify the build is clean', 'QM check after implementation', 'confirm tests pass and refs resolve before sign-off'. This is the build-side gate; to review the design before build use design-qm, and for both gates in one pass recommend /qm. For general factual questions use info."
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
@rules/bp_implementation_plan.md

Refactor discipline for ref sweeps:
@rules/code_refactor.md

Governance skeletons to check against:
@rules/code_style_python.md
@rules/test_style_python.md
@rules/test_gov.md

Preferred tools for sweeps and suite runs:
@rules/tools.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + implementation plan. Confirm every `[done]`
   matches reality on disk.
3. Run the test suite via `uv run pytest` (or the project's runner). Note, if qm is done on design-ar, then some errors are expected.
4. verify governance adherence @rules/governance_health.md
5. Plan the execution @rules/act.md based on actual and expected/desired state
6. Ref sweep: `fdc "@rules/"` and `fdc "@skills/"` — every hit must
   resolve.
7. Return `MEMO: <2-3 lines — clean or list of blockers>\nPATH: <bp-path>`.
