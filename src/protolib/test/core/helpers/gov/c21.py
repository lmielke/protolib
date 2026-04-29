"""
script_path: src/protolib/test/core/helpers/gov/c21.py
purpose: "[TO_DELETE] c21 — repeated locals check. Flags identifiers assigned in many different defs."
description: "Names recurring in 3+ defs often belong on a class or shared parameter object."
update_rules: "Do not modify in clones."
"""
import re
from protolib.test.core.helpers.gov.base import parse_defs

_COMMON_LOCALS = {"self", "cls", "i", "j", "k", "x", "e", "f", "m", "n", "d", "l",
                  "result", "results", "output", "line", "lines", "path", "name",
                  "key", "value", "data", "item", "args", "kwargs", "err", "warn"}


def _c21_repeated_locals(lines, rel, *args, **kwargs):
    """purpose: Count distinct defs in which each non-common local is assigned."""
    warn, err = [], []
    var_fns = {}
    for lineno, indent, fn_name, body in parse_defs(lines):
        body_indent = " " * (indent + 4)
        for bl in body:
            mat = re.match(rf'^{body_indent}(\w+)\s*=\s', bl)
            if not mat: continue
            vname = mat.group(1)
            if vname.startswith("_") or vname in _COMMON_LOCALS: continue
            var_fns.setdefault(vname, set()).add(fn_name)
    for vname, fns in sorted(var_fns.items()):
        if len(fns) >= 3:
            warn.append(f"'{vname}' assigned in {len(fns)} functions — consider class/pkg parameter")
    return warn, err
