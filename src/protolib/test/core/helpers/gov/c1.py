"""
script_path: src/protolib/test/core/helpers/gov/c1.py
purpose: "[TO_DELETE] c1 — function length check. Mandatory-fix rule: max 10 code lines per def."
description: "Warns at >8 code lines, errors at >10. Excludes comments and docstrings."
update_rules: "Do not modify in clones."
"""
from protolib.test.core.helpers.gov.base import parse_defs, _code_lines


def _c1_function_length(lines, rel, *args, **kwargs):
    """purpose: Flag defs whose code-line count exceeds thresholds."""
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        n = len(_code_lines(body))
        if n > 10: err.append(f"line {lineno+1}: {name}() has {n} lines (max 10)")
        elif n > 8: warn.append(f"line {lineno+1}: {name}() has {n} lines (>8)")
    return warn, err
