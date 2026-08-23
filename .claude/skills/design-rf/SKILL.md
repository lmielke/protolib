---
name: design-rf
description: "Populate the QM sections of a REFACTOR blueprint -- the Violations Found and Desired End State that drive the remediation plan. Use when a refactor needs its design written up: 'design the refactor sections', 'populate the violations for this blueprint', 'write the refactor design', 'document the desired end state'. Design-only -- it does NOT execute any remediation (that is build-rf). For feature (non-refactor) architecture use design-ar; for a quick unplanned cleanup with no blueprint use governance; the full refactor flow is the /refactor orchestrator."
argument-hint: "[project] [scope|bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# Purpose
Refactor-design leaf. Populates the QM-style sections of a refactor blueprint
(§Architecture, §Data Flow, §Developer Guidelines, §PEP8 Compliance, §Unused
Code, §Test Coverage IT, §Test Coverage UAT/EtE) each as
`Violations found → Desired end state`. Shape of the fix, not the fix itself.
Runs inline — aggregates typically run this inside a `leader` (opus) subagent
for the strategic weight.

# Rules

Blueprint + refactor-section shape:
@rules/bp.md
@rules/bp_refactor.md
@rules/bp_implementation_plan.md

Place the change strategically in the package:
@rules/architecture.md

Brainstorm gate before any design work:
@rules/brainstorm.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
0. **Blueprint gate.** Parse `$ARGUMENTS` → second token is `<scope>` or
   `<bp-path>`. If it resolves to an existing file → bp-path in hand, skip to
   step 1. If it's free-text scope → `Skill(brainstorm, args="<scope>")` and
   STOP. Return the brainstorm output verbatim; the user re-invokes this
   skill with the bp-path produced via `mk_blueprint.sh … refactor` once the
   brainstorm ripens 4/4. If both missing → fail loud, ask for scope.
1. Parse `$ARGUMENTS` → `<project> <bp-path>` (gate guaranteed bp-path).
2. Read the paired `_implementation_plan.md`; confirm blueprint type is
   `refactor`. If not, fail loud — this leaf writes refactor sections only.
3. Targeted audit (no full-file reads): run `fdc` / `fd5` / `docs search` to
   collect concrete violations per section. Cite file:line where possible.
4. Populate each section `### Violations found` + `### Desired end state`.
   Sections with no hits: write "No issues found" under each H3 — keep the H3
   (validator checks H2 only, but the contract is "every section has both H3s
   filled or marked no-issues").
5. Attach `[open]` steps to the paired `_implementation_plan.md`, one per
   remediation the refactor implies. Each step: `- [open] <desc> — ref:
   blueprint §<section>`.
6. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.

# Section contract

| Section              | What goes here                                                |
|----------------------|---------------------------------------------------------------|
| Architecture         | SRP, coupling, package boundaries, ownership                  |
| Data Flow            | kwargs discipline, forwarding, routing, memo shapes           |
| Developer Guidelines | function length, nesting, duplication, control patterns       |
| PEP8 Compliance      | line length, imports, annotations, ordering (N/A if no py)    |
| Unused Code          | dead files, orphan tests, conditional branches, flagged refs  |
| Test Coverage (IT)   | missing module IT, testhelper drift, scenario breadth         |
| Test Coverage (UAT)  | EtE scripts, undefined inputs/outputs, host-level coverage    |
