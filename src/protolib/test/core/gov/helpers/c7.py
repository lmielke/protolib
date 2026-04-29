"""
script_path: src/protolib/test/core/gov/helpers/c7.py
paths: ["**/*.py"]
purpose: "Helper: c7 — eval/exec usage check. Flags eval()/exec() calls in source."
description: |-
  Scans each line (after stripping comments) for `eval(` or `exec(` calls.
  Emits 'error' per match — these execute arbitrary strings and bypass
  the type system. Cannot be suppressed.
update_rules: "Do not modify in clones. Pure pattern; no thresholds."
"""
import re

_PAT = re.compile(r'\b(eval|exec)\s*\(')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines)
            if _PAT.search(line.split("#", 1)[0])]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one error record for an eval/exec line.'"""
    return {"level": "error", "line": i + 1, "scope": "def",
            "technical_message": "eval/exec usage"}
