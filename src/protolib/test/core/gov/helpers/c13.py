"""
script_path: src/protolib/test/core/gov/helpers/c13.py
paths: ["**/*.py"]
purpose: "Helper: c13 — module-level classes must precede module-level functions."
description: |-
  Finds the first `^def \\w+` and the first `^class \\w+` line. Emits one
  'warn' record when the def appears before the class.
update_rules: "Do not modify in clones. No thresholds."
"""
import re

_DEF = re.compile(r'^def \w+')
_CLS = re.compile(r'^class \w+')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    first_def = next((i for i, l in enumerate(lines) if _DEF.match(l)), None)
    first_cls = next((i for i, l in enumerate(lines) if _CLS.match(l)), None)
    if first_def is None or first_cls is None or first_def >= first_cls: return []
    return [{"level": "warn", "line": first_def + 1, "scope": "module",
             "technical_message": "module-level function before first class"}]
