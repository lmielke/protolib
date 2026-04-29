"""
script_path: src/protolib/test/core/gov/governance.py
paths: ["**/*.py"]
purpose: "Governance validations master — runnable engine + literate definitions."
description: |-
  Single source of truth for every check. Loading this module RUNS each
  check (via `run_check`) and populates `RESULTS`. Each `## cN` block
  combines the rule's definition (docstring) with its execution (params
  build + run_check call). Helpers under `helpers/cN.py` stay dumb —
  they receive thresholds via **params and compose their own messages.
update_rules: "Append `## cN` blocks at the bottom; never reorder existing ones."
governance_exceptions:
  - c2:  "literate per-rule blocks use bare string literals between imports — by design"
  - c25: "imports interleaved with literate sections — by design"
  - c34: "master file is intentionally long; one block per rule"
"""
import protolib.core.settings as core_sts
from protolib.test.core.gov.base import run_check

# Registry of all checks. Populated by the literate sections below on import.
# Shape: {code: {"fn": callable, "kind": str, "exceptions_apply": bool,
#                "why": str, "fix": str, "auto_correct": callable | None}}
RESULTS: dict = {}


# Validations
# ============================================================================


## c1
"""
name: "c1 - def length"
rule: "@rules/def_gov.md"
purpose: "c1 — function length. Mandatory-fix."
description: |-
  Body code lines per def (excludes docstring/blank/comment). Warn band
  between warn and max; error above max. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c1

# C1 thresholds for def lengths.
# Note: @rules/def_gov.md sets the design target at ≤7 lines (aspirational).
# The live thresholds below are deliberately looser — enforcement floor, not
# the target. Tighten only when the codebase consistently meets the rule.
c1_params = {
              'warn': 9,
              'max': 15,
}

RESULTS.update(run_check(c1, **c1_params))


## c11
"""
name: "c11 - line length"
rule: "@rules/code_style_python.md"
purpose: "c11 — line length. Mandatory-fix."
description: |-
  Per-line character count. Warn band between warn and max; error above
  max. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c11

c11_params = {
    'warn': 120,
    'max': 150,
}
RESULTS.update(run_check(c11, **c11_params))


## c90_1
"""
name: "c90_1 - dfmt"
rule: "@rules/module_gov.md"
purpose: "c90_1 — docstring front-matter format. Mandatory-fix (meta-rule)."
description: |-
  Validates docstring front-matter at module / class / def scope. Required
  and allowed key sets are scope-indexed inline as `required` / `allowed`
  dicts. Rejects unknown keys; flags missing required keys. Cannot be
  suppressed.
"""
from protolib.test.core.gov.helpers import c90_1

c90_1_params = {
    'required': {
        'module': ['script_path', 'purpose'],
        'class':  ['purpose'],
        'def':    ['purpose'],
    },
    'allowed': {
        'module': ['script_path', 'purpose', 'description',
                   'update_rules', 'governance_exceptions'],
        'class':  ['purpose', 'description', 'governance_exceptions'],
        'def':    ['purpose', 'description', 'governance_exceptions'],
    },
    'pkg': core_sts.package_name,   # PKG for script_path validation
}
RESULTS.update(run_check(c90_1, **c90_1_params))


## c90_2
"""
name: "c90_2 - dscope"
rule: "@rules/module_gov.md"
purpose: "c90_2 — exception scope. Each governance_exceptions entry must apply at its scope."
description: |-
  Validates that every code listed under a docstring's `governance_exceptions`
  applies at the scope where it was declared (module/class/def). A `c1`
  exception at module scope is a scope error; def-only rules cannot be
  silenced from above. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c90_2

c90_2_params = {
    'scope_allowed': {
        'module': ['c2', 'c3', 'c8', 'c12', 'c17', 'c34', 'c41'],
        'class':  ['c2', 'c8'],
        'def':    ['c1', 'c2', 'c5', 'c11', 'c14', 'c15', 'c21', 'c25'],
    },
}
RESULTS.update(run_check(c90_2, **c90_2_params))


## c3
"""
name: "c3 - module length"
rule: "@rules/code_style_python.md"
purpose: "c3 — module length warn at >warn, error at >max."
description: |-
  Total source-line count per module. Tiny stubs below min_lines are
  skipped. Suppressible at module scope via governance_exceptions: c3.
"""
from protolib.test.core.gov.helpers import c3

c3_params = {
    'warn': 300,
    'max': 500,
    'min_lines': 10,                # below this, skip the check (stub modules ok)
}
RESULTS.update(run_check(c3, **c3_params))


## c5
"""
name: "c5 - kwargs signature"
rule: "@rules/code_style_python.md"
purpose: "c5 — every def takes *args/**kwargs on the signature line."
description: |-
  Two cases warn: (1) **kwargs without *args (partial signature), and
  (2) neither *args nor **kwargs when the body has more than
  min_body_lines real lines. Suppressible at def scope via
  governance_exceptions: c5.
"""
from protolib.test.core.gov.helpers import c5

c5_params = {
    'min_body_lines': 2,
}
RESULTS.update(run_check(c5, **c5_params))


## c12
"""
name: "c12 - class count"
rule: "@rules/architecture_python.md"
purpose: "c12 — too many classes per module hints at multiple responsibilities."
description: |-
  Counts top-level ClassDef nodes; warns when count exceeds
  max_classes. Suppressible at module scope via
  governance_exceptions: c12.
"""
from protolib.test.core.gov.helpers import c12

c12_params = {
    'max_classes': 5,
}
RESULTS.update(run_check(c12, **c12_params))


## c14
"""
name: "c14 - elif chain length"
rule: "@rules/code_style_python.md"
purpose: "c14 — long elif chains resist exhaustive testing; prefer dispatch."
description: |-
  Per-def longest elif-chain length. Warns when the chain exceeds
  max_elif. Not suppressible (def-shape).
"""
from protolib.test.core.gov.helpers import c14

c14_params = {
    'max_elif': 3,
}
RESULTS.update(run_check(c14, **c14_params))


## c15
"""
name: "c15 - deep nesting"
rule: "@rules/code_style_python.md"
purpose: "c15 — real indent depth above warn_col / max_col."
description: |-
  Tokenize-based; ignores bracket-continuation lines. Warns at
  warn_col (>4 levels) and errors at max_col (>5 levels).
"""
from protolib.test.core.gov.helpers import c15

c15_params = {
    'warn_col': 16,
    'max_col': 20,
}
RESULTS.update(run_check(c15, **c15_params))


## c17
"""
name: "c17 - module docstring length"
rule: "@rules/module_gov.md"
purpose: "c17 — module docstring description must meet min length."
description: |-
  Description is the docstring text after stripping the script_path:
  line. Passes if EITHER min_words OR min_sentences is met.
  Suppressible at module scope via governance_exceptions: c17.
"""
from protolib.test.core.gov.helpers import c17

c17_params = {
    'min_words': 25,
    'min_sentences': 3,
}
RESULTS.update(run_check(c17, **c17_params))


## c21
"""
name: "c21 - repeated locals"
rule: "@rules/def_gov.md"
purpose: "c21 — names assigned in many defs likely belong on a class."
description: |-
  Per-module scan; flags non-common, non-dunder local names assigned
  in min_fns or more distinct defs. Suppressible at def scope via
  governance_exceptions: c21.
"""
from protolib.test.core.gov.helpers import c21

c21_params = {
    'min_fns': 3,
}
RESULTS.update(run_check(c21, **c21_params))


## c24
"""
name: "c24 - def spacing"
rule: "@rules/code_style_python.md"
purpose: "c24 — top-level defs need 1 blank line; classes need 2."
description: |-
  Decorators walk back to the true block top before counting blanks.
  Counts allow 0 (file start) or the configured value. Auto-fixable by
  protolib.test.core.helpers.auto_correct.
"""
from protolib.test.core.gov.helpers import c24

c24_params = {
    'blanks_before_def': 1,
    'blanks_before_class': 2,
}
RESULTS.update(run_check(c24, **c24_params))


## c36
"""
name: "c36 - inline literal size"
rule: "@rules/architecture_python.md"
purpose: "c36 — large in-def literals belong in settings or a resource."
description: |-
  AST scan for Dict/List/Set/Tuple literals assigned inside a def.
  Warns when entry count exceeds max_entries. Module-level literals
  are intentionally permitted. Suppressible at def scope via
  governance_exceptions: c36.
"""
from protolib.test.core.gov.helpers import c36

c36_params = {
    'max_entries': 8,
}
RESULTS.update(run_check(c36, **c36_params))


## c2
"""
name: "c2 - one-line module-level defs"
rule: "@rules/code_style_python.md"
purpose: "c2 — one-line module-level defs (warn)."
description: |-
  Module-level defs whose body is a single expression/return are usually
  scaffolding. dunders and exempt_names are skipped. Suppressible at def
  scope via governance_exceptions: c2.
"""
from protolib.test.core.gov.helpers import c2

c2_params = {
    'exempt_names': ['main'],       # dunders also exempt (heuristic: __x__)
}
RESULTS.update(run_check(c2, **c2_params))


## c4
"""
name: "c4 - direct kwargs access"
rule: "@rules/code_style_python.md"
purpose: "c4 — direct kwargs access (kwargs.get / kwargs[key]) is forbidden."
description: |-
  kwargs is transport, not contract. Named params on the signature are
  the contract. Suppressible at def scope via governance_exceptions: c4.
"""
from protolib.test.core.gov.helpers import c4

c4_params = {}
RESULTS.update(run_check(c4, **c4_params))


## c6
"""
name: "c6 - statement on semicolon"
rule: "@rules/code_style_python.md"
purpose: "c6 — `;`-joined statements are forbidden."
description: |-
  Mandatory-fix. Split or extract. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c6

c6_params = {}
RESULTS.update(run_check(c6, **c6_params))


## c7
"""
name: "c7 - eval/exec usage"
rule: "@rules/code_style_python.md"
purpose: "c7 — eval()/exec() calls are forbidden."
description: |-
  Mandatory-fix. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c7

c7_params = {}
RESULTS.update(run_check(c7, **c7_params))


## c8
"""
name: "c8 - class presence"
rule: "@rules/architecture_python.md"
purpose: "c8 — modules should define at least one class (warn)."
description: |-
  OOP is the primary paradigm. Modules with only stateless helpers may
  suppress at module scope via governance_exceptions: c8. Enum-only
  modules are auto-exempt by enum_bases regex.
"""
from protolib.test.core.gov.helpers import c8

c8_params = {
    'enum_bases': r'\((\w+\.)?(Enum|IntEnum|StrEnum|Flag|IntFlag)\)',
}
RESULTS.update(run_check(c8, **c8_params))


## c10
"""
name: "c10 - flat imports"
rule: "@rules/architecture_python.md"
purpose: "c10 — package imports must route through app/core/helpers/test."
description: |-
  Flat imports like `from <pkg> import foo` skip the architectural
  boundary. Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c10

c10_params = {
    'allowed_subpkgs': ['app', 'core', 'helpers', 'test'],
    'pkg': core_sts.package_name,   # PKG threaded for clone portability
}
RESULTS.update(run_check(c10, **c10_params))


## c13
"""
name: "c13 - class before function"
rule: "@rules/code_style_python.md"
purpose: "c13 — module-level classes must precede module-level functions."
description: |-
  Functions before classes signals procedural drift. Suppressible at
  module scope via governance_exceptions: c13.
"""
from protolib.test.core.gov.helpers import c13

c13_params = {}
RESULTS.update(run_check(c13, **c13_params))


## c16
"""
name: "c16 - pass-only function"
rule: "@rules/code_style_python.md"
purpose: "c16 — pass-only function bodies (warn)."
description: |-
  __init__ is exempt. Suppressible at def scope via
  governance_exceptions: c16.
"""
from protolib.test.core.gov.helpers import c16

c16_params = {
    'exempt_names': ['__init__'],
}
RESULTS.update(run_check(c16, **c16_params))


## c18
"""
name: "c18 - test pairing"
rule: "@rules/testing_project.md"
purpose: "c18 — every module must have a paired test_<module>.py."
description: |-
  Mandatory-fix. Cross-file scan against the test/ subtree.
"""
from protolib.test.core.gov.helpers import c18

c18_params = {}
RESULTS.update(run_check(c18, **c18_params))


## c19
"""
name: "c19 - mutable default arguments"
rule: "@rules/code_style_python.md"
purpose: "c19 — mutable default args (list/dict/set) are forbidden."
description: |-
  Mandatory-fix. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c19

c19_params = {}
RESULTS.update(run_check(c19, **c19_params))


## c20
"""
name: "c20 - main() name guard"
rule: "@rules/code_style_python.md"
purpose: "c20 — module-level main() must be guarded by __name__ == '__main__'."
description: |-
  Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c20

c20_params = {}
RESULTS.update(run_check(c20, **c20_params))


## c25
"""
name: "c25 - local imports"
rule: "@rules/code_style_python.md"
purpose: "c25 — imports inside def bodies (warn)."
description: |-
  Imports belong at module top. Suppressible at module scope via
  governance_exceptions: c25.
"""
from protolib.test.core.gov.helpers import c25

c25_params = {}
RESULTS.update(run_check(c25, **c25_params))


## c26
"""
name: "c26 - relative imports"
rule: "@rules/code_style_python.md"
purpose: "c26 — relative imports (`from .X` / `from ..X`) are forbidden."
description: |-
  Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c26

c26_params = {}
RESULTS.update(run_check(c26, **c26_params))


## c27
"""
name: "c27 - wildcard imports"
rule: "@rules/code_style_python.md"
purpose: "c27 — wildcard imports (`from X import *`) are forbidden."
description: |-
  Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c27

c27_params = {}
RESULTS.update(run_check(c27, **c27_params))


## c28
"""
name: "c28 - bare except"
rule: "@rules/code_style_python.md"
purpose: "c28 — bare `except:` clauses are forbidden."
description: |-
  Catch specific exception types. Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c28

c28_params = {}
RESULTS.update(run_check(c28, **c28_params))


## c29
"""
name: "c29 - hardcoded absolute paths"
rule: "@rules/code_style_python.md"
purpose: "c29 — hardcoded absolute paths in string literals (warn)."
description: |-
  Use settings or env vars instead. Suppressible at def scope via
  governance_exceptions: c29.
"""
from protolib.test.core.gov.helpers import c29

c29_params = {}
RESULTS.update(run_check(c29, **c29_params))


## c30
"""
name: "c30 - raw print() usage"
rule: "@rules/code_style_python.md"
purpose: "c30 — raw print() outside exempt scopes (warn)."
description: |-
  Use helpers/printing.py. exempt_paths whitelisted. Suppressible at
  def scope via governance_exceptions: c30.
"""
from protolib.test.core.gov.helpers import c30

c30_params = {
    'exempt_paths': ['/apis/', 'creator/', 'helpers/printing.py'],
}
RESULTS.update(run_check(c30, **c30_params))


## c32
"""
name: "c32 - stdlib logging"
rule: "@rules/architecture_python.md"
purpose: "c32 — stdlib `import logging` outside allowed paths is forbidden."
description: |-
  Use helpers/printing.py. Mandatory-fix outside allowed_paths.
"""
from protolib.test.core.gov.helpers import c32

c32_params = {
    'allowed_paths': ['helpers/printing.py'],
}
RESULTS.update(run_check(c32, **c32_params))


## c34
"""
name: "c34 - strip_ansi_codes redefinition"
rule: "@rules/architecture_python.md"
purpose: "c34 — strip_ansi_codes redefinition outside canonical module (warn)."
description: |-
  Single source of truth in helpers/printing.py. Suppressible at module
  scope via governance_exceptions: c34.
"""
from protolib.test.core.gov.helpers import c34

c34_params = {
    'canonical_path': 'helpers/printing.py',
}
RESULTS.update(run_check(c34, **c34_params))


## c35
"""
name: "c35 - core imports app"
rule: "@rules/architecture_python.md"
purpose: "c35 — core/ must not import app/."
description: |-
  Architectural boundary. Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c35

c35_params = {
    'scope_prefix': 'core/',
    'pkg': core_sts.package_name,   # PKG threaded for clone portability
}
RESULTS.update(run_check(c35, **c35_params))


## c40
"""
name: "c40 - helpers purity"
rule: "@rules/architecture_python.md"
purpose: "c40 — helpers/ must not import core/ or app/ (except app.settings)."
description: |-
  Helpers must remain stateless and dependency-free of orchestration
  layers. Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c40

c40_params = {
    'scope_prefix': 'helpers/',
    'app_settings_attr': 'settings',
    'pkg': core_sts.package_name,   # PKG threaded for clone portability
}
RESULTS.update(run_check(c40, **c40_params))


## c41
"""
name: "c41 - filename collisions"
rule: "@rules/architecture_python.md"
purpose: "c41 — duplicate basenames across the source tree (error)."
description: |-
  Cross-file scan. Mandatory-fix.
"""
from protolib.test.core.gov.helpers import c41

c41_params = {}
RESULTS.update(run_check(c41, **c41_params))


## c90_3
"""
name: "c90_3 - dorph"
rule: "@rules/module_gov.md"
purpose: "c90_3 — orphan governance_exceptions. Meta-rule."
description: |-
  For every governance_exceptions: cN entry, verify cN actually fired
  at that scope in this file. If cN did not fire, the exception is an
  orphan and should be removed. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c90_3

c90_3_params = {}
RESULTS.update(run_check(c90_3, **c90_3_params))


import sys as _sys
from pathlib import Path as _Path
from protolib.test.core.gov.base import run_master as _run_master


def run(*args, **kwargs) -> tuple:
    """purpose: 'Run the master governance suite; return (warnings_count, errors_count).'"""
    log_path = str(_Path(__file__).parent / "logs" / "governance_log.yaml")
    errs = _run_master(results=RESULTS, master_path=__file__, log_path=log_path)
    return [], [None] * errs


if __name__ == "__main__":
    _sys.exit(1 if run()[1] else 0)
