"""
script_path: src/protolib/test/core/helpers/gov/c40.py
purpose: "[TO_DELETE] c40 — helpers purity check. Forbids helpers/ from importing core/ or app/."
description: "helpers/ must be portable to clones; only stdlib, app.settings, other helpers allowed."
update_rules: "Do not modify in clones."
"""
import re
import protolib.core.settings as sts

PKG = sts.package_name


def _c40_helpers_purity(lines, rel, *args, **kwargs):
    """purpose: Flag core/ or app/ imports in any helpers/ module."""
    warn, err = [], []
    if not rel.startswith("helpers/"): return warn, err
    pat_core = re.compile(rf'(?:import|from)\s+{PKG}\.core\b')
    pat_app = re.compile(rf'(?:import|from)\s+{PKG}\.app(?!\.settings\b)\b')
    for i, line in enumerate(lines):
        stripped = line.split("#")[0]
        if pat_core.search(stripped):
            err.append(f"line {i+1}: helpers imports from core — core may be absent in clones")
        elif pat_app.search(stripped):
            err.append(f"line {i+1}: helpers imports from app (except app.settings) — purity")
    return warn, err
