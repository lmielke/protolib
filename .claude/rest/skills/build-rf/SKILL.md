---
name: build-rf
description: "Execute the remediation steps of an approved REFACTOR blueprint -- works through the [open] mandatory/auto-fixable/suppressible fixes and closes with green tests. Use when a refactor blueprint's implementation plan is ready to run: 'execute the refactor plan', 'run the refactor build', 'apply the remediation steps from the blueprint'. This is the planned, blueprinted path: for a quick ad-hoc cleanup with no blueprint use governance instead; to write the refactor's design sections first use design-rf; the full design-review-build refactor flow is the /refactor orchestrator."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Purpose
Refactor-build leaf. Executes the `[open]` remediation steps of a refactor
blueprint's implementation plan — categorised as §Mandatory Fixes,
§Auto-Fixable, §Suppressible, §Package Checks, §Test Coverage. Runs inline
— aggregates typically run this inside a `worker` subagent. Blueprint-type
contract: must be `refactor`; fails loud otherwise.

# Rule set
Append-only impl plan; `[open]→[done]`:
@rules/bp_implementation_plan.md

Refactor-section contract the remediation satisfies:
@rules/bp_refactor.md

Find-refs-first, minimal change:
@rules/code_refactor.md

Governance skeletons the remediation must satisfy:
@rules/code_style_python.md
@rules/test_style_python.md
@rules/test_gov.md

Test discipline for §Test Coverage remediation:
@rules/tdd.md
@rules/testing.md
@rules/testing_project.md

Preferred tools (auto_correct, fdc, uv run):
@rules/tools.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + paired `_implementation_plan.md`. Confirm
   blueprint type is `refactor` (filename matches `*_refactor_*.md`).
   If not, fail loud — this leaf executes refactor plans only.
3. List `[open]` steps. Execute in category order:
   a. **Auto-Fixable** first —
      `uv run python -m <pkg>.core.auto_correct` or project equivalent.
      Re-run governance to collect residue.
   b. **Mandatory Fixes** (c1/c11/c_dfmt/c_dscope/c_dorph) —
      non-suppressible; resolve each at code level.
   c. **Suppressible** — resolve where cheap; add `governance_exceptions`
      entries where the suppression is still justified.
   d. **Package Checks** — mock usage, testhelper candidates,
      test-file location, sync drift. Fix each per pkg.py hints.
   e. **Test Coverage** (IT + UAT/EtE) — add the missing tests
      identified under §Test Coverage; parametrize when scenarios
      are shaped alike.
4. Mark each step `[done]` in the impl plan as it lands. Never edit
   past entries.
5. Mandatory close — run the test suite green:
   1. `uv run pytest` (or project equivalent).
   2. Fix root cause on any failure; re-run.
   3. Do not return until green.
6. Return `MEMO: <2-3 lines — categories closed, suite status>\nPATH: <bp-path>`.
