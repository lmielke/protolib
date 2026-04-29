"""
script_path: src/protolib/test/core/gov/helpers/c90_2.py
purpose: "Helper: c90_2 — dscope. Validate exception code is allowed at its scope."
description: |-
  For each docstring-bearing node, reads governance_exceptions and checks
  every entry's code against scope_allowed[scope]. Codes not allowed at
  the declaration scope produce an error. Cannot be suppressed.
update_rules: "Do not modify in clones. Helper contract: no sts import; everything via params."
"""
import ast

import yaml


def _meta(node, *args, **kwargs) -> dict:
    """purpose: 'Parse docstring front-matter; {} on missing or non-dict.'"""
    ds = ast.get_docstring(node, clean=False)
    if ds is None: return {}
    try: m = yaml.safe_load(ds.split("\n\n", 1)[0])
    except yaml.YAMLError: return {}
    return m if isinstance(m, dict) else {}


def _docstring_nodes(tree, *args, **kwargs):
    """purpose: 'Yield (node, scope, line) for module/class/def nodes.'"""
    yield tree, 'module', 1
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class', n.lineno
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def', n.lineno


def _entry_code(entry, *args, **kwargs):
    """purpose: 'Code from one governance_exceptions entry; None if malformed.'"""
    if not isinstance(entry, dict) or len(entry) != 1: return None
    (ec, _), = entry.items()
    return ec


def _node_records(node, scope, line, *args, scope_allowed, **kwargs) -> list:
    """purpose: 'Errors for exception codes not allowed at this scope.'"""
    excs = _meta(node).get('governance_exceptions') or []
    if not isinstance(excs, list): return []
    allowed = set(scope_allowed.get(scope, []))
    bad = [c for c in (_entry_code(e) for e in excs) if c and c not in allowed]
    return [{"line": line, "scope": scope, "level": "error",
             "technical_message": f"[{scope}] {c} not allowed at {scope}"} for c in bad]


def run(*args, tree=None, scope_allowed=None, **kwargs) -> list[dict]:
    """purpose: 'Validate exception codes against scope_allowed map.'"""
    if tree is None: return []
    out = []
    for node, scope, line in _docstring_nodes(tree):
        out += _node_records(node, scope, line, scope_allowed=scope_allowed)
    return out
