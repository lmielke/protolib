"""
script_path: src/protolib/test/core/gov/helpers/c32.py
paths: ["**/*.py"]
purpose: "Helper: c32 — stdlib `import logging` is forbidden outside allowed paths."
description: |-
  Skips files in allowed_paths. Otherwise scans for the first line that
  imports the stdlib logging module (either `from logging` or `import …
  logging`) and emits one 'warn' record. Use logprint instead.
update_rules: "Do not modify in clones. allowed_paths via params."
"""
import re

_PAT_FROM = re.compile(r'^from logging\b')
_PAT_IMPORT = re.compile(r'\blogging\b')


def run(*args, lines, rel, allowed_paths, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if rel in set(allowed_paths): return []
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('#'): continue
        if _PAT_FROM.match(s) or (s.startswith('import ') and _PAT_IMPORT.search(s)):
            return [_rec(i=i)]
    return []


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record at module scope.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "import logging — use logprint from helpers/printing"}
