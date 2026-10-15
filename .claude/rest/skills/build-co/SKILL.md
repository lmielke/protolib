---
name: build-co
description: "Implement the module bodies of a blueprint test-first -- the orchestrator that fans out one build-mo subagent per module in dependency waves, then runs the integrating green suite plus governance. Use when skeletons already exist and the logic needs filling in: 'implement the modules', 'build the code from the blueprint', 'fill in the module bodies', 'write the implementation'. This is the code/logic phase and assumes the architecture skeleton is already built (build-ar). To run architecture plus code together in one pass recommend /feature build-arco."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, Skill
---

# Purpose
Code implementation orchestrator. The skeletons already exist (build-ar wrote
module headers, class defs, signatures + docstrings). build-co enumerates the
§Modules to implement, orders them into dependency waves, and dispatches one
`build-mo` leaf per module — parallel within a wave, wave-by-wave so each
module's real dependencies are built before its IT runs. Closes with the
integrating green suite + governance. Runs inline — aggregates run this inside a
`worker`; it spawns nested `worker` subagents per module (supported Claude Code
v2.1.172+).

# Rule set
Execute steps against the implementation plan:
@rules/bp_implementation_plan.md

Per-module implementation contract (the leaf):
@skills/build-mo

Governance — run immediately at the integrating gate, never defer:
@rules/governance_health.md

Integrating verification:
@rules/testing_project.md

Package architecture placement:
@rules/architecture.md
@rules/architecture_python.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + implementation plan. List `[open]` §Modules steps and
   their paired §Test Coverage (IT) scenarios → the module work-list.
3. Order the work-list into dependency **waves** by reading intra-package
   imports in the on-disk skeletons (targeted `fdc`/`fd5`, no full reads):
   wave 0 = no intra-package deps; each later wave depends only on earlier ones.
   A dependency cycle is a design fault — halt and report, don't force an order.
4. For each wave in order, dispatch one `worker` per module **in parallel**
   (multiple Task calls in one message); wait for the whole wave to return
   before the next, so every dependency is real when the next wave's IT runs:
   ```
   Task(subagent_type="worker",
        description="implement <module>",
        prompt="Skill(build-mo, '<project> <bp-path> <module-path>').
                Return MEMO + PATH.")
   ```
5. Collect each leaf's `MEMO` + `PATH`. Scan MEMOs for `CONTRACT-BREAK`; if any,
   amend the skeleton, then re-dispatch the leaves in the current and later waves
   that imported the amended module before proceeding to step 6.
6. Integrating gate — run the suite green over the whole package and validate
   immediately (do not defer governance):
   1. `uv run pytest` (or project equivalent).
   2. `uv run gov run` (governance) per @rules/governance_health.md.
   3. Fix root cause on any integration-level failure; re-run. Mark each
      §Modules + IT step `[done]` in the implementation plan.
7. Return `MEMO: <2-3 lines, modules built + suite/gov status>\nPATH: <bp-path>`.
