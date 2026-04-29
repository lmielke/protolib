"""
script_path: src/protolib/test/core/gov/helpers/c27.py
paths: ["**/*.py"]
purpose: "Helper: c27 — wildcard imports (`from X import *`) are forbidden."
description: |-
  Scans each line for the wildcard-import pattern. Emits 'warn' per match —
  wildcard imports hide dependencies and pollute the module namespace.
update_rules: "Do not modify in clones. Pattern only; no thresholds."
"""
import re

_PAT = re.compile(r'^\s*from\s+\S+\s+import\s+\*')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines) if _PAT.match(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a wildcard-import line.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "wildcard import — import names explicitly"}
