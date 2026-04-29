"""
script_path: src/protolib/test/core/gov/helpers/c90_1.py
purpose: "Helper: c90_1 — dfmt. Validate docstring front-matter format."
description: |-
  Walks every module/class/def docstring-bearing node. Parses YAML
  front-matter (head before first blank line). Emits errors for:
  module-level missing docstring; non-mapping front-matter; missing
  required keys; unknown keys; module script_path mismatch.
update_rules: "Do not modify in clones. Helper contract: no sts import; everything via params."
"""
import ast
import os

import yaml


def _rec(*args, line: int, scope: str, technical: str, **kwargs) -> dict:
    """purpose: 'Build a single error-level violation record.'"""
    return {"line": line, "scope": scope, "level": "error", "technical_message": technical}


def _meta(node, *args, **kwargs) -> tuple:
    """purpose: 'Return (state, meta) where state is missing|bad|ok.'"""
    ds = ast.get_docstring(node, clean=False)
    if ds is None: return ('missing', {})
    try: m = yaml.safe_load(ds.split("\n\n", 1)[0])
    except yaml.YAMLError: return ('bad', {})
    return ('ok', m) if isinstance(m, dict) and m else ('bad', {})


def _docstring_nodes(tree, *args, **kwargs):
    """purpose: 'Yield (node, scope, line) for module/class/def nodes.'"""
    yield tree, 'module', 1
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class', n.lineno
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def', n.lineno


def _missing(scope, line, *args, **kwargs) -> list:
    """purpose: 'Module missing docstring is an error; class/def tolerated.'"""
    if scope != 'module': return []
    return [_rec(line=line, scope=scope, technical=f"[{scope}] missing docstring")]


def _key_records(meta, scope, line, *args, required, allowed, **kwargs) -> list:
    """purpose: 'Records for missing required keys plus unknown keys.'"""
    out = [_rec(line=line, scope=scope, technical=f"[{scope}] missing {k}")
           for k in required[scope] if k not in meta]
    return out + [_rec(line=line, scope=scope, technical=f"[{scope}] unknown key {k!r}")
                  for k in meta if k not in allowed[scope]]


def _check_script_path(meta, rel, line, *args, pkg, **kwargs) -> list:
    """purpose: 'Module script_path must match src/<pkg>/<rel>.'"""
    got = meta.get('script_path')
    if got is None: return []
    want = f"src/{pkg}/{rel.replace(os.sep, '/')}"
    return [] if got == want \
        else [_rec(line=line, scope='module', technical=f"script_path {got!r} != {want!r}")]


def _check_node(node, scope, line, *args, rel, required, allowed, pkg, **kwargs) -> list:
    """purpose: 'Run all dfmt checks for one docstring node.'"""
    state, meta = _meta(node)
    if state == 'missing': return _missing(scope, line)
    if state == 'bad':
        return [_rec(line=line, scope=scope, technical=f"[{scope}] bad front-matter")]
    keys = _key_records(meta, scope, line, required=required, allowed=allowed)
    path = _check_script_path(meta, rel, line, pkg=pkg) if scope == 'module' else []
    return keys + path


def run(*args, tree=None, rel=None, required=None, allowed=None, pkg=None, **kwargs) -> list[dict]:
    """purpose: 'Validate docstring front-matter; emit error per missing/unknown/path issue.'"""
    if tree is None: return []
    out = []
    for node, scope, line in _docstring_nodes(tree):
        out += _check_node(node, scope, line, rel=rel,
                           required=required, allowed=allowed, pkg=pkg)
    return out
