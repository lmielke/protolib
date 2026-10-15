---
name: design-qm
description: "Independent read-only review of a DESIGN document before any code is built -- the spec (sp), implementation plan (im) or brainstorm (bs) of a sprint -- flags blockers, gaps and contract violations. Read-only: it does not write or fix sections. Use when a review task or the user asks for a design-qm: 'review this spec', 'QM check the design', 'is this plan ready to build', 'critique the design before we implement'. This reviews the design side only; to verify built code use build-qm. Not for general code questions (use info)."
argument-hint: "[project] [doc-path]"
allowed-tools: Read, Glob, Grep, Bash
---

# Purpose
Read-only review of a design document: the review a none-lane sprint asks for ("one
independent design-qm per document") and the reviewer's craft on a panel lane. It writes
nothing; blockers surface in the memo and the hand folds them in place.

# Workflow
1. Parse `$ARGUMENTS` → `<project> <doc-path>`: the sp, im or bs of the sprint.
2. Read the document in full. Then read the review readme of its type, under
   `~/.eddie/templates/blueprints/tasks/` (`sp_review_readme.md`, `im_review_readme.md`,
   `bs_review_readme.md`): it states what the review covers. An im is read against the sp
   it plans. The grammar of a spec is AGENTS.md chapter 4.
3. For a spec, run the checker: `uv run python ~/scripts/testing/test_spec_tabs.py <spec>
   [--code <dir>]`. OK means both trees build and every class is found in the code.
4. Critique in the readme's order. Every finding names its chapter or line and carries a
   severity (blocker, major, minor). A finding rooted in an earlier document of the axis
   names that document: it goes back there, never patched downstream.
5. Return `MEMO: <2-3 lines — clean or list of blockers>\nPATH: <doc-path>`.
   Empty findings means clean.
