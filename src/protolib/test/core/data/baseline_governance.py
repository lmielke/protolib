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
from protolib.test.core.gov import settings as sts
from protolib.test.core.gov.base import run_check

# Registry of all checks. Populated by the literate sections below on import.
# Shape: {code: {"fn": callable, "kind": str, "exceptions_apply": bool,
#                "why": str, "fix": str, "auto_correct": callable | None}}
RESULTS: dict = {}


# Validations
# ============================================================================


## c90_1
"""
name: "c90_1 - dfmt"
rule: "@rules/module_gov.md"
purpose: "c90_1 — docstring front-matter format. Mandatory-fix (meta-rule)."
description: |-
  Validates docstring front-matter at module / class / def scope. Required
  and allowed key sets are scope-indexed and live in sts.checks['c90_1']
  as `.required` / `.allowed` dicts. Rejects unknown keys; flags missing
  required keys. Cannot be suppressed.
"""
from protolib.test.core.gov.helpers import c90_1

c90_1_params = {
    **sts.checks['c90_1'],          # base: required / allowed dicts (per scope)
    # 'extra_key': ...,             # rule-local extras go here when the rule needs them
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
    **sts.checks['c90_2'],          # base: scope-allowed code map
    # 'extra_key': ...,             # rule-local extras go here when the rule needs them
}
RESULTS.update(run_check(c90_2, **c90_2_params))
