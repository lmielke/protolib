---
name: design-arco
description: "Use when a blueprint needs both architecture and module design in one pass. Triggers: '/feature design-arco <project> <scope>'. Spawns a leader that runs design-ar then design-co inline, sharing strategic memory across both."
disable-model-invocation: true
argument-hint: "[project] [scope|bp-path]"
allowed-tools: Task, Skill
---

# Purpose
Aggregate: architecture + code-shape design in a single strategic context.
One `leader` subagent runs both leaves inline — the architect keeps full
memory of the strategic framing while sketching module contracts.

Brainstorm gate runs here (in main) because subagents are batch-only and
cannot hold an interactive brainstorm loop. Spec: @rules/brainstorm.md.

# Workflow
0. **Blueprint gate (runs in main).** Parse `$ARGUMENTS` → second token is
   `<scope>` or `<bp-path>`. If it resolves to an existing file → bp-path in
   hand, skip to dispatch. If it's free-text scope →
   `Skill(brainstorm, args="<scope>")` in the main conversation and STOP.
   Do not `Task()`. Return the brainstorm output; the user re-invokes this
   aggregate with the bp-path once the brainstorm ripens 4/4 and
   `mk_blueprint.sh` has produced the pair.
1. Dispatch — bp-path is guaranteed at this point:
```
Task(subagent_type="leader",
     description="design-ar then design-co",
     prompt="Run two leaf skills in order, keeping working memory across them:
1. Skill(design-ar, '<project> <bp-path>') — capture returned PATH.
2. Skill(design-co, '<project> <PATH>') — §Modules against that blueprint.
Stop early if either returns blockers. Return the final MEMO + PATH.")
```
2. Return the subagent's `MEMO:` + `PATH:` verbatim.
