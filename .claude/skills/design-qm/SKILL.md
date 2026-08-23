---
name: design-qm
description: "Quality review of a DESIGN blueprint before any code is built -- reads the blueprint and flags blockers, gaps, and contract violations. Read-only: it does not write or fix sections. Use when the user wants a design critiqued prior to implementation: 'review this blueprint', 'QM check the design', 'is this blueprint ready to build', 'critique the design before we implement'. This reviews the design side only; to verify an already-built blueprint before sign-off use build-qm, and for both sides in one pass recommend /qm. Not for general code questions (use info)."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Glob, Grep, Bash
---

# Purpose
Read-only QM review of a design blueprint. Checks §Architecture, §Modules,
§Test Coverage coherence and governance compliance. No writes — blockers
surface in the memo. Runs inline — aggregates typically run this inside a
`detective` subagent.

# Rule set
Blueprint section expectations:
@rules/bp.md
@rules/bp_refactor.md

Architecture placement (abstract base + Python specialization):
@rules/architecture.md
@rules/architecture_python.md

Module + function governance skeletons:
@rules/code_style_python.md
@rules/test_gov.md

Test-plan rules:
@rules/test_gov.md
@rules/testing_project.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the full blueprint. Note which sections are populated vs. empty.
3. Critique in order: strategic placement, module manifest coherence,
   function/class contract shape, test-coverage realism, governance
   exceptions named properly.
4. Return `MEMO: <2-3 lines — clean or list of blockers>\nPATH: <bp-path>`.
   Empty findings means clean.
