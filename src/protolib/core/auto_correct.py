"""
script_path: src/protolib/core/auto_correct.py

Auto-corrects governance violations that can be safely automated.
Run manually after test_governance.py reports fixable violations.
Each corrector matches a test in test_governance.py by check code (c24, c26, c28).

Usage: uv run python -m protolib.core.auto_correct
"""
import os, re, ast, yaml
import protolib.core.settings as sts

SRC_ROOT = sts.package_dir
SCAN_SKIP_DIRS = {"test", "resources", "__pycache__"}
SKIP_FILES = {"__init__.py", "__main__.py"}

_DOC_ALLOWED = {
    'module': {'script_path', 'purpose', 'description',
               'update_rules', 'governance_exceptions'},
    'class':  {'purpose', 'description', 'governance_exceptions'},
    'def':    {'purpose', 'description', 'governance_exceptions'},
}
_DOC_REQUIRED = {'module': {'script_path', 'purpose'},
                 'class':  {'purpose'},
                 'def':    {'purpose'}}
_DOC_ORDER = ['script_path', 'purpose', 'description',
              'update_rules', 'governance_exceptions']


def discover_sources(*args, **kwargs):
    paths = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SCAN_SKIP_DIRS and not x.startswith("__"))
        for f in sorted(files):
            if not f.endswith(".py") or f in SKIP_FILES: continue
            paths.append(os.path.relpath(os.path.join(root, f), SRC_ROOT))
    return paths


def _rewrite(path, fixed, *args, rel='', **kwargs):
    with open(path, 'w') as f:
        f.write(fixed)
    print(f"  fixed: {rel or path}")


def correct_c24_def_spacing(*args, path: str, rel: str, **kwargs) -> bool:
    """Normalize blank lines: exactly 1 before def, 2 before class."""
    with open(path) as f:
        text = f.read()
    out = re.sub(r'\n{3,}(def )', r'\n\n\1', text)
    out = re.sub(r'\n{4,}(class )', r'\n\n\n\1', out)
    if out == text: return False
    _rewrite(path, out, rel=rel)
    return True


def correct_c26_relative_imports(*args, path: str, rel: str, **kwargs) -> bool:
    """Replace relative imports (from . import x) with absolute imports."""
    pkg = sts.package_name
    parent = '.'.join(rel.replace(os.sep, '.').removesuffix('.py').split('.')[:-1])
    with open(path) as f: text = f.read()
    sub = lambda m: f"from {pkg}.{parent}.{m.group(1)} import {m.group(1)}"
    out = re.sub(r'from \. import (\w+)', sub, text)
    if out == text: return False
    _rewrite(path, out, rel=rel)
    return True


def correct_c28_bare_except(*args, path: str, rel: str, **kwargs) -> bool:
    """Replace bare 'except:' with 'except Exception:'."""
    with open(path) as f:
        text = f.read()
    out = re.sub(r'\bexcept\s*:', 'except Exception:', text)
    if out == text: return False
    _rewrite(path, out, rel=rel)
    return True


# ── c_dfmt: docstring front-matter ────────────────────────────────────────────

def _parse_front_matter(ds, *args, **kwargs) -> tuple:
    """Split on first blank; parse head as YAML. Returns (meta or None, body)."""
    if not ds: return None, ""
    parts = ds.split("\n\n", 1)
    head, body = parts[0], (parts[1] if len(parts) > 1 else "")
    try: meta = yaml.safe_load(head)
    except yaml.YAMLError: return None, ""
    return (meta if isinstance(meta, dict) else None), (body if isinstance(meta, dict) else "")


def _placeholder(key, rel, *args, **kwargs) -> str:
    """Placeholder value for a missing required key."""
    if key == 'script_path': return f"src/{sts.package_name}/{rel.replace(os.sep, '/')}"
    return f"TODO: describe {key}"


def _fix_meta(meta, scope, rel, *args, **kwargs) -> dict:
    """Move unknowns to description, fix script_path, add placeholders for required keys."""
    unknowns = {k: v for k, v in (meta or {}).items() if k not in _DOC_ALLOWED[scope]}
    kept = {k: v for k, v in (meta or {}).items() if k in _DOC_ALLOWED[scope]}
    if unknowns:
        appended = "\n".join(f"{k}: {v}" for k, v in unknowns.items())
        existing = kept.get('description', '')
        kept['description'] = (existing + "\n" + appended).strip() if existing else appended
    if scope == 'module':
        kept['script_path'] = _placeholder('script_path', rel)
    for req in _DOC_REQUIRED[scope]:
        kept.setdefault(req, _placeholder(req, rel))
    return {k: kept[k] for k in _DOC_ORDER if k in kept}


def _render_meta(meta, *args, **kwargs) -> str:
    """Emit front-matter lines. Fold string values longer than 80 chars."""
    out = []
    for k, v in meta.items():
        style = '>' if isinstance(v, str) and len(v) > 80 else None
        chunk = yaml.safe_dump({k: v}, default_flow_style=False,
                               default_style=style, width=80,
                               sort_keys=False, allow_unicode=True).rstrip()
        out.append(chunk)
    return "\n".join(out)


def _needs_fix(meta, scope, rel, *args, **kwargs) -> bool:
    """True if the docstring front-matter fails c_dfmt."""
    if meta is None: return True
    keys = set(meta.keys())
    if keys - _DOC_ALLOWED[scope]: return True
    if _DOC_REQUIRED[scope] - keys: return True
    want = f"src/{sts.package_name}/{rel.replace(os.sep, '/')}"
    return scope == 'module' and meta.get('script_path') != want


def _docstring_expr(node, *args, **kwargs):
    """Return the Expr wrapping the node's docstring, or None."""
    if not getattr(node, 'body', None): return None
    first = node.body[0]
    if not isinstance(first, ast.Expr): return None
    v = first.value
    return first if (isinstance(v, ast.Constant) and isinstance(v.value, str)) else None


def _iter_scopes(tree, *args, **kwargs):
    """Yield (node, scope) for module and every class/def."""
    yield tree, 'module'
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class'
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def'


def _byte_offset(src_bytes, lineno, col, *args, **kwargs) -> int:
    """Convert (1-based lineno, byte col) to absolute byte offset."""
    pos, line = 0, 1
    while line < lineno and pos < len(src_bytes):
        if src_bytes[pos:pos+1] == b'\n': line += 1
        pos += 1
    return pos + col


def _indent_str(src_lines, lineno, *args, **kwargs) -> str:
    """Leading whitespace of the given 1-based source line."""
    line = src_lines[lineno - 1] if 0 < lineno <= len(src_lines) else ""
    return line[:len(line) - len(line.lstrip(' \t'))]


def _has_raw_prefix(src_bytes, expr, *args, **kwargs) -> bool:
    """True if the literal at expr starts with r/R prefix."""
    start = _byte_offset(src_bytes, expr.lineno, expr.col_offset)
    return src_bytes[start:start+1] in (b'r', b'R')


def _format_docstring(meta, body, indent, raw, *args, **kwargs) -> str:
    """Build a triple-quoted docstring literal with indented content."""
    front = _render_meta(meta)
    content = front + (f"\n\n{body.strip()}" if body.strip() else "")
    lines = "\n".join((indent + l) if l else l for l in content.split("\n"))
    pre = 'r' if raw else ''
    return f'{pre}"""\n{lines}\n{indent}"""'


def _dfmt_edit(expr, scope, src_bytes, src_lines, rel, *args, **kwargs):
    """Return (start, end, repl_bytes) for a docstring that needs fixing, else None."""
    meta, body = _parse_front_matter(expr.value.value)
    if not _needs_fix(meta, scope, rel): return None
    fixed = _fix_meta(meta, scope, rel)
    indent = _indent_str(src_lines, expr.lineno)
    text = _format_docstring(fixed, body, indent, _has_raw_prefix(src_bytes, expr))
    start = _byte_offset(src_bytes, expr.lineno, expr.col_offset)
    end = _byte_offset(src_bytes, expr.end_lineno, expr.end_col_offset)
    return (start, end, text.encode('utf-8'))


def _collect_dfmt_edits(tree, src_bytes, src, rel, *args, **kwargs) -> list:
    """Gather all docstring edits for the file."""
    edits, src_lines = [], src.splitlines()
    for node, scope in _iter_scopes(tree):
        expr = _docstring_expr(node)
        if not expr: continue
        ed = _dfmt_edit(expr, scope, src_bytes, src_lines, rel)
        if ed: edits.append(ed)
    return edits


def _apply_edits(src_bytes, edits, *args, **kwargs) -> bytes:
    """Apply byte-range edits bottom-up so earlier offsets stay valid."""
    out = src_bytes
    for start, end, repl in sorted(edits, key=lambda e: -e[0]):
        out = out[:start] + repl + out[end:]
    return out


def correct_c_dfmt_docstring_format(*args, path: str, rel: str, **kwargs) -> bool:
    """Rebuild malformed/incomplete docstring front-matter; preserve body."""
    with open(path, 'rb') as f: src_bytes = f.read()
    src = src_bytes.decode('utf-8')
    try: tree = ast.parse(src)
    except SyntaxError: return False
    edits = _collect_dfmt_edits(tree, src_bytes, src, rel)
    if not edits: return False
    _rewrite(path, _apply_edits(src_bytes, edits).decode('utf-8'), rel=rel)
    return True


CORRECTORS = [
    ('c24',    'def spacing',       correct_c24_def_spacing),
    ('c26',    'relative imports',  correct_c26_relative_imports),
    ('c28',    'bare except',       correct_c28_bare_except),
    ('c_dfmt', 'docstring format',  correct_c_dfmt_docstring_format),
]


def run(*args, **kwargs):
    sources = discover_sources()
    for code, label, fn in CORRECTORS:
        count = sum(fn(path=os.path.join(SRC_ROOT, r), rel=r) for r in sources)
        status = f"fixed {count} file(s)" if count else "nothing to fix"
        print(f"[{code}] {label}: {status}")


if __name__ == '__main__':
    run()
