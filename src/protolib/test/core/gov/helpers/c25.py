"""
script_path: src/protolib/test/core/gov/helpers/c25.py
paths: ["**/*.py"]
purpose: "Helper: c25 — local imports inside def bodies (warn)."
description: |-
  Walks every FunctionDef / AsyncFunctionDef in the AST and emits 'warn'
  for any Import / ImportFrom node nested inside its body. Local imports
  hide dependencies and usually signal a circular-import workaround.
update_rules: "Do not modify in clones. AST-based; no thresholds."
"""
import ast


def run(*args, tree, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    types = (ast.FunctionDef, ast.AsyncFunctionDef)
    return [_rec(node=n, name=fn.name)
            for fn in ast.walk(tree) if isinstance(fn, types)
            for n in ast.walk(fn) if isinstance(n, (ast.Import, ast.ImportFrom)) and n is not fn]


def _rec(*args, node, name, **kwargs) -> dict:
    """purpose: 'Build one warn record for a local-import line.'"""
    return {"level": "warn", "line": node.lineno, "scope": "def",
            "technical_message": f"local import in {name}() — move to module top"}
