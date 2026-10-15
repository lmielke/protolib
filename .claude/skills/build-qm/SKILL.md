---
name: build-qm
description: "Independent read-only review of a BUILT stage -- the skeleton or the code of a sprint -- before sign-off: confirms the stage matches its spec, tests pass, governance is clean and the paths the spec names resolve, and flags any blockers. Read-only: it reports problems but does NOT fix them. Use when a skeleton or code review task asks for a build-qm, or implementation is done and needs a clean bill of health: 'verify the build is clean', 'QM check after implementation', 'confirm tests pass before sign-off'. This is the build-side gate; to review the design before build use design-qm. For general factual questions use info."
argument-hint: "[project] [branch-and-sha]"
allowed-tools: Read, Glob, Grep, Bash
---

# Purpose
Read-only review of a committed build stage, run by an agent other than the builder
(AGENTS.md chapter 2: a second model reviews). It writes nothing; blockers surface in the
memo and the hand folds every finding in place with a follow-up commit.

# Workflow
1. Parse `$ARGUMENTS` → `<project> <branch-and-sha>`: the committed stage on the build
   branch. The skeleton and code inform and review task readmes under
   `~/.eddie/templates/blueprints/tasks/` give the scope and the five values the hand
   reports (reviewer, branch, sha, verdict, findings).
2. Read the spec of every unit the sprint touches, and the im. Confirm each step marked
   done matches reality on disk and every Acceptance row has a test.
3. Run the suite in the build worktree (`uv run pytest` or the project runner), and the
   spec checker on each touched spec. On a skeleton stage the planned tests stand as
   expected failures; on the code stage none may.
4. Governance: `uv run gov run` on the touched files. Zero errors; every warning has a
   `docs ma` entry.
5. Path sweep: every path in the Pointers rows of the touched specs exists.
6. Return `MEMO: <2-3 lines — verdict ok or nok, findings count, blockers listed>\nPATH: <stage-ref>`.
