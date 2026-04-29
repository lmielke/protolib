---
name: qm
description: "Use when a blueprint needs a full quality review covering both design and build sides. Triggers: '/qm <project> <bp-path>'. Runs design-qm then build-qm in a single detective context. Read-only -- no writes."
disable-model-invocation: true
argument-hint: "[project] [bp-path]"
allowed-tools: Task
---

# Purpose
Aggregate: complete QM review of a blueprint, design + build sides, in one
`detective` subagent context — the reviewer keeps working memory of the
blueprint across both halves.

# Workflow
Parse `$ARGUMENTS` → `<project> <bp-path>`.

```
Task(subagent_type="detective",
     description="full QM review",
     prompt="Run two leaf skills in order, keeping working memory across them:
1. Skill(design-qm, '<project> <bp-path>') — section coherence, governance.
2. Skill(build-qm, '<project> <bp-path>') — structure on disk, suite green, refs resolve.
Return a merged MEMO (clean or list of blockers) + PATH.")
```

Return the subagent's `MEMO:` + `PATH:` verbatim.
