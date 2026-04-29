"""
script_path: src/protolib/test/core/gov/helpers/c19.py
paths: ["**/*.py"]
purpose: "Helper: c19 — mutable default arguments (warn)."
description: |-
  Scans def signature lines for `=[]`, `={}`, or `=set()` mutable
  defaults. Emits one warn per matched line. Mutable defaults persist
  across calls — use None and assign in the body.
update_rules: "Do not modify in clones. No thresholds."
"""
import re

_DEF = re.compile(r'\s*def ')
_MUT = re.compile(r'=\s*\[\]|=\s*\{\}|=\s*set\(\)')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines)
            if _DEF.match(line) and _MUT.search(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a mutable-default line.'"""
    return {"level": "warn", "line": i + 1, "scope": "def",
            "technical_message": "mutable default argument — use None instead"}
