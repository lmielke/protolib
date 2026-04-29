"""
script_path: src/protolib/test/core/helpers/gov/c10.py
purpose: "[TO_DELETE] c10 — flat import check. Imports must route through app/core/helpers/test."
description: "Flat imports like 'protolib.foo' bypass layering and break clone portability."
update_rules: "Do not modify in clones."
"""
import re
import protolib.core.settings as sts

PKG = sts.package_name
_C10_ALLOWED_SUBPKGS = ("app", "core", "helpers", "test")


def _c10_flat_imports(lines, rel, *args, **kwargs):
    """purpose: Flag imports of PKG.<subpkg> that are not app/core/helpers/test."""
    warn, err = [], []
    pat = re.compile(rf'(?:import|from)\s+{PKG}\.(\w+)')
    for i, line in enumerate(lines):
        m = pat.search(line.split("#")[0])
        if m and m.group(1) not in _C10_ALLOWED_SUBPKGS:
            err.append(f"line {i+1}: flat import '{PKG}.{m.group(1)}' — use app/core/helpers only")
    return warn, err
