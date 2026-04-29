"""
script_path: src/protolib/test/core/gov/helpers/c28.py
paths: ["**/*.py"]
purpose: "Helper: c28 — bare `except:` clauses are forbidden."
description: |-
  Scans each line for `except:` without an exception type. Emits 'warn'
  per match — bare except masks KeyboardInterrupt / SystemExit and hides
  real failures. Auto-fixable.
update_rules: "Do not modify in clones. Pattern only; no thresholds."
"""
import re

_PAT = re.compile(r'^\s*except\s*:')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines) if _PAT.match(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a bare-except line.'"""
    return {"level": "warn", "line": i + 1, "scope": "def",
            "technical_message": "bare except — specify exception type"}
