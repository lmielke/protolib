"""
script_path: src/protolib/test/core/helpers/gov/c32.py
purpose: "[TO_DELETE] c32 — stdlib-logging check. Forbids 'import logging' outside helpers/printing."
description: "Use logprint from helpers/printing; stdlib logging duplicates configuration."
update_rules: "Do not modify in clones."
"""
import re

_LOGGING_ALLOWED = {"helpers/printing.py"}


def _c32_stdlib_logging(lines, rel, *args, **kwargs):
    """purpose: Flag first stdlib-logging import in non-exempt modules."""
    warn, err = [], []
    if rel in _LOGGING_ALLOWED: return warn, err
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'): continue
        if re.match(r'from logging\b', stripped) or (
                stripped.startswith('import ') and re.search(r'\blogging\b', stripped)):
            warn.append(f"line {i+1}: import logging — use logprint from helpers/printing")
            break
    return warn, err
