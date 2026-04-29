"""
script_path: src/protolib/test/core/gov/helpers/c30.py
paths: ["**/*.py"]
purpose: "Helper: c30 — raw print() outside exempt scopes (warn)."
description: |-
  Scans for the first `print(` call in modules whose `rel` path does
  not contain any of `exempt_paths`. Emits a single 'warn' per file.
update_rules: "Do not modify in clones. exempt_paths arrives via params."
"""
import re

_PAT = re.compile(r'^\s*print\s*\(')


def run(*args, lines, rel, exempt_paths, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if any(p in rel for p in exempt_paths): return []
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        if _PAT.match(line): return [_rec(i=i)]
    return []


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one warn record for a raw-print line.'"""
    return {"level": "warn", "line": i + 1, "scope": "module",
            "technical_message": "raw print() — use logprint or move to API"}
