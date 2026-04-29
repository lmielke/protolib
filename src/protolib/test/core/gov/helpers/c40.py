"""
script_path: src/protolib/test/core/gov/helpers/c40.py
paths: ["**/*.py"]
purpose: "Helper: c40 — helpers/ must not import core/ or app/ (except app.settings)."
description: |-
  Active only when `rel` starts with scope_prefix. Flags every line that
  imports PKG.core (always error) or PKG.app.<x> where x != settings.
  helpers/ must be portable to clones where core/ may be absent.
update_rules: "Do not modify in clones. PKG / scope_prefix via params."
"""
import re


def run(*args, lines, rel, pkg, scope_prefix, app_settings_attr, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if not rel.startswith(scope_prefix): return []
    pc = re.compile(rf'(?:import|from)\s+{re.escape(pkg)}\.core\b')
    pa = re.compile(rf'(?:import|from)\s+{re.escape(pkg)}\.app(?!\.{app_settings_attr}\b)\b')
    return [r for i, line in enumerate(lines)
            if (r := _check(i=i, line=line.split("#", 1)[0], pc=pc, pa=pa))]


def _check(*args, i, line, pc, pa, **kwargs) -> dict:
    """purpose: 'Return error record if line imports core or non-settings app.'"""
    if pc.search(line):
        return {"level": "error", "line": i + 1, "scope": "module",
                "technical_message": "helpers imports from core — core may be absent in clones"}
    if pa.search(line):
        return {"level": "error", "line": i + 1, "scope": "module",
                "technical_message": "helpers imports from app (except app.settings) — purity"}
    return {}
