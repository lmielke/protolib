"""
script_path: src/protolib/test/core/helpers/gov/c34.py
purpose: "[TO_DELETE] c34 — strip_ansi_codes redefinition check. Only helpers/printing owns the canonical def."
description: "Redefining strip_ansi_codes creates silent drift from the helpers/printing version."
update_rules: "Do not modify in clones."
"""
import re

_STRIP_ANSI_CANONICAL = "helpers/printing.py"


def _c34_strip_ansi_redef(lines, rel, *args, **kwargs):
    """purpose: Flag any def of strip_ansi_codes outside the canonical module."""
    warn, err = [], []
    if rel == _STRIP_ANSI_CANONICAL: return warn, err
    for i, line in enumerate(lines):
        if re.match(r'\s*def strip_ansi_codes\(', line):
            warn.append(f"line {i+1}: strip_ansi_codes redefined — import from helpers/printing")
    return warn, err
