"""
script_path: src/protolib/test/core/helpers/gov/c19.py
purpose: "[TO_DELETE] c19 — mutable default argument check. Flags defs with [], {}, or set() defaults."
description: "Mutable defaults persist across calls — use None and assign in the body."
update_rules: "Do not modify in clones."
"""
import re


def _c19_mutable_defaults(lines, rel, *args, **kwargs):
    """purpose: Flag def lines with mutable default arguments."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if not re.match(r'\s*def ', line): continue
        if re.search(r'=\s*\[\]|=\s*\{\}|=\s*set\(\)', line):
            warn.append(f"line {i+1}: mutable default argument — use None instead")
    return warn, err
