"""
script_path: src/protolib/test/core/gov/helpers/c90_3.py
paths: ["**/*.py"]
purpose: "Helper: c90_3 — c_dorph. Orphan governance_exceptions (meta-rule)."
description: |-
  Meta helper. Runs in pass 2 of base._collect with file_records. For each
  docstring-bearing node (module/class/def) reads governance_exceptions
  and checks that every (code, technical_message) entry actually
  suppresses a record at the same scope. Entries with no matching record
  are reported as 'orphan' errors. Cannot be suppressed.
update_rules: "Do not modify in clones. Meta-helper; uses file_records."
"""
import ast

import yaml

_KIND = "meta"


def run(*args, tree, file_records, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    return [r for node, scope, line in _doc_nodes(tree=tree)
            for r in _check_node(node=node, scope=scope, line=line, recs=file_records)]


def _doc_nodes(*args, tree, **kwargs):
    """purpose: 'Yield (node, scope, line) for module / class / def nodes.'"""
    yield tree, 'module', 1
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class', n.lineno
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield n, 'def', n.lineno


def _check_node(*args, node, scope, line, recs, **kwargs) -> list:
    """purpose: 'Return orphan records for one node.'"""
    return [_rec(scope=scope, line=line, ec=ec)
            for ec, _et in _exc_pairs(node=node)
            if not _matches(recs=recs, ec=ec, scope=scope, node=node)]


def _exc_pairs(*args, node, **kwargs) -> list:
    """purpose: 'Yield (code, tech) pairs from governance_exceptions list.'"""
    ds = ast.get_docstring(node)
    if not ds: return []
    try: meta = yaml.safe_load(ds) or {}
    except yaml.YAMLError: return []
    excs = meta.get('governance_exceptions') or []
    return [list(e.items())[0] for e in excs if isinstance(e, dict) and len(e) == 1]


def _matches(*args, recs, ec, scope, node, **kwargs) -> bool:
    """purpose: 'True when code ec fired at this scope inside this node\\'s line range.'"""
    lo = getattr(node, 'lineno', 1)
    hi = getattr(node, 'end_lineno', 10**9)
    return any(r.get("scope") == scope and lo <= (r.get("line") or 0) <= hi
               for r in recs.get(ec, []))


def _rec(*args, scope, line, ec, **kwargs) -> dict:
    """purpose: 'Build one orphan-exception error record with fix hint.'"""
    msg = (f"stale governance_exception {ec!r} at {scope} scope — "
           f"no {ec} finding fires here; remove this entry or move it to the "
           f"docstring of the node where {ec} actually fires")
    return {"level": "error", "line": line, "scope": scope, "technical_message": msg}
