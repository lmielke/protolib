---
name: build-mo
description: "Implement a SINGLE module body test-first against its already-built dependencies, run governance immediately, and return the module path. This is an internal worker normally dispatched one-per-module BY build-co and is rarely invoked directly. Use only when explicitly building or re-building one specific module whose contract, IT scenarios, and skeleton are all already in place. To implement a whole blueprint's modules use build-co; for the architecture skeleton use build-ar."
argument-hint: "[project] [bp-path] [module-path]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Purpose
Single-module implementation leaf. Fills exactly one module's skeleton body
test-first. The skeleton (signatures + docstrings) is the interface contract;
the blueprint's §Modules row + §Test Coverage (IT) scenarios are the intent and
the test spec. Its intra-package dependencies are already built (build-co
dispatches in dependency waves), so the IT runs against real objects — no mocks.
Runs inside a `worker` subagent; isolated context, returns a single MEMO + PATH.

# Rule set
TDD discipline (test-first, real inputs/outputs):
@rules/tdd.md
@rules/testing_project.md

Module + function shape, kwargs discipline:
@rules/code_style_python.md
@rules/test_style_python.md
@rules/test_gov.md

Package architecture placement:
@rules/architecture_python.md

Governance — run immediately, never defer:
@rules/governance_health.md

Log any automation candidate at close:
@rules/automation.md

# Workflow
1. Parse `$ARGUMENTS` → `<project> <bp-path> <module-path>`.
2. Read this module's §Modules contract + §Test Coverage (IT) scenarios in the
   blueprint; read its on-disk skeleton; read the skeletons of any sibling it
   imports — interfaces only (targeted reads, no full files).
3. Write the IT test first per the scenarios; run it red.
4. Implement the module body into the skeleton — public signatures + docstring
   schema frozen; private helpers may be added (@rules/code_skeleton_python.md).
   No drift. Run the module's IT green against its real (already-built) deps.
5. Run governance validations **immediately** on the module + test you wrote —
   do not defer: `uv run gov run --target <module-path> --target <test-path>`
   per @rules/governance_health.md. Fix root cause on any violation; re-run green.
6. Return `MEMO: <module + key classes, test + gov status>\nPATH: <module-path>`.
   If a sibling's skeleton contract is wrong (signature/schema cannot be honored),
   **do not drift** — return `MEMO: CONTRACT-BREAK <sibling.method> <what's wrong>`
   instead so build-co can amend the skeleton and re-dispatch.
