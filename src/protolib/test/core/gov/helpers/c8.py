"""
script_path: src/protolib/test/core/gov/helpers/c8.py
paths: ["**/*.py"]
purpose: "Helper: c8 — class presence check (warn). OOP is the primary paradigm."
description: |-
  Modules without any class definition emit one warn. Modules with classes
  but no __init__ emit a warn unless every class subclasses an enum base
  matched by `enum_bases`.
update_rules: "Do not modify in clones. enum_bases regex arrives via params."
"""
import re


def run(*args, lines, enum_bases, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    classes = [l for l in lines if re.match(r'^class \w+', l)]
    if not classes: return [_rec(msg="no class definition — verify OOP intent")]
    if any(re.match(r'\s+def (__init__|__post_init__)\(', l) for l in lines): return []
    if all(re.search(enum_bases, c) for c in classes): return []
    return [_rec(msg="class(es) without __init__ — may be enum/constant, verify OOP intent")]


def _rec(*args, msg, **kwargs) -> dict:
    """purpose: 'Build one warn record at module scope.'"""
    return {"level": "warn", "line": 1, "scope": "module", "technical_message": msg}
