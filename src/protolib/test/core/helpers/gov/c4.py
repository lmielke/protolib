"""
script_path: src/protolib/test/core/helpers/gov/c4.py
purpose: "[TO_DELETE] c4 — kwargs direct-access check. Forbids kwargs.get() and kwargs[key]."
description: "Direct kwargs access bypasses param forwarding; declare named params instead."
update_rules: "Do not modify in clones."
"""
import re


def _c4_kwargs_access(lines, rel, *args, **kwargs):
    """purpose: Flag kwargs.get() or kwargs[key] — must use named parameters."""
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.split("#")[0]
        if re.search(r'kwargs\.get\(', s) or re.search(r'kwargs\[', s):
            err.append(f"line {i+1}: kwargs accessed directly — use forwarding")
    return warn, err
