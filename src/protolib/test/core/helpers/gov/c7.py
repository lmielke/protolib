"""
script_path: src/protolib/test/core/helpers/gov/c7.py
purpose: "[TO_DELETE] c7 — eval/exec usage check. Flags any eval() or exec() call in source."
description: "eval/exec execute arbitrary strings — security risk and debuggability hazard."
update_rules: "Do not modify in clones."
"""
import re


def _c7_eval_exec(lines, rel, *args, **kwargs):
    """purpose: Flag eval() or exec() calls outside comments."""
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.split("#")[0]
        if re.search(r'\beval\s*\(', s) or re.search(r'\bexec\s*\(', s):
            err.append(f"line {i+1}: eval/exec usage")
    return warn, err
