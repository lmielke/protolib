"""
script_path: src/protolib/test/core/gov/helpers/c1.py
paths: ["**/*.py"]
purpose: "Helper: c1 — def length. Emit violation records per FunctionDef."
description: |-
  Walks the AST for FunctionDef / AsyncFunctionDef. Counts body code lines
  via base._code_lines (excludes docstring, blank, comment-only). Emits
  'error' when count > params['max'], 'warn' when count > params['warn'].
  Composes own technical_message / display_message inline from params.
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""
import ast

from protolib.test.core.gov.base import _code_lines


def run(*args, lines, tree, warn, max, **params) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    records = []
    for node in _defs(tree=tree):
        if rec := _check(node=node, lines=lines, warn=warn, max=max):
            records.append(rec)
    return records


def _defs(*args, tree, **kwargs) -> list:
    """purpose: 'Return all FunctionDef / AsyncFunctionDef nodes anywhere in tree.'"""
    types = (ast.FunctionDef, ast.AsyncFunctionDef)
    return [n for n in ast.walk(tree) if isinstance(n, types)]


def _check(*args, node, lines, warn, max, **kwargs) -> dict:
    """purpose: 'Return violation record if node trips threshold else {}.'"""
    n = _count(node=node, lines=lines)
    level = "error" if n > max else ("warn" if n > warn else None)
    if level is None: return {}
    tech = f"{node.name}() has {n} lines (max {max})" if level == "error" \
           else f"{node.name}() has {n} lines (warn >{warn}, error >{max})"
    return {"level": level, "line": node.lineno, "scope": "def", "node": node.name,
            "technical_message": tech}


def _count(*args, node, lines, **kwargs) -> int:
    """purpose: 'Count code lines in def body — excludes docstring, blank, comment.'"""
    body = node.body[1:] if ast.get_docstring(node) else node.body
    if not body: return 0
    span = lines[body[0].lineno - 1 : body[-1].end_lineno]
    return len(_code_lines(span))
