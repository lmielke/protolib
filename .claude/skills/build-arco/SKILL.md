---
name: build-arco
description: "Execute an approved blueprint's architecture and module phases in a single pass -- runs build-ar -> build-qm -> build-co inline, stopping early on any blocker. Invoked via its slash command: '/feature build-arco <project> <bp-path>'. Recommend when both the architecture and module steps are approved and the user wants them built end-to-end without separate calls. Use the individual build-ar or build-co skills when only one phase is needed."
disable-model-invocation: true
argument-hint: "[project] [bp-path]"
allowed-tools: Task
---

# Purpose
Aggregate: structural moves → QM gate → TDD implementation in a single
build context. One `worker` subagent runs the three leaves inline — shared
memory across the ref sweep, the verification pass, and the TDD loop.

# Workflow
Parse `$ARGUMENTS` → `<project> <bp-path>`.

Spawn the worker and chain the three leaves in one context:
```
Task(subagent_type="worker",
     description="build-ar → build-qm → build-co",
     prompt="Before starting, read @rules/governance_health.md — keep its
read-order, action ladder, and severity policy in working memory for the
QM gate.

Then run three leaf skills in order, keeping working memory across them:
1. Skill(build-ar, '<project> <bp-path>') — apply structural moves + ref sweep.
2. Skill(build-qm, '<project> <bp-path>') — verify the arch build (skeletons,
   dirs, UAT/EtE scripts) per @rules/governance_health.md. Read-only.
3. Skill(build-co, '<project> <bp-path>') — TDD the §Modules steps.
   Note: build-co is itself an orchestrator — it fans out a nested `worker`
   per module (build-mo) in dependency waves. Nesting is expected here.
Stop early if any leaf returns blockers. Return the final MEMO + PATH.")
```

Return the subagent's `MEMO:` + `PATH:` verbatim.
