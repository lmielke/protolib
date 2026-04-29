"""
script_path: src/protolib/test/core/helpers/gov/c5.py
purpose: "[TO_DELETE] c5 — kwargs signature check. Defs must take *args/**kwargs on the def line."
description: "Missing *args/**kwargs breaks hook-compatible forwarding across the call stack."
update_rules: "Do not modify in clones."
"""
from protolib.test.core.helpers.gov.base import parse_defs, _signature_text


def _c5_kwargs_signature(lines, rel, *args, **kwargs):
    """purpose: Flag defs missing *args/**kwargs on their signature line."""
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        sig_line = _signature_text(lines, lineno)
        has_args = "*args" in sig_line
        has_kwargs = "**kwargs" in sig_line
        if has_kwargs and not has_args:
            warn.append(f"line {lineno+1}: {name}() has **kwargs but no *args on same def line")
        real = [l for l in body if l.strip() and not l.strip().startswith("#")]
        if not has_args and not has_kwargs and len(real) > 2:
            warn.append(f"line {lineno+1}: {name}() missing *args/**kwargs on def line — required by kwargs hook")
    return warn, err
