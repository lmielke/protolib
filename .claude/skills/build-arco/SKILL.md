---
name: build-arco
description: "Execute an approved blueprint's architecture and module phases in a single pass -- chains build-ar (worker) -> build-qm (detective) -> build-co (worker) -> build-qm (detective), stopping early on any blocker. Invoked via its slash command: '/feature build-arco <project> <bp-path>'. Recommend when both the architecture and module steps are approved and the user wants them built end-to-end without separate calls. Use the individual build-ar or build-co skills when only one phase is needed."
disable-model-invocation: true
argument-hint: "[project] [bp-path]"
allowed-tools: Task
---

# Purpose
Aggregate: structural moves → QM gate → TDD implementation → QM gate.
Build leaves run in `worker` subagents (write access); each QM gate runs in
a `detective` subagent (read-only) — builder never reviews its own work.

# Workflow
Parse `$ARGUMENTS` → `<project> <bp-path>`.

Run four Tasks strictly in order; each starts only after the previous
returned. Stop early if any returns blockers.

1. Build architecture (worker):
```
Task(subagent_type="worker",
     description="build-ar",
     prompt="Skill(build-ar, '<project> <bp-path>') — apply structural moves
+ ref sweep. Return MEMO + PATH.")
```
2. QM gate on the arch build (detective):
```
Task(subagent_type="detective",
     description="build-qm arch gate",
     prompt="Read @rules/governance_health.md first — keep its read-order,
action ladder, and severity policy in working memory.
Skill(build-qm, '<project> <bp-path>') — verify the arch build (skeletons,
dirs, UAT/EtE scripts). Read-only. Return MEMO + blockers if any.")
```
3. Build code (worker):
```
Task(subagent_type="worker",
     description="build-co",
     prompt="Skill(build-co, '<project> <bp-path>') — TDD the §Modules steps.
Note: build-co is itself an orchestrator — it fans out a nested `worker`
per module (build-mo) in dependency waves. Nesting is expected here.
Return MEMO + PATH.")
```
4. Final QM gate (detective):
```
Task(subagent_type="detective",
     description="build-qm final gate",
     prompt="Read @rules/governance_health.md first — keep its read-order,
action ladder, and severity policy in working memory.
Skill(build-qm, '<project> <bp-path>') — full code review, full
design-target-was-met review. Read-only. Return merged MEMO + PATH.")
```

Return the final `MEMO:` + `PATH:` verbatim (plus any blocker MEMO that
caused an early stop).
