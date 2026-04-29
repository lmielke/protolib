---
name: design-qm
description: "Use when a design blueprint needs a quality review before build. Triggers: 'review this blueprint', 'QM check the design', 'critique the blueprint before implementation'. Read-only -- flags blockers, does NOT write sections."
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
@rules/module_gov.md
@rules/def_gov.md

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
