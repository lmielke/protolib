"""
script_path: src/protolib/test/core/helpers/gov/c36.py
purpose: "[TO_DELETE] c36 — inline dict/list/set/tuple size check. Flags literals with >8 entries in a def."
description: "Large inline literals obscure config intent; promote to settings.py or yaml."
update_rules: "Do not modify in clones."
"""
import ast

_C36_SKIP_NAMES = {"__all__", "CHECKS", "PY2JSON", "_COMMON_LOCALS", "_C36_SKIP_NAMES"}
_C36_LITERALS = (ast.Dict, ast.List, ast.Set, ast.Tuple)
_C36_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _c36_inline_dict_size(lines, rel, *args, **kwargs):
    """purpose: Parse AST and flag large container literals assigned inside a function."""
    warn, err = [], []
    try: tree = ast.parse("".join(lines))
    except SyntaxError: return warn, err
    _c36_scan(tree, in_def=False, out=warn)
    return warn, err


def _c36_scan(node, *args, in_def: bool, out: list, **kwargs):
    """purpose: Recurse the AST; emit when inside a def; descend deeper into nested defs."""
    if in_def: _c36_emit(node, out=out)
    deeper = in_def or isinstance(node, _C36_DEFS)
    for child in ast.iter_child_nodes(node):
        _c36_scan(child, in_def=deeper, out=out)


def _c36_emit(node, *args, out: list, **kwargs):
    """purpose: Emit a warning for Assign/AnnAssign nodes whose value literal is large."""
    if not isinstance(node, (ast.Assign, ast.AnnAssign)): return
    if not isinstance(node.value, _C36_LITERALS): return
    n = len(node.value.keys) if isinstance(node.value, ast.Dict) else len(node.value.elts)
    if n <= 8: return
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in targets:
        if isinstance(t, ast.Name) and t.id not in _C36_SKIP_NAMES:
            out.append(f"line {node.lineno}: '{t.id}' has >8 entries — consider settings/yaml")
