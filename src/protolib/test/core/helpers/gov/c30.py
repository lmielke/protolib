"""
script_path: src/protolib/test/core/helpers/gov/c30.py
purpose: "[TO_DELETE] c30 — raw print() check. Forbids print() outside API and creator scopes."
description: "Use logprint from helpers/printing, or move output to an API module."
update_rules: "Do not modify in clones."
"""
import re

_C30_EXEMPT = ("/apis/", "creator/", "helpers/printing.py")


def _c30_raw_print(lines, rel, *args, **kwargs):
    """purpose: Flag first raw print() call in non-exempt modules."""
    warn, err = [], []
    if any(p in rel for p in _C30_EXEMPT): return warn, err
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        if re.match(r'\s*print\s*\(', line):
            warn.append(f"line {i+1}: raw print() — use logprint or move to API")
            break
    return warn, err
