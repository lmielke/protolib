"""
script_path: src/protolib/test/core/gov/helpers/c36.py
paths: ["**/*.py"]
purpose: "Helper: c36 — inline literal max entries inside a def."
description: |-
  AST-based scan for Assign / AnnAssign nodes whose value is a Dict /
  List / Set / Tuple literal. Emits 'warn' when the literal has more
  than max_entries items AND the assignment lives inside a def. Module-
  level constants are intentionally permitted — this is a code-shape
  rule, not a config-discipline rule.
update_rules: "Do not modify in clones. Threshold arrives via **params from settings.yml."
"""
import ast

_LITERALS = (ast.Dict, ast.List, ast.Set, ast.Tuple)
_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def run(*args, tree, max_entries, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    out = []
    _scan(node=tree, in_def=False, out=out, max_entries=max_entries)
    return out


def _scan(*args, node, in_def, out, max_entries, **kwargs):
    """purpose: 'Recurse AST; emit when inside a def; descend into nested defs.'"""
    if in_def: _emit(node=node, out=out, max_entries=max_entries)
    deeper = in_def or isinstance(node, _DEFS)
    for child in ast.iter_child_nodes(node):
        _scan(node=child, in_def=deeper, out=out, max_entries=max_entries)


def _emit(*args, node, out, max_entries, **kwargs):
    """purpose: 'Append warn record for Assign/AnnAssign with large literal value.'"""
    if not isinstance(node, (ast.Assign, ast.AnnAssign)): return
    if not isinstance(node.value, _LITERALS): return
    n = len(node.value.keys) if isinstance(node.value, ast.Dict) else len(node.value.elts)
    if n <= max_entries: return
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in targets: _add(t=t, lineno=node.lineno, n=n, out=out, max_entries=max_entries)


def _add(*args, t, lineno, n, out, max_entries, **kwargs):
    """purpose: 'Append record only when target is a plain Name node.'"""
    if not isinstance(t, ast.Name): return
    msg = f"'{t.id}' has {n} entries (>{max_entries}) — consider settings/yaml"
    out.append({"line": lineno, "scope": "def", "level": "warn",
                "technical_message": msg})
