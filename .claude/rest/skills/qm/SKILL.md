---
name: qm
description: "Full quality review of a blueprint covering BOTH the design and build sides -- runs design-qm then build-qm in a single read-only detective pass. Invoked via its slash command: '/qm <project> <bp-path>'. Recommend when the user wants a complete quality gate across the whole blueprint at once. For just the design side use design-qm; for just the built side use build-qm. Read-only -- flags blockers, never writes or fixes."
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
