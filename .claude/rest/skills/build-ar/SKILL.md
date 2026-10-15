---
name: build-ar
description: "Execute the ARCHITECTURE steps of an approved blueprint -- create the package skeleton, files, imports, OOP scaffolding, and UAT/EtE test stubs, closing with a green suite. Use when the architecture plan is approved and needs to be made real: 'execute the architecture plan', 'build the structure', 'scaffold the skeleton from the blueprint', 'set up the files and imports'. This builds structure only, not module logic -- once skeletons exist, build-co fills their bodies. Writing the plan rather than executing it is design-ar; cloning a brand-new package from scratch is clone."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Purpose
OOP Architecture execution leaf. Performs the structural moves listed as
`[open]` in the implementation plan's OOP §Architecture steps (crate skeleton), and writes the
host-level UAT/EtE scripts listed under §Test Coverage (UAT/EtE). Runs inline —
aggregates typically run this inside a `detective` subagent.

# Expected Results / Deliverables
- populated package directory tree including module dirs, resource dirs (use dfeaults), test dirs
- all relevant module files with per module OOP skeletons (`__init__` + core method +
  `__str__`/`__repr__` per @rules/code_skeleton_python.md)
- governance test modules skeletons for every model to be written 

# Mandatory rule set
Execute steps against the implementation plan:
@rules/bp_implementation_plan.md


Package architecture placement (abstract base + Python specialization):
@rules/architecture.md
@rules/architecture_python.md

TDD + host-level UAT/EtE mandatory scripts:
@rules/testing.md
@rules/testing_project.md
@rules/test_style_python.md
@rules/test_gov.md

# Optional rules
If the build contains a refactor:
@rules/code_refactor.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Know the blueprint + implementation plan. List the `[open]`
   §Architecture **and §Test Coverage (UAT/EtE)** steps.
3. Know the module skeleton "mcp ### Modules - Dot" to be implemented.
4. Execute §Architecture skeleton following @rules/code_skeleton_python.md.
5. Execute governance tests: @rules/test_gov.md
6. Fix and re-iterate.
7. Spawn a design-qm:
```
Task(subagent_type="detective",
     description="design-qm review of $blueprint",
     prompt="Critically review the design-ar skeleton implementation result. Return actionable qm summary and recommendations. Stop early if any leaf returns blockers. Return the final MEMO + PATH.")
```
8. For each module execute revision recomendations (if in doubt, reject/skip execution step)
9. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.
