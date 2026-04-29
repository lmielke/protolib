"""
script_path: src/protolib/test/core/helpers/gov/c28.py
purpose: "[TO_DELETE] c28 — bare-except check. Forbids 'except:' without an exception type."
description: "Bare except masks KeyboardInterrupt/SystemExit. Auto-fixable."
update_rules: "Do not modify in clones."
"""
import re


def _c28_bare_except(lines, rel, *args, **kwargs):
    """purpose: Flag any 'except:' line without an exception type."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*except\s*:', line):
            warn.append(f"line {i+1}: bare except — specify exception type")
    return warn, err
