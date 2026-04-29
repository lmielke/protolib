"""
script_path: src/protolib/test/core/helpers/gov/c16.py
purpose: "[TO_DELETE] c16 — pass-only function check. Flags defs whose body is just 'pass'."
description: "A pass-only function signals incomplete work or dead code; __init__ is exempt."
update_rules: "Do not modify in clones."
"""
from protolib.test.core.helpers.gov.base import parse_defs


def _c16_pass_only(lines, rel, *args, **kwargs):
    """purpose: Flag defs with real body equal to only 'pass' (exempt __init__)."""
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        real = [l.strip() for l in body if l.strip() and not l.strip().startswith("#")]
        if real == ["pass"] and name != "__init__":
            warn.append(f"line {lineno+1}: {name}() is pass-only — implement or remove")
    return warn, err
