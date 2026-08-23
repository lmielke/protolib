---
name: refactor
description: "Full refactor lifecycle orchestrator -- runs design-rf, then design-qm, then build-rf, with a mandatory approval gate between design and build. Invoked via its slash command: '/refactor <project> <scope>' or '/refactor bugfix: <desc>'. Recommend when the user wants an entire refactor managed from analysis through implementation. For a quick unplanned cleanup use governance; for a feature (non-refactor) lifecycle use /feature design-build-test; to run just one refactor phase use design-rf or build-rf."
disable-model-invocation: true
argument-hint: "[project] [scope|bp-path]"
allowed-tools: Task, Skill
---

# Purpose
Aggregate: complete refactor lifecycle against a refactor blueprint. Three
subagent phases: `leader` writes the refactor sections (`design-rf`),
`detective` reviews (`design-qm`), then a MANDATORY approval stop, then
`worker` executes the refactor impl plan (`build-rf`). Bugfix is not a
first-class type — the idiom is `/refactor "bugfix: <one-line scope>"`,
which routes through the brainstorm gate like any other free-text scope.

Brainstorm gate runs here (in main) because subagents are batch-only and
cannot hold an interactive brainstorm loop. Spec: @rules/brainstorm.md.

# Workflow
0. **Blueprint gate (runs in main).** Parse `$ARGUMENTS` → second token is
   `<scope>` or `<bp-path>`. If it resolves to an existing file → bp-path in
   hand, skip to Phase 1. If it's free-text scope →
   `Skill(brainstorm, args="<scope>")` in the main conversation and STOP.
   Do not `Task()`. Return the brainstorm output; the user re-invokes this
   aggregate with the bp-path once the brainstorm ripens 4/4 and
   `mk_blueprint.sh "<topic>" <project> refactor` has produced the pair.

Phase 1 — write the refactor design (bp-path guaranteed):
```
Task(subagent_type="leader",
     description="refactor design write",
     prompt="Skill(design-rf, '<project> <bp-path>'). Return MEMO + PATH.")
```

Phase 2 — QM review:
```
Task(subagent_type="detective",
     description="refactor QM review",
     prompt="Skill(design-qm, '<project> <PATH from phase 1>'). Return MEMO + PATH.")
```

If Phase 2 surfaces blockers, return both memos and stop — do not
auto-repair. The user decides whether to re-run `design-rf` or proceed.

**Phase 3 — MANDATORY user approval stop.** Return the Phase 1 + Phase 2
memos and the impl-plan path. Wait for explicit "proceed" from the user
before Phase 4. Do not `Task()` until approval is given.

Phase 4 — execute the refactor impl plan:
```
Task(subagent_type="worker",
     description="refactor build",
     prompt="Skill(build-rf, '<project> <bp-path>'). Return MEMO + PATH.")
```

Return the Phase 4 `MEMO:` + `PATH:` verbatim.
