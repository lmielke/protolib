"""
script_path: src/protolib/test/core/helpers/gov/c12.py
purpose: "[TO_DELETE] c12 — class count check. Warns at >5 classes in one module."
description: "Too many classes in one module usually means it has more than one responsibility."
update_rules: "Do not modify in clones."
"""
import re


def _c12_class_count(lines, rel, *args, **kwargs):
    """purpose: Flag modules with more than 5 top-level class definitions."""
    warn, err = [], []
    count = len(re.findall(r'^class \w+', "".join(lines), re.MULTILINE))
    if count > 5:
        warn.append(f"{count} classes in module (>5) — consider splitting")
    return warn, err
