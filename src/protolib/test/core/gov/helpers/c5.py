"""
script_path: src/protolib/test/core/gov/helpers/c5.py
paths: ["**/*.py"]
purpose: "Helper: c5 — kwargs signature. Defs must take *args/**kwargs on the def line."
description: |-
  Walks every FunctionDef. Two emission cases:
    1. Has **kwargs but no *args  → warn (always).
    2. Missing both *args and **kwargs → warn only when body has
       > min_body_lines real (non-blank, non-comment) code lines.
update_rules: "Do not modify in clones. Threshold arrives via **params from settings.yml."
"""
import ast

from protolib.test.core.gov.base import _code_lines

_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def run(*args, tree, lines, min_body_lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    out = []
    for node in [n for n in ast.walk(tree) if isinstance(n, _DEFS)]:
        out += _check(node=node, lines=lines, min_body_lines=min_body_lines)
    return out


def _check(*args, node, lines, min_body_lines, **kwargs) -> list:
    """purpose: 'Per-def records — kwargs-only or missing-both depending on body size.'"""
    has_a, has_k = node.args.vararg is not None, node.args.kwarg is not None
    if has_a and has_k: return []
    if has_k and not has_a:
        return [_rec(node=node, msg=f"{node.name}() has **kwargs but no *args")]
    return _gate(node=node, lines=lines, min_body_lines=min_body_lines)


def _gate(*args, node, lines, min_body_lines, **kwargs) -> list:
    """purpose: 'Emit missing-both record only when body exceeds min_body_lines.'"""
    body = node.body[1:] if ast.get_docstring(node) else node.body
    if not body: return []
    span = lines[body[0].lineno - 1: body[-1].end_lineno]
    if len(_code_lines(span)) <= min_body_lines: return []
    return [_rec(node=node, msg=f"{node.name}() missing *args/**kwargs on def line")]


def _rec(*args, node, msg, **kwargs) -> dict:
    """purpose: 'Build one warn-level violation record.'"""
    return {"line": node.lineno, "scope": "def", "level": "warn",
            "technical_message": msg}
