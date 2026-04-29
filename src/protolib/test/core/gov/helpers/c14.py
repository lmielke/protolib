"""
script_path: src/protolib/test/core/gov/helpers/c14.py
paths: ["**/*.py"]
purpose: "Helper: c14 — elif-chain length per def."
description: |-
  Walks every FunctionDef; finds the longest elif chain in its body.
  Emits 'warn' when the chain length exceeds max_elif. Long elif chains
  resist exhaustive testing — prefer dispatch dicts.
update_rules: "Do not modify in clones. Threshold arrives via **params from settings.yml."
"""
import ast

_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def run(*args, tree, max_elif, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    out = []
    for node in [n for n in ast.walk(tree) if isinstance(n, _DEFS)]:
        if rec := _check(node=node, max_elif=max_elif): out.append(rec)
    return out


def _check(*args, node, max_elif, **kwargs) -> dict:
    """purpose: 'Record if def contains an elif chain longer than max_elif.'"""
    chains = (_chain_len(if_node=s) for s in ast.walk(node) if isinstance(s, ast.If))
    n = max(chains, default=0)
    if n <= max_elif: return {}
    msg = f"{node.name}() has {n} elif branches (>{max_elif})"
    return {"line": node.lineno, "scope": "def", "level": "warn", "technical_message": msg}


def _chain_len(*args, if_node, **kwargs) -> int:
    """purpose: 'Count chained elif branches starting from this If node.'"""
    n, cur = 0, if_node
    while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
        n += 1
        cur = cur.orelse[0]
    return n
