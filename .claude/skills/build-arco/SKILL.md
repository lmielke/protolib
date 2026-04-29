---
name: build-arco
description: "Use when a blueprint's architecture and module steps are both approved and need execution in one pass. Triggers: '/feature build-arco <project> <bp-path>'. Spawns a worker that runs build-ar then build-co inline."
disable-model-invocation: true
argument-hint: "[project] [bp-path]"
allowed-tools: Task
---

# Purpose
Aggregate: structural moves + TDD implementation in a single build context.
One `worker` subagent runs both leaves inline — shared memory across the
ref sweep and the TDD loop.

# Workflow
Parse `$ARGUMENTS` → `<project> <bp-path>`.

Spawn the worker and chain the two leaves in one context:
```
Task(subagent_type="worker",
     description="build-ar then build-co",
     prompt="Run two leaf skills in order, keeping working memory across them:
1. Skill(build-ar, '<project> <bp-path>') — apply structural moves + ref sweep.
2. Skill(build-co, '<project> <bp-path>') — TDD the §Modules steps.
Stop early if either returns blockers. Return the final MEMO + PATH.")
```

Return the subagent's `MEMO:` + `PATH:` verbatim.
