"""
script_path: src/protolib/test/core/helpers/gov/c25.py
purpose: "[TO_DELETE] c25 — local-import check. Flags imports inside function bodies."
description: "Local imports hide dependencies and usually signal a circular-import workaround."
update_rules: "Do not modify in clones."
"""
import re
from protolib.test.core.helpers.gov.base import parse_defs, find_body_end


def _c25_local_imports(lines, rel, *args, **kwargs):
    """purpose: Flag import statements inside def bodies."""
    warn, err = [], []
    for start, indent, name, _ in parse_defs(lines):
        end = find_body_end(lines, start, indent)
        for i in range(start + 1, end):
            stripped = lines[i].lstrip()
            if stripped.startswith("#"): continue
            if re.match(r'(import\s+|from\s+\S+\s+import\s+)', stripped):
                warn.append(f"line {i+1}: local import in {name}() — move to module top")
    return warn, err
