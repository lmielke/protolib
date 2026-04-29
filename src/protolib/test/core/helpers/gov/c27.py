"""
script_path: src/protolib/test/core/helpers/gov/c27.py
purpose: "[TO_DELETE] c27 — wildcard-import check. Forbids 'from X import *'."
description: "Wildcard imports hide dependencies and pollute the module namespace."
update_rules: "Do not modify in clones."
"""
import re


def _c27_wildcard_imports(lines, rel, *args, **kwargs):
    """purpose: Flag any 'from X import *' line."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*from\s+\S+\s+import\s+\*', line):
            warn.append(f"line {i+1}: wildcard import — import names explicitly")
    return warn, err
