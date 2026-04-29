"""
script_path: src/protolib/test/core/helpers/gov/c14.py
purpose: "[TO_DELETE] c14 — elif-chain length check. Warns at >3 elif branches in one def."
description: "Long elif chains resist exhaustive testing; prefer dispatch dicts."
update_rules: "Do not modify in clones."
"""
import re
from protolib.test.core.helpers.gov.base import parse_defs


def _c14_elif_chains(lines, rel, *args, **kwargs):
    """purpose: Count elif occurrences per def; flag when more than 3."""
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        count = sum(1 for l in body if re.match(r'\s+elif ', l))
        if count > 3:
            warn.append(f"line {lineno+1}: {name}() has {count} elif branches (>3)")
    return warn, err
