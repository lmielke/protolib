"""
script_path: src/protolib/test/core/helpers/gov/c35.py
purpose: "[TO_DELETE] c35 — core-imports-app check. Forbids core/ modules from importing app/."
description: "core/ must be self-contained and present in all clones; app/ is user-owned."
update_rules: "Do not modify in clones."
"""
import re
import protolib.core.settings as sts

PKG = sts.package_name


def _c35_core_imports_app(lines, rel, *args, **kwargs):
    """purpose: Flag first 'import PKG.app' line in any core/ module."""
    warn, err = [], []
    if not rel.startswith("core/"): return warn, err
    pat = re.compile(rf'(?:import|from)\s+{PKG}\.app\b')
    for i, line in enumerate(lines):
        if pat.search(line.split("#")[0]):
            err.append(f"line {i+1}: core module imports from app — core must be self-contained")
            break
    return warn, err
