"""
script_path: src/protolib/test/core/gov/helpers/c29.py
paths: ["**/*.py"]
purpose: "Helper: c29 — hardcoded absolute paths in string literals."
description: |-
  Scans each non-comment line for string literals starting with /home/,
  /tmp/, or a Windows drive letter. Emits 'warn' per match — paths
  belong in settings or anchors (os.path / pathlib).
update_rules: "Do not modify in clones. Pattern is structural, kept inline."
"""
import re

_PAT = re.compile(r'["\'][A-Z]:\\|["\']/home/|["\']/tmp/')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [_rec(i=i) for i, line in enumerate(lines)
            if not line.strip().startswith('#') and _PAT.search(line)]


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a hardcoded-path line.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "hardcoded path — use settings or os.path"}
