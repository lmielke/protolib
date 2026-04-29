"""
script_path: src/protolib/test/core/helpers/gov/c24.py
purpose: "[TO_DELETE] c24 — def spacing check. Top-level defs need 1 blank line before, classes 2."
description: "Auto-fixable by protolib.test.core.helpers.auto_correct. Decorators counted as block top."
update_rules: "Do not modify in clones."
"""
import re


def _count_preceding_blanks(lines, lineno, *args, **kwargs) -> int:
    """purpose: Count consecutive blank lines immediately preceding `lineno`."""
    count = 0
    for i in range(lineno - 1, -1, -1):
        if not lines[i].strip(): count += 1
        else: break
    return count


def _block_top(lines, i, *args, **kwargs) -> int:
    """purpose: Walk past decorator lines to locate the true top of the def/class block."""
    j = i
    while j > 0 and lines[j - 1].lstrip().startswith('@'):
        j -= 1
    return j


def _c24_def_spacing(lines, rel, *args, **kwargs):
    """purpose: Flag top-level defs/classes without the correct leading blank-line count."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if i == 0: continue
        stripped = line.lstrip()
        if len(line) - len(stripped) != 0: continue
        blanks = _count_preceding_blanks(lines, _block_top(lines, i))
        if re.match(r'def \w+\(', stripped) and blanks not in (0, 1):
            warn.append(f"line {i+1}: def needs 1 blank line before (has {blanks})")
        elif re.match(r'class \w+', stripped) and blanks not in (0, 2):
            warn.append(f"line {i+1}: class needs 2 blank lines before (has {blanks})")
    return warn, err
