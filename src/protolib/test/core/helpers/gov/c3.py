"""
script_path: src/protolib/test/core/helpers/gov/c3.py
purpose: "[TO_DELETE] c3 — module length check. Warns at >300 lines, errors at >500."
description: |-
  Skips modules below the minimum threshold (10 lines) — stub __init__.py and
  tiny per-rule gov/cN.py files are intentionally small and do not trip c3.
update_rules: "Do not modify in clones."
"""
_C3_MIN = 10


def _c3_module_length(lines, rel, *args, **kwargs):
    """purpose: Flag over-long modules; skip below the min-length threshold."""
    warn, err = [], []
    n = len(lines)
    if n < _C3_MIN: return warn, err
    if n > 500: err.append(f"module has {n} lines (max 500)")
    elif n > 300: warn.append(f"module has {n} lines (>300)")
    return warn, err
