---
name: build-co
description: "Use when a blueprint's module contracts are approved and need TDD implementation. Triggers: 'implement the modules', 'write the code test-first', 'build the modules from the blueprint'. Writes test + module together, closes each step green."
argument-hint: "[project] [bp-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Purpose
Code implementation leaf. Writes modules per §Modules contract and IT tests
per §Test Coverage (IT), test-first. Test file + module file land together;
each `[open]` plan step closes with green tests before the next starts. Runs inline — aggregates typically run
this inside a `worker` subagent.

# Rule set
Execute steps against the implementation plan:
@rules/bp_plan.md

TDD discipline:
@rules/tdd.md

Module + function skeletons:
@rules/module_gov.md
@rules/def_gov.md

Pytest idioms + testhelper pattern:
@rules/test_style.md
@rules/test_gov.md
@rules/testing_project.md

Package architecture placement (abstract base + Python specialization):
@rules/architecture.md
@rules/architecture_python.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path>`.
2. Read the blueprint + implementation plan. List `[open]` §Modules **and
   §Test Coverage (IT)** steps.
3. For each step: write the test first, run it red, implement the module,
   run green, mark `[done]`.
4. Return `MEMO: <2-3 lines>\nPATH: <bp-path>`.
