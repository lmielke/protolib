"""
script_path: src/protolib/test/core/gov/base.py
purpose: "Shared discovery + AST utilities + master orchestration."
description: |-
  Pure utilities — no rule logic. discover_sources walks SRC_ROOT under the
  configured filters; read_source returns (lines, ast_tree); parse_defs and
  _code_lines power the legacy line-based helpers (c1, c11). run_check
  registers a check; run_master walks sources, dispatches every RESULTS
  entry, writes the per-file log.
update_rules: "Do not modify in clones. Mechanism only — never rule data."
governance_exceptions:
  - c1: "discover_sources walks os.walk; flattening obscures intent"
"""
import ast
import os
import re

import yaml

import protolib.core.settings as core_sts
from protolib.test.core.gov import settings as sts

SRC_ROOT = core_sts.package_dir
REPO_ROOT = os.path.dirname(os.path.dirname(SRC_ROOT))
SCAN_SKIP_DIRS = set(sts.checks['scan']['skip_dirs'])
SKIP_FILES = set(sts.checks['scan']['skip_files'])
_MASTER_BLOCK_RX = re.compile(r'^## (c\w+)\s*\n"""\n(.*?)\n"""', re.M | re.S)


def discover_sources(*args, **kwargs) -> list:
    """purpose: 'Return sorted relative paths of source files under SRC_ROOT.'"""
    paths = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SCAN_SKIP_DIRS and not x.startswith("__"))
        for f in sorted(files):
            if not f.endswith(".py") or f in SKIP_FILES: continue
            if f.startswith("test_"): continue
            paths.append(os.path.relpath(os.path.join(root, f), SRC_ROOT))
    return paths


def read_source(*args, path: str, **kwargs) -> tuple:
    """purpose: 'Read a file path; return (lines, ast.Module). Raises SyntaxError on bad parse.'"""
    text = open(path).read()
    return text.splitlines(keepends=False), ast.parse(text)


def find_body_end(lines, start, indent, *args, **kwargs) -> int:
    """purpose: 'Find line index where a def body ends (dedent back to parent).'"""
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip(): continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent and not line.lstrip().startswith(('#', ')', ']', '}')):
            return i
    return len(lines)


def parse_defs(lines, *args, **kwargs) -> list:
    """purpose: 'Extract (start, indent, name, body_lines) for each def in lines.'"""
    defs = [(i, len(m.group(1)), m.group(2))
            for i, line in enumerate(lines)
            if (m := re.match(r'^(\s*)def (\w+)\(', line))]
    result = []
    for start, indent, name in defs:
        end = find_body_end(lines, start, indent)
        body = [l for l in lines[start + 1:end] if l.strip()]
        result.append((start, indent, name, body))
    return result


def run_check(helper, *args, **params) -> dict:
    """purpose: 'Register a check from its helper module; return {code: meta_dict}.'"""
    code = helper.__name__.rsplit(".", 1)[-1]
    return {code: {"fn": helper.run, "params": params, "module": helper}}


def run_master(*args, results: dict, master_path: str, log_path: str, **kwargs) -> int:
    """purpose: 'Walk sources, dispatch RESULTS, write log; return error count.'"""
    from protolib.test.core.gov.log import GovernanceLog
    meta = parse_master_meta(master_path=master_path)
    log = GovernanceLog(log_path=log_path)
    errs = sum(_scan(rel=r, results=results, meta=meta, log=log) for r in discover_sources())
    log.save()
    return errs


def parse_master_meta(*args, master_path: str, **kwargs) -> dict:
    """purpose: 'Parse `## cN` blocks from master src; return {code: meta_dict}.'"""
    src = open(master_path).read()
    return {m.group(1): (yaml.safe_load(m.group(2)) or {}) for m in _MASTER_BLOCK_RX.finditer(src)}


def _scan(*args, rel: str, results: dict, meta: dict, log, **kwargs) -> int:
    """purpose: 'Scan one file; record warnings/errors; return error count.'"""
    try: lines, tree = read_source(path=os.path.join(SRC_ROOT, rel))
    except SyntaxError: return 0
    header = _extract_header(tree=tree)
    warns, errs = _collect(rel=rel, lines=lines, tree=tree, results=results, meta=meta)
    log.record(rel=rel, header=header, warnings=warns, errors=errs)
    return len(errs)


def _extract_header(*args, tree, **kwargs) -> dict:
    """purpose: 'Parse module docstring front-matter into a dict; {} on parse failure.'"""
    ds = ast.get_docstring(tree)
    if not ds: return {}
    try: return yaml.safe_load(ds) or {}
    except yaml.YAMLError: return {}


def _collect(*args, rel: str, lines: list, tree, results: dict, meta: dict, **kwargs) -> tuple:
    """purpose: 'Two-pass: data helpers populate file_records; meta helpers consume.'"""
    file_records: dict = {}
    w1, e1 = _dispatch(rel=rel, lines=lines, tree=tree, results=results, meta=meta,
                       kind="data", file_records=file_records)
    w2, e2 = _dispatch(rel=rel, lines=lines, tree=tree, results=results, meta=meta,
                       kind="meta", file_records=file_records)
    return w1 + w2, e1 + e2


def node_excs(*args, node, **kwargs) -> set:
    """purpose: 'Exception codes declared in this node\\'s docstring governance_exceptions.'"""
    ds = ast.get_docstring(node)
    if not ds: return set()
    try: meta = yaml.safe_load(ds) or {}
    except yaml.YAMLError: return set()
    excs = meta.get('governance_exceptions') or []
    return {list(e.keys())[0] for e in excs if isinstance(e, dict) and len(e) == 1}


def enclosing_node(*args, tree, line: int, scope: str, **kwargs):
    """purpose: 'Return smallest module/class/def AST node enclosing line at given scope.'"""
    if scope == 'module': return tree
    types = {'class': (ast.ClassDef,),
             'def': (ast.FunctionDef, ast.AsyncFunctionDef)}.get(scope, ())
    cands = [n for n in ast.walk(tree) if isinstance(n, types)
             and n.lineno <= line <= getattr(n, 'end_lineno', n.lineno)]
    return min(cands, key=lambda n: getattr(n, 'end_lineno', n.lineno) - n.lineno) if cands else None


def _suppressed(*args, tree, raw, code, **kwargs) -> bool:
    """purpose: 'True iff code is declared in the enclosing node\\'s docstring exceptions.'"""
    scope, line = raw.get("scope"), raw.get("line")
    if scope not in ("module", "class", "def"): return False
    node = enclosing_node(tree=tree, line=line or 1, scope=scope)
    return node is not None and code in node_excs(node=node)


def _dispatch(*args, rel, lines, tree, results, meta, kind, file_records, **kwargs) -> tuple:
    """purpose: 'Run helpers; populate file_records; suppress per-scope excs from enclosing node.'"""
    warns, errs = [], []
    for code, entry in results.items():
        if getattr(entry["module"], "_KIND", "data") != kind: continue
        for r in entry["fn"](lines=lines, tree=tree, rel=rel,
                             file_records=file_records, **entry["params"]):
            if kind == "data": file_records.setdefault(code, []).append(r)
            if _suppressed(tree=tree, raw=r, code=code): continue
            rec = _build_record(code=code, raw=r, meta=meta.get(code, {}), module=entry["module"])
            (errs if r.get("level") == "error" else warns).append(rec)
    return warns, errs


def _build_record(*args, code: str, raw: dict, meta: dict, module, **kwargs) -> dict:
    """purpose: 'Enrich helper-emitted record with name/rule/helper from master meta.'"""
    return {"name": meta.get("name", code), "rule": meta.get("rule", ""),
            "helper": os.path.relpath(module.__file__, REPO_ROOT),
            "line": raw.get("line"), "scope": raw.get("scope"),
            "technical_message": raw.get("technical_message"),
            "display_message": meta.get("purpose", "")}


def _code_lines(body, *args, **kwargs) -> list:
    """purpose: 'Filter body to executable code — drop comments and triple-quoted strings.'"""
    out, in_triple = [], None
    for line in body:
        s = line.strip()
        if in_triple:
            if in_triple in s: in_triple = None
            continue
        if s.startswith("#"): continue
        if s.startswith(('"""', "\'\'\'")):
            q = s[:3]
            if q in s[3:]: continue
            in_triple = q
            continue
        out.append(line)
    return out
