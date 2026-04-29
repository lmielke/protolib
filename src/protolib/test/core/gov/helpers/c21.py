"""
script_path: src/protolib/test/core/gov/helpers/c21.py
paths: ["**/*.py"]
purpose: "Helper: c21 — repeated locals across defs."
description: |-
  Scans every def body for simple `name =` assignments. Names appearing
  in min_fns or more distinct functions are flagged — they often belong
  on a class instance attribute or pkg-level constant. Skips common
  loop indices, error vars, and dunder-prefixed locals.
update_rules: "Do not modify in clones. Threshold arrives via **params from settings.yml."
"""
import re

from protolib.test.core.gov.base import parse_defs

_COMMON = {"self", "cls", "i", "j", "k", "x", "e", "f", "m", "n", "d", "l",
           "result", "results", "output", "line", "lines", "path", "name",
           "key", "value", "data", "item", "args", "kwargs", "err", "warn"}


def run(*args, lines, min_fns, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    var_fns = _collect(lines=lines)
    return [_rec(name=v, fns=fns) for v, fns in sorted(var_fns.items())
            if len(fns) >= min_fns]


def _collect(*args, lines, **kwargs) -> dict:
    """purpose: 'Map: variable_name -> set of def_names that assign it.'"""
    var_fns = {}
    for lineno, indent, fn_name, body in parse_defs(lines):
        _add(var_fns=var_fns, indent=indent, fn_name=fn_name, body=body)
    return var_fns


def _add(*args, var_fns, indent, fn_name, body, **kwargs):
    """purpose: 'Record name -> fn_name for each top-of-body assignment.'"""
    body_indent = " " * (indent + 4)
    for bl in body:
        m = re.match(rf'^{body_indent}(\w+)\s*=\s', bl)
        if m and (v := m.group(1)) and not v.startswith("_") and v not in _COMMON:
            var_fns.setdefault(v, set()).add(fn_name)


def _rec(*args, name, fns, **kwargs) -> dict:
    """purpose: 'One warn record per high-fanout local.'"""
    msg = f"'{name}' assigned in {len(fns)} functions — consider class/pkg parameter"
    return {"line": 1, "scope": "module", "level": "warn", "technical_message": msg}
