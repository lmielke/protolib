"""
script_path: src/protolib/test/core/gov/helpers/c34.py
paths: ["**/*.py"]
purpose: "Helper: c34 — strip_ansi_codes redefinition outside the canonical module."
description: |-
  Skips the canonical module. Otherwise scans for any line defining
  `strip_ansi_codes(` and emits 'warn' per match — duplicate definitions
  drift silently from the canonical version.
update_rules: "Do not modify in clones. canonical_path arrives via params."
"""
import re

_PAT = re.compile(r'^\s*def strip_ansi_codes\(')


def run(*args, lines, rel, canonical_path, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if rel == canonical_path: return []
    return [_rec(i=i) for i, line in enumerate(lines) if _PAT.match(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a strip_ansi_codes redefinition.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "strip_ansi_codes redefined — import from helpers/printing"}
