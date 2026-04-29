"""
script_path: src/protolib/test/core/helpers/gov/c13.py
purpose: "[TO_DELETE] c13 — class-before-function check. Module-level classes must precede functions."
description: "Consistent ordering (classes first) makes navigation predictable."
update_rules: "Do not modify in clones."
"""
import re


def _c13_class_before_function(lines, rel, *args, **kwargs):
    """purpose: Flag first module-level function appearing before the first class."""
    warn, err = [], []
    first_def = next((i for i, l in enumerate(lines) if re.match(r'^def \w+', l)), None)
    first_cls = next((i for i, l in enumerate(lines) if re.match(r'^class \w+', l)), None)
    if first_def is not None and first_cls is not None and first_def < first_cls:
        warn.append(f"line {first_def+1}: module-level function before first class")
    return warn, err
