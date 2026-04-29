"""
script_path: src/protolib/test/core/helpers/gov/c26.py
purpose: "[TO_DELETE] c26 — relative-import check. Forbids 'from .' / 'from ..' style imports."
description: "Relative imports break grepability and make module moves fragile. Auto-fixable."
update_rules: "Do not modify in clones."
"""
import re


def _c26_relative_imports(lines, rel, *args, **kwargs):
    """purpose: Flag any relative-import line."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*from\s+\.', line):
            warn.append(f"line {i+1}: relative import — use absolute")
    return warn, err
