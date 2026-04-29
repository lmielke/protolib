"""
script_path: src/protolib/test/core/gov/helpers/c35.py
paths: ["**/*.py"]
purpose: "Helper: c35 — core/ must not import app/."
description: |-
  Active only when `rel` starts with scope_prefix. Flags the FIRST line
  importing PKG.app — emits one 'error' record per file. core/ ships in
  every clone; app/ is user-owned and may be absent.
update_rules: "Do not modify in clones. PKG / scope_prefix via params."
"""
import re


def run(*args, lines, rel, pkg, scope_prefix, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if not rel.startswith(scope_prefix): return []
    pat = re.compile(rf'(?:import|from)\s+{re.escape(pkg)}\.app\b')
    for i, line in enumerate(lines):
        if pat.search(line.split("#", 1)[0]): return [_rec(i=i)]
    return []


def _rec(*args, i, **kwargs) -> dict:
    """purpose: 'Build one error record for a core→app import.'"""
    return {"level": "error", "line": i + 1, "scope": "module",
            "technical_message": "core module imports from app — core must be self-contained"}
