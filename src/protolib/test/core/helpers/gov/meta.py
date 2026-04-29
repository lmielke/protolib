"""
script_path: src/protolib/test/core/helpers/gov/meta.py
purpose: "[TO_DELETE] Meta-rule checks operating on docstring front-matter (c_dfmt, c_dscope, c_dorph)."
description: |-
  Consumes Docstrings.from_node from helpers/docstrings to read YAML front-matter.
  Exposes META_CHECKS dict keyed by meta-code; also exposes _filter_docstring_excs
  used by per-rule checks to honour in-scope governance_exceptions suppressions.
update_rules: "Do not modify in clones."
"""
import os, re, ast
import protolib.core.settings as sts
from protolib.helpers.collections import load_docstring_schema
from protolib.helpers.docstrings import Docstring, Docstrings

PKG = sts.package_name
_DS = load_docstring_schema()
_DOC_ALLOWED = {s: v['allowed'] for s, v in _DS.items()}
_DOC_REQUIRED = {s: v['required'] for s, v in _DS.items()}
_RE_LINE_PREFIX = re.compile(r'^line (\d+):\s*(.*)$')


def _parse_legacy(msg, *args, **kwargs) -> tuple:
    """purpose: Split a legacy check string into (line, technical_message)."""
    m = _RE_LINE_PREFIX.match(msg)
    return (int(m.group(1)), m.group(2)) if m else (0, msg)


def _rec(*args, line, scope, technical, display="", level, **kwargs) -> dict:
    """purpose: Governance record. level is 'warn' or 'error'."""
    return {"line": line, "scope": scope, "level": level,
            "technical_message": technical, "display_message": display}


def _parse_docstring_front_matter(ds, *args, **kwargs) -> tuple:
    """purpose: Split docstring on first blank line; parse head as YAML. Returns (meta, body)."""
    d = Docstring(ds)
    return ((d.meta, d.body) if isinstance(d.meta, dict) else ({}, d.body or ""))


def _enclosing_scopes(tree, line, *args, **kwargs) -> list:
    """purpose: AST nodes enclosing `line`, narrowest first, Module last."""
    inner = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
             and n.lineno <= line <= getattr(n, 'end_lineno', n.lineno)]
    inner.sort(key=lambda n: -n.lineno)
    return inner + [tree]


def _docstring_nodes(tree, *args, **kwargs):
    """purpose: Yield (node, scope, lineno) for every docstring-bearing node."""
    yield tree, 'module', 1
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class', n.lineno
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def', n.lineno


def _docstring_exceptions(node, *args, **kwargs) -> list:
    """purpose: governance_exceptions list from front-matter; raise on non-list."""
    excs = Docstrings.from_node(node).get(key="governance_exceptions")
    if excs is None: return []
    if not isinstance(excs, list):
        raise ValueError(f"governance_exceptions must be a list, got {type(excs).__name__}")
    return excs


def _docstring_excs_safe(node, *args, **kwargs) -> list:
    """purpose: governance_exceptions list; silent [] on malformed (c_dfmt reports)."""
    excs = Docstrings.from_node(node).get(key="governance_exceptions")
    return excs if isinstance(excs, list) else []


def _match_exception(check, tech, excs, *args, rules, **kwargs) -> bool:
    """purpose: True if excs matches (check, tech). Raises on mandatory-rule target."""
    for entry in excs:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise ValueError(f"malformed exception entry: {entry!r}")
        (ec, et), = entry.items()
        if ec in rules and not rules[ec]['exceptions_apply']:
            raise AssertionError(
                f"rule {ec} is mandatory-fix and cannot be suppressed via docstring")
        if ec == check and et == tech: return True
    return False


def _filter_docstring_excs(msgs, *args, code, tree, rules, **kwargs) -> list:
    """purpose: Drop msgs whose (line, tech) is suppressed by a docstring exception in scope."""
    kept = []
    for msg in msgs:
        line, tech = _parse_legacy(msg)
        excs = [e for n in _enclosing_scopes(tree, line) for e in _docstring_exceptions(n)]
        if _match_exception(code, tech, excs, rules=rules): continue
        kept.append(msg)
    return kept


def _c_dfmt_check(tree, rel, *args, rules, **kwargs) -> tuple:
    """purpose: c_dfmt — every docstring conforms to template. Returns (warns, errs)."""
    if tree is None: return [], []
    errs = []
    for node, scope, line in _docstring_nodes(tree):
        ds = ast.get_docstring(node, clean=False)
        if ds is None:
            if scope == 'module': errs.append(f"line {line}: [module] missing docstring")
            continue
        errs += _dfmt_validate(ds, scope, rel, line, rules)
    return [], errs


def _dfmt_validate(ds, scope, rel, line, rules, *args, **kwargs) -> list:
    """purpose: Run all docstring-shape checks; return list of issues."""
    meta = Docstring(ds).meta
    if not isinstance(meta, dict) or not meta:
        return [f"line {line}: [{scope}] no front-matter mapping"]
    issues = [f"line {line}: [{scope}] missing {k}" for k in _DOC_REQUIRED[scope] if k not in meta]
    issues += [f"line {line}: [{scope}] unexpected key {k!r}" for k in meta if k not in _DOC_ALLOWED[scope]]
    if scope == 'module': issues += _dfmt_script_path(meta, rel, line)
    issues += _dfmt_excs_shape(meta, scope, line, rules)
    return issues


def _dfmt_script_path(meta, rel, line, *args, **kwargs) -> list:
    """purpose: Validate script_path meta matches the file's source-relative path."""
    got = meta.get('script_path')
    if got is None: return []
    want = f"src/{PKG}/{rel.replace(os.sep, '/')}"
    return [] if got == want else [f"line {line}: [module] script_path {got!r} != {want!r}"]


def _dfmt_excs_shape(meta, scope, line, rules, *args, **kwargs) -> list:
    """purpose: Validate governance_exceptions is a list of single-key dicts over soft rules."""
    excs = meta.get('governance_exceptions')
    if excs is None: return []
    if not isinstance(excs, list):
        return [f"line {line}: [{scope}] governance_exceptions must be a list"]
    out = []
    for e in excs:
        if not isinstance(e, dict) or len(e) != 1:
            out.append(f"line {line}: [{scope}] malformed exception: {e!r}")
            continue
        (ec, _), = e.items()
        if ec in rules and not rules[ec]['exceptions_apply']:
            out.append(f"line {line}: [{scope}] cannot suppress mandatory rule {ec}")
    return out


def _c_dscope_check(tree, file_records, *args, **kwargs) -> tuple:
    """purpose: c_dscope — exception's scope must match a record's scope when record exists."""
    if tree is None: return [], []
    errs = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            errs += _dscope_entry(e, scope, line, file_records)
    return [], errs


def _dscope_entry(entry, scope, line, file_records, *args, **kwargs) -> list:
    """purpose: Validate one exception entry against existing file records."""
    if not isinstance(entry, dict) or len(entry) != 1: return []
    (ec, et), = entry.items()
    matching = [r for r in file_records.get(ec, []) if r['technical_message'] == et]
    if matching and not any(r['scope'] == scope for r in matching):
        actual = sorted({r['scope'] for r in matching})
        return [f"line {line}: [{scope}] {ec}:{et!r} exists at {actual}, not {scope}"]
    return []


def _c_dorph_check(tree, file_records, *args, rules, **kwargs) -> tuple:
    """purpose: c_dorph — exception on soft rule must suppress a record in same scope."""
    if tree is None: return [], []
    errs = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            errs += _dorph_entry(e, scope, line, file_records, rules)
    return [], errs


def _dorph_entry(entry, scope, line, file_records, rules, *args, **kwargs) -> list:
    """purpose: Validate one exception entry matches a record of same code+scope."""
    if not isinstance(entry, dict) or len(entry) != 1: return []
    (ec, et), = entry.items()
    if ec not in rules:
        return [f"line {line}: [{scope}] exception against unknown rule {ec}"]
    if not rules[ec]['exceptions_apply']:
        return [f"line {line}: [{scope}] exception against hard rule {ec} — cannot be suppressed"]
    recs = file_records.get(ec, [])
    if not any(r['technical_message'] == et and r['scope'] == scope for r in recs):
        return [f"line {line}: [{scope}] orphan {ec}:{et!r} matches no record"]
    return []


META_CHECKS = {
    'c_dfmt':   {'fn': _c_dfmt_check,   'kind': 'tree',    'exceptions_apply': False,
                 'why': "Docstrings are the source of governance metadata; malformed docstrings corrupt the rule engine.",
                 'fix': "Use canonical front-matter: script_path/purpose/description/update_rules/governance_exceptions."},
    'c_dscope': {'fn': _c_dscope_check, 'kind': 'records', 'exceptions_apply': False,
                 'why': "An exception declared in the wrong scope silently suppresses nothing or the wrong record.",
                 'fix': "Move the governance_exceptions entry to the docstring of the scope where the violation lives."},
    'c_dorph':  {'fn': _c_dorph_check,  'kind': 'records', 'exceptions_apply': False,
                 'why': "Orphan exceptions indicate drift — the suppressed violation no longer exists.",
                 'fix': "Remove the governance_exceptions entry; the underlying code no longer trips the rule."},
}
