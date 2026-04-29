"""
script_path: src/protolib/test/core/gov/helpers/c4.py
paths: ["**/*.py"]
purpose: "Helper: c4 — direct kwargs access (kwargs.get / kwargs[key]) is forbidden."
description: |-
  Scans each line for `kwargs.get(` or `kwargs[`. Comments are stripped.
  Emits 'error' per match — direct access bypasses the forwarding contract.
update_rules: "Do not modify in clones. Pure pattern; no thresholds."
"""
import re

_PAT = re.compile(r'kwargs\.get\(|kwargs\[')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i, line=line) for i, line in enumerate(lines)
            if _PAT.search(line.split("#", 1)[0])]


def _rec(*args, i, line, **kwargs) -> dict:
    """purpose: 'Build one error record for a kwargs-access line.'"""
    return {"level": "error", "line": i + 1, "scope": "def",
            "technical_message": "kwargs accessed directly — use forwarding"}
