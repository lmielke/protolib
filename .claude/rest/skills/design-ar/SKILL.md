---
name: design-ar
description: "Write the architecture section of a feature blueprint -- strategic placement, module manifest, resource manifest, directory shape, and the UAT/EtE test plan. Use when an approved scope or brainstorm needs turning into a concrete architecture plan: 'design the architecture', 'plan the package structure', 'write the architecture section of the blueprint', 'lay out the modules and resources'. Design-only -- it writes the plan but does NOT create files or execute structural moves (that is build-ar). For shell/bash projects use shell_architecture; to review a finished design use design-qm; for refactor blueprints use design-rf."
argument-hint: "[project] [scope|bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# Purpose
Architect-level design leaf. Produces §Architecture and §Test Coverage
(UAT/EtE), and attaches `[open]` steps to the paired implementation plan.
Strategic framing first, structure second, host-level test plan last.
Runs inline — aggregates typically run this inside a `leader` (opus)
subagent for the strategic weight.

# Deliverables
- blueprint and implementation plan

# Rule set
Write the blueprint end-state and the paired implementation plan:
@rules/bp.md (mandatory read)
@rules/bp_implementation_plan.md (mandatory read)

Place the change strategically in the package:
@rules/architecture.md (mandatory read)

Host-level UAT/EtE test planning:
@rules/testing.md

# Workflow
1. **Blueprint gate.** Parse `$ARGUMENTS` → second token is `<scope>` or
   `<bp-path>`. If it resolves to an existing file → bp-path in hand, skip to
   step 2. Flipped packages (@rules/bp_routing.md): the bp lives at
   `<pkg>/blueprint/<CR>_bp_*.md`, created via `bpm new bp` (bs release gates it);
   reviews land via `bpm approve <cr> bp`.
   NOTE: If it's free-text scope → revert to @skills/design-build-test (full design build test skill)
2. **Basis gate.** Orient on the `blueprint.md` scaffold (purpose, preamble, type)
   + `_implementation_plan.md`, then check for the **brainstorm document and/or
   prototype** that form the design basis (Phase-0 outputs of brainstorm/prototype, produced under @skills/design-build-test).
   - Present → use them to **write/update** the `blueprint.md` (§Architecture /
     §Test Coverage) and the `_implementation_plan.md`. design-ar authors these, not just reads.
   - Absent, or type mismatches the work (master / feature) → revert to @skills/design-build-test
     (full design build test skill) to produce the basis first.
3. Plan the execution @rules/act.md (create a detailed workplan)
4. Populate §Architecture **and §Test Coverage (UAT/EtE)**: module manifest
   (table), directory structure, resource manifest, strategic placement rationale; UAT/EtE
   scripts covering the public contract (host-level, prereq-validated).
   Attach `[open]` steps to the `_implementation_plan.md`.
5. Review the blueprint (Code Module Headers), Is this what we want to build?
6. Create or revise the Readme.md with a agent/user facing dcumentation
7. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.

Note: Designing the architecure includes setting up the file headers for all involved modules. This will help to review validate and and revise the solution before verbose coding begins.
Docstring template: `~/.governance/docstring_templates.yml`