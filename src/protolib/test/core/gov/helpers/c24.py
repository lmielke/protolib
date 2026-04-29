"""
script_path: src/protolib/test/core/gov/helpers/c24.py
paths: ["**/*.py"]
purpose: "Helper: c24 — top-level def/class spacing."
description: |-
  Module-level def needs blanks_before_def blank lines preceding it
  (or 0 if it's the first thing in a file). Module-level class needs
  blanks_before_class. Decorator lines walk back to the true block top.
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""
import re


def run(*args, lines, blanks_before_def, blanks_before_class, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    out = []
    for i, line in enumerate(lines):
        if i == 0 or _is_indented(line=line): continue
        if rec := _check(lines=lines, i=i, b_def=blanks_before_def, b_cls=blanks_before_class):
            out.append(rec)
    return out


def _is_indented(*args, line, **kwargs) -> bool:
    """purpose: 'True if line begins with whitespace.'"""
    return len(line) - len(line.lstrip()) != 0


def _check(*args, lines, i, b_def, b_cls, **kwargs) -> dict:
    """purpose: 'Record if leading blanks mismatch the def/class expectation.'"""
    stripped = lines[i].lstrip()
    blanks = _count_blanks(lines=lines, lineno=_block_top(lines=lines, i=i))
    if re.match(r'def \w+\(', stripped) and blanks not in (0, b_def):
        return _rec(i=i, blanks=blanks, kind="def", expected=b_def)
    if re.match(r'class \w+', stripped) and blanks not in (0, b_cls):
        return _rec(i=i, blanks=blanks, kind="class", expected=b_cls)
    return {}


def _count_blanks(*args, lines, lineno, **kwargs) -> int:
    """purpose: 'Consecutive blank lines preceding lineno.'"""
    n = 0
    for j in range(lineno - 1, -1, -1):
        if lines[j].strip(): break
        n += 1
    return n


def _block_top(*args, lines, i, **kwargs) -> int:
    """purpose: 'Walk past decorator lines to true top of def/class block.'"""
    j = i
    while j > 0 and lines[j - 1].lstrip().startswith('@'):
        j -= 1
    return j


def _rec(*args, i, blanks, kind, expected, **kwargs) -> dict:
    """purpose: 'Spacing violation record.'"""
    msg = f"{kind} needs {expected} blank line(s) before (has {blanks})"
    return {"line": i + 1, "scope": "module", "level": "warn", "technical_message": msg}
