"""
script_path: src/protolib/test/core/gov/helpers/c26.py
paths: ["**/*.py"]
purpose: "Helper: c26 — relative imports (`from .X` / `from ..X`) are forbidden."
description: |-
  Scans each line for the relative-import prefix `from .`. Emits 'warn' per
  match — relative imports break grepability and module-move portability.
  Auto-fixable.
update_rules: "Do not modify in clones. Pattern only; no thresholds."
"""
import re

_PAT = re.compile(r'^\s*from\s+\.')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines) if _PAT.match(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a relative-import line.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "relative import — use absolute"}
