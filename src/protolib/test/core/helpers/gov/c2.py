"""
script_path: src/protolib/test/core/helpers/gov/c2.py
purpose: "[TO_DELETE] c2 — one-line function check. Flags module-level defs with a single real body line."
description: "Dunder methods and main() are exempt. One-liners usually inline better."
update_rules: "Do not modify in clones."
"""
from protolib.test.core.helpers.gov.base import parse_defs


def _c2_one_line_functions(lines, rel, *args, **kwargs):
    """purpose: Flag module-level defs whose body is a single real line."""
    warn, err = [], []
    for lineno, indent, name, body in parse_defs(lines):
        if indent != 0: continue
        if (name.startswith('__') and name.endswith('__')) or name == 'main': continue
        real = [l for l in body if not l.strip().startswith("#")]
        if len(real) == 1:
            warn.append(f"line {lineno+1}: {name}() is one-line — candidate to inline")
    return warn, err
