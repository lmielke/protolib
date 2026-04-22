"""
script_path: src/protolib/test/core/test_governance.py

One test per governance rule. Each scans all source files and reports violations
with context (why the rule exists, how to fix it). Warnings print to stdout and
do not fail the suite. Errors fail the suite.
Auto-fixable rules note: Run auto_correct.py.
"""
import os, re, io, ast, tokenize, yaml, unittest
from datetime import datetime as dt
import protolib.core.settings as sts
from protolib.helpers.collections import load_docstring_schema

PKG = sts.package_name
SRC_ROOT = sts.package_dir
LOG_PATH = os.path.join(sts.test_dir, "governance_log.yaml")
EXCS_LOG_PATH = os.path.join(sts.test_dir, "governance_exceptions_log.yaml")
SCAN_SKIP_DIRS = {"test", "resources", "__pycache__"}
# test_*.py and testhelper.py are excluded from source scans — they live under test/.
SKIP_FILES = {"__init__.py", "__main__.py", "auto_correct.py"}
_AC = "Run: uv run python -m protolib.core.auto_correct"


_RE_LINE_PREFIX = re.compile(r'^line (\d+):\s*(.*)$')


def _parse_legacy(msg, *args, **kwargs) -> tuple:
    """Split a legacy check string into (line, technical_message)."""
    m = _RE_LINE_PREFIX.match(msg)
    return (int(m.group(1)), m.group(2)) if m else (0, msg)


def _rec(*args, line, scope, technical, display="", level, **kwargs) -> dict:
    """Governance record. level is 'warn' or 'error'."""
    return {"line": line, "scope": scope, "level": level,
            "technical_message": technical, "display_message": display}


def _compose(*args, technical, display, **kwargs) -> str:
    """Canonical print form: '(tech) - display'. Omits display if empty."""
    return f"({technical}) - {display}" if display else f"({technical})"


def _parse_docstring_front_matter(ds, *args, **kwargs) -> tuple:
    """Split docstring on first blank line; parse head as YAML. Returns (meta, body)."""
    if not ds: return {}, ""
    parts = ds.split("\n\n", 1)
    head, body = parts[0], (parts[1] if len(parts) > 1 else "")
    try: meta = yaml.safe_load(head)
    except yaml.YAMLError: return {}, ds
    return (meta, body) if isinstance(meta, dict) else ({}, ds)


def _enclosing_scopes(tree, line, *args, **kwargs) -> list:
    """AST nodes enclosing `line`, narrowest first, Module last."""
    inner = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
             and n.lineno <= line <= getattr(n, 'end_lineno', n.lineno)]
    inner.sort(key=lambda n: -n.lineno)
    return inner + [tree]


def _docstring_exceptions(node, *args, **kwargs) -> list:
    """governance_exceptions list from node's docstring front-matter ([] if none)."""
    meta, _ = _parse_docstring_front_matter(ast.get_docstring(node))
    excs = meta.get("governance_exceptions") if isinstance(meta, dict) else None
    if excs is None: return []
    if not isinstance(excs, list):
        raise ValueError(f"governance_exceptions must be a list, got {type(excs).__name__}")
    return excs


def _match_exception(check, tech, excs, *args, rules, **kwargs) -> bool:
    """True if any entry in excs matches (check, tech). Raises on mandatory-rule target."""
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
    """Drop msgs whose (line, tech) is suppressed by a docstring exception in scope."""
    kept = []
    for msg in msgs:
        line, tech = _parse_legacy(msg)
        excs = [e for n in _enclosing_scopes(tree, line) for e in _docstring_exceptions(n)]
        if _match_exception(code, tech, excs, rules=rules): continue
        kept.append(msg)
    return kept


# ── meta-rule helpers ─────────────────────────────────────────────────────────

_DS = load_docstring_schema()
_DOC_ALLOWED = {s: v['allowed'] for s, v in _DS.items()}
_DOC_REQUIRED = {s: v['required'] for s, v in _DS.items()}


def _docstring_nodes(tree, *args, **kwargs):
    """Yield (node, scope, lineno) for every docstring-bearing node."""
    yield tree, 'module', 1
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class', n.lineno
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def', n.lineno


def _docstring_excs_safe(node, *args, **kwargs) -> list:
    """governance_exceptions list; returns [] silently on malformed (c_dfmt reports)."""
    meta, _ = _parse_docstring_front_matter(ast.get_docstring(node))
    excs = meta.get("governance_exceptions") if isinstance(meta, dict) else None
    return excs if isinstance(excs, list) else []


def _c_dfmt_check(tree, rel, *args, rules, **kwargs) -> tuple:
    """c_dfmt: every docstring conforms to template. Returns (warns, errs)."""
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
    meta = _parse_docstring_front_matter(ds)[0]
    if not isinstance(meta, dict) or not meta:
        return [f"line {line}: [{scope}] no front-matter mapping"]
    issues = [f"line {line}: [{scope}] missing {k}" for k in _DOC_REQUIRED[scope] if k not in meta]
    issues += [f"line {line}: [{scope}] unexpected key {k!r}" for k in meta if k not in _DOC_ALLOWED[scope]]
    if scope == 'module': issues += _dfmt_script_path(meta, rel, line)
    issues += _dfmt_excs_shape(meta, scope, line, rules)
    return issues


def _dfmt_script_path(meta, rel, line, *args, **kwargs) -> list:
    got = meta.get('script_path')
    if got is None: return []
    want = f"src/{PKG}/{rel.replace(os.sep, '/')}"
    return [] if got == want else [f"line {line}: [module] script_path {got!r} != {want!r}"]


def _dfmt_excs_shape(meta, scope, line, rules, *args, **kwargs) -> list:
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
    """c_dscope: exception's scope must match a record's scope when record exists."""
    if tree is None: return [], []
    errs = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            errs += _dscope_entry(e, scope, line, file_records)
    return [], errs


def _dscope_entry(entry, scope, line, file_records, *args, **kwargs) -> list:
    if not isinstance(entry, dict) or len(entry) != 1: return []
    (ec, et), = entry.items()
    matching = [r for r in file_records.get(ec, []) if r['technical_message'] == et]
    if matching and not any(r['scope'] == scope for r in matching):
        actual = sorted({r['scope'] for r in matching})
        return [f"line {line}: [{scope}] {ec}:{et!r} exists at {actual}, not {scope}"]
    return []


def _c_dorph_check(tree, file_records, *args, rules, **kwargs) -> tuple:
    """c_dorph: exception on soft rule must suppress a record in same scope."""
    if tree is None: return [], []
    errs = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            errs += _dorph_entry(e, scope, line, file_records, rules)
    return [], errs


def _dorph_entry(entry, scope, line, file_records, rules, *args, **kwargs) -> list:
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


class GovernanceLog:
    """Reads and writes the mtime-based incremental scan log."""

    MTIME = int(os.path.getmtime(__file__))

    def __init__(self, *args, **kwargs):
        self.data = {}
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                self.data = yaml.safe_load(f) or {}

    def stale(self, *args, key: str, mtime: float, **kwargs) -> bool:
        entry = self.data.get(key, {})
        return int(entry.get("mtime", 0)) != int(mtime) or \
               int(entry.get("linter_mtime", 0)) != self.MTIME

    def record(self, *args, key: str, mtime: float, status: str,
               warnings: list, errors: list, **kwargs):
        self.data[key] = {
            "mtime": mtime, "linter_mtime": self.MTIME,
            "last_checked": dt.now().isoformat(timespec="seconds"),
            "status": status, "warnings": warnings, "errors": errors,
        }

    def prune(self, *args, active_keys: set, **kwargs):
        """purpose: Remove log entries for files no longer in discover_sources."""
        self.data = {k: v for k, v in self.data.items() if k in active_keys}

    def save(self, *args, **kwargs):
        chunks = [
            yaml.dump({k: v}, default_flow_style=False, sort_keys=False, indent=4).rstrip()
            for k, v in self.data.items()
        ]
        with open(LOG_PATH, "w") as f:
            f.write("\n\n".join(chunks) + "\n")


# ── exceptions log ────────────────────────────────────────────────────────────

def _collect_file_exceptions(tree, rel, file_records, *args, **kwargs) -> list:
    """Every governance_exceptions entry in `tree`, with match count from file_records."""
    if tree is None: return []
    out = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            out += _build_exc_row(e, node, scope, line, rel, file_records)
    return out


def _build_exc_row(e, node, scope, line, rel, file_records, *args, **kwargs) -> list:
    if not isinstance(e, dict) or len(e) != 1: return []
    (ec, et), = e.items()
    name = getattr(node, 'name', None) or os.path.basename(rel)
    hits = sum(1 for r in file_records.get(ec, [])
               if r['technical_message'] == et and r['scope'] == scope)
    return [{'file': rel, 'code': ec, 'scope': scope, 'line': line,
             'node': name, 'tech': et, 'matches': hits}]


def _group_exceptions(rows, *args, **kwargs) -> dict:
    by_rule = {}
    for r in rows:
        by_rule.setdefault(r['code'], []).append(
            {k: r[k] for k in ('file', 'scope', 'line', 'node', 'tech', 'matches')})
    return by_rule


def _save_exceptions_log(rows, path, *args, **kwargs):
    """Dump exceptions grouped by rule code to YAML."""
    data = {'generated_at': dt.now().isoformat(timespec='seconds'),
            'total': len(rows), 'by_rule': _group_exceptions(rows)}
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False,
                  indent=2, allow_unicode=True)


def discover_sources(*args, **kwargs) -> list:
    paths = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SCAN_SKIP_DIRS and not x.startswith("__"))
        for f in sorted(files):
            if not f.endswith(".py") or f in SKIP_FILES: continue
            if f.startswith("test_"): continue  # test_*.py: not runtime code, skipped anywhere
            paths.append(os.path.relpath(os.path.join(root, f), SRC_ROOT))
    return paths


def find_body_end(lines: list, start: int, indent: int, *args, **kwargs) -> int:
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip(): continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent and not line.lstrip().startswith(('#', ')', ']', '}')):
            return i
    return len(lines)


def parse_defs(lines: list, *args, **kwargs) -> list:
    defs = [(i, len(m.group(1)), m.group(2))
            for i, line in enumerate(lines)
            if (m := re.match(r'^(\s*)def (\w+)\(', line))]
    result = []
    for start, indent, name in defs:
        end = find_body_end(lines, start, indent)
        body = [l for l in lines[start + 1:end] if l.strip()]
        result.append((start, indent, name, body))
    return result


def _signature_text(lines, start, *args, **kwargs) -> str:
    """Join def line through matching close paren."""
    buf, depth = [], 0
    for i in range(start, len(lines)):
        buf.append(lines[i])
        depth += lines[i].count('(') - lines[i].count(')')
        if depth == 0 and buf: return ''.join(buf)
    return ''.join(buf)


# ── per-file check functions ───────────────────────────────────────────────────

def _code_lines(body, *args, **kwargs) -> list:
    """Filter body to executable code — drop comments and triple-quoted strings."""
    out, in_triple = [], None
    for line in body:
        s = line.strip()
        if in_triple:
            if in_triple in s: in_triple = None
            continue
        if s.startswith("#"): continue
        if s.startswith(('"""', "'''")):
            q = s[:3]
            if q in s[3:]: continue
            in_triple = q
            continue
        out.append(line)
    return out


def _c1_function_length(lines, rel, *args, **kwargs):
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        n = len(_code_lines(body))
        if n > 10: err.append(f"line {lineno+1}: {name}() has {n} lines (max 10)")
        elif n > 8: warn.append(f"line {lineno+1}: {name}() has {n} lines (>8)")
    return warn, err


def _c2_one_line_functions(lines, rel, *args, **kwargs):
    warn, err = [], []
    for lineno, indent, name, body in parse_defs(lines):
        if indent != 0: continue
        if (name.startswith('__') and name.endswith('__')) or name == 'main': continue
        real = [l for l in body if not l.strip().startswith("#")]
        if len(real) == 1:
            warn.append(f"line {lineno+1}: {name}() is one-line — candidate to inline")
    return warn, err


def _c3_module_length(lines, rel, *args, **kwargs):
    warn, err = [], []
    n = len(lines)
    if n > 500: err.append(f"module has {n} lines (max 500)")
    elif n > 300: warn.append(f"module has {n} lines (>300)")
    return warn, err


def _c4_kwargs_access(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.split("#")[0]
        if re.search(r'kwargs\.get\(', s) or re.search(r'kwargs\[', s):
            err.append(f"line {i+1}: kwargs accessed directly — use forwarding")
    return warn, err


def _c5_kwargs_signature(lines, rel, *args, **kwargs):
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        sig_line = _signature_text(lines, lineno)
        has_args = "*args" in sig_line
        has_kwargs = "**kwargs" in sig_line
        if has_kwargs and not has_args:
            warn.append(f"line {lineno+1}: {name}() has **kwargs but no *args on same def line")
        real = [l for l in body if l.strip() and not l.strip().startswith("#")]
        if not has_args and not has_kwargs and len(real) > 2:
            warn.append(f"line {lineno+1}: {name}() missing *args/**kwargs on def line — required by kwargs hook")
    return warn, err


def _c6_statement_semicolon(lines, rel, *args, **kwargs):
    warn, err = [], []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO("".join(lines)).readline))
    except (tokenize.TokenizeError, IndentationError):
        return warn, err
    for tok in toks:
        if tok.type == tokenize.OP and tok.string == ';':
            warn.append(f"line {tok.start[0]}: statement-joined with ';' — split to new line")
    return warn, err


def _c7_eval_exec(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.split("#")[0]
        if re.search(r'\beval\s*\(', s) or re.search(r'\bexec\s*\(', s):
            err.append(f"line {i+1}: eval/exec usage")
    return warn, err


_C8_ENUM_BASES = r'\((\w+\.)?(Enum|IntEnum|StrEnum|Flag|IntFlag)\)'


def _c8_class_presence(lines, rel, *args, **kwargs):
    warn, err = [], []
    classes = [l for l in lines if re.match(r'^class \w+', l)]
    if not classes:
        warn.append("no class definition — verify OOP intent")
        return warn, err
    has_init = any(re.match(r'\s+def (__init__|__post_init__)\(', l) for l in lines)
    all_enum = all(re.search(_C8_ENUM_BASES, c) for c in classes)
    if not has_init and not all_enum:
        warn.append("class(es) without __init__ — may be enum/constant, verify OOP intent")
    return warn, err


_C10_ALLOWED_SUBPKGS = ("app", "core", "helpers", "test")


def _c10_flat_imports(lines, rel, *args, **kwargs):
    warn, err = [], []
    pat = re.compile(rf'(?:import|from)\s+{PKG}\.(\w+)')
    for i, line in enumerate(lines):
        m = pat.search(line.split("#")[0])
        if m and m.group(1) not in _C10_ALLOWED_SUBPKGS:
            err.append(f"line {i+1}: flat import '{PKG}.{m.group(1)}' — use app/core/helpers only")
    return warn, err


def _c11_line_length(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.rstrip("\n")
        if s.strip() and not s.strip().startswith("#") and len(s) > 95:
            warn.append(f"line {i+1}: {len(s)} chars (max 95)")
    return warn, err


def _c12_class_count(lines, rel, *args, **kwargs):
    warn, err = [], []
    count = len(re.findall(r'^class \w+', "".join(lines), re.MULTILINE))
    if count > 5:
        warn.append(f"{count} classes in module (>5) — consider splitting")
    return warn, err


def _c13_class_before_function(lines, rel, *args, **kwargs):
    warn, err = [], []
    first_def = next((i for i, l in enumerate(lines) if re.match(r'^def \w+', l)), None)
    first_cls = next((i for i, l in enumerate(lines) if re.match(r'^class \w+', l)), None)
    if first_def is not None and first_cls is not None and first_def < first_cls:
        warn.append(f"line {first_def+1}: module-level function before first class")
    return warn, err


def _c14_elif_chains(lines, rel, *args, **kwargs):
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        count = sum(1 for l in body if re.match(r'\s+elif ', l))
        if count > 3:
            warn.append(f"line {lineno+1}: {name}() has {count} elif branches (>3)")
    return warn, err


_C15_SKIP = {tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
             tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}


def _c15_deep_nesting(lines, rel, *args, **kwargs):
    """Flag real block nesting depth — skip bracket-continuation lines."""
    warn, err = [], []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO("".join(lines)).readline))
    except (tokenize.TokenizeError, IndentationError):
        return warn, err
    depth, line_depth, seen = 0, 0, set()
    for tok in toks:
        if tok.type in (tokenize.NEWLINE, tokenize.NL):
            line_depth = depth
            continue
        if tok.type in _C15_SKIP: continue
        row, col = tok.start
        if row not in seen and line_depth == 0:
            seen.add(row)
            if col > 20: err.append(f"line {row}: indent {col} spaces (>20, max 5 levels)")
            elif col > 16: warn.append(f"line {row}: indent {col} spaces (>4 levels)")
        if tok.type == tokenize.OP:
            if tok.string in "([{": depth += 1
            elif tok.string in ")]}": depth -= 1
    return warn, err


def _c16_pass_only(lines, rel, *args, **kwargs):
    warn, err = [], []
    for lineno, _, name, body in parse_defs(lines):
        real = [l.strip() for l in body if l.strip() and not l.strip().startswith("#")]
        if real == ["pass"] and name != "__init__":
            warn.append(f"line {lineno+1}: {name}() is pass-only — implement or remove")
    return warn, err


def _c17_docstring(lines, rel, *args, **kwargs):
    warn, err = [], []
    non_blank = [(i, l.strip()) for i, l in enumerate(lines) if l.strip()][:5]
    if not any(l.startswith('"""') for _, l in non_blank):
        err.append("missing module docstring (triple-quote) in first 5 non-blank lines")
        return warn, err
    text = "".join(lines)
    m = re.search(r'"""(.*?)"""', text, re.DOTALL)
    if not m:
        err.append("module docstring not closed")
        return warn, err
    doc = m.group(1)
    if "script_path:" not in doc:
        err.append("module docstring missing 'script_path:' line")
    desc = re.sub(r'script_path:\s*\S+\n?', '', doc).strip()
    words, sentences = desc.split(), len(re.findall(r'[.!?][\s\n]', desc))
    if len(words) < 25 and sentences < 3:
        warn.append("module docstring too short (add ≥25 words or 3 sentences)")
    return warn, err


def _c18_test_pairing(lines, rel, *args, **kwargs):
    warn, err = [], []
    results_path = os.path.join(sts.test_dir, "test_results.yaml")
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = yaml.safe_load(f) or {}
        entry = results.get("modules", {}).get(rel.replace(os.sep, "/"), {})
        if entry.get("status") == "missing":
            err.append(f"test missing: {entry.get('test_file', '?')} (from test_results.yaml)")
    else:
        parts = rel.replace(os.sep, "/").split("/")
        test_rel = "/".join(["test"] + parts[:-1] + [f"test_{parts[-1]}"])
        if not os.path.exists(os.path.join(SRC_ROOT, test_rel.replace("/", os.sep))):
            err.append(f"no test file — create {test_rel}")
    return warn, err


def _c19_mutable_defaults(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if not re.match(r'\s*def ', line): continue
        if re.search(r'=\s*\[\]|=\s*\{\}|=\s*set\(\)', line):
            warn.append(f"line {i+1}: mutable default argument — use None instead")
    return warn, err


def _c20_name_guard(lines, rel, *args, **kwargs):
    warn, err = [], []
    if not any(re.match(r'^def main\(', l) for l in lines):
        return warn, err
    if not any(re.match(r'if __name__\s*==\s*[\'"]__main__[\'"]', l) for l in lines):
        warn.append("has main() but no if __name__ == '__main__' guard")
    return warn, err


_COMMON_LOCALS = {"self", "cls", "i", "j", "k", "x", "e", "f", "m", "n", "d", "l",
                  "result", "results", "output", "line", "lines", "path", "name",
                  "key", "value", "data", "item", "args", "kwargs", "err", "warn"}


def _c21_repeated_locals(lines, rel, *args, **kwargs):
    warn, err = [], []
    var_fns = {}
    for lineno, indent, fn_name, body in parse_defs(lines):
        body_indent = " " * (indent + 4)
        for bl in body:
            mat = re.match(rf'^{body_indent}(\w+)\s*=\s', bl)
            if not mat: continue
            vname = mat.group(1)
            if vname.startswith("_") or vname in _COMMON_LOCALS: continue
            var_fns.setdefault(vname, set()).add(fn_name)
    for vname, fns in sorted(var_fns.items()):
        if len(fns) >= 3:
            warn.append(f"'{vname}' assigned in {len(fns)} functions — consider class/pkg parameter")
    return warn, err


def _count_preceding_blanks(lines, lineno, *args, **kwargs) -> int:
    count = 0
    for i in range(lineno - 1, -1, -1):
        if not lines[i].strip(): count += 1
        else: break
    return count


def _block_top(lines, i, *args, **kwargs) -> int:
    j = i
    while j > 0 and lines[j - 1].lstrip().startswith('@'):
        j -= 1
    return j


def _c24_def_spacing(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if i == 0: continue
        stripped = line.lstrip()
        if len(line) - len(stripped) != 0: continue
        blanks = _count_preceding_blanks(lines, _block_top(lines, i))
        if re.match(r'def \w+\(', stripped) and blanks not in (0, 1):
            warn.append(f"line {i+1}: def needs 1 blank line before (has {blanks})")
        elif re.match(r'class \w+', stripped) and blanks not in (0, 2):
            warn.append(f"line {i+1}: class needs 2 blank lines before (has {blanks})")
    return warn, err


def _c25_local_imports(lines, rel, *args, **kwargs):
    warn, err = [], []
    for start, indent, name, _ in parse_defs(lines):
        end = find_body_end(lines, start, indent)
        for i in range(start + 1, end):
            stripped = lines[i].lstrip()
            if stripped.startswith("#"): continue
            if re.match(r'(import\s+|from\s+\S+\s+import\s+)', stripped):
                warn.append(f"line {i+1}: local import in {name}() — move to module top")
    return warn, err


def _c26_relative_imports(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*from\s+\.', line):
            warn.append(f"line {i+1}: relative import — use absolute")
    return warn, err


def _c27_wildcard_imports(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*from\s+\S+\s+import\s+\*', line):
            warn.append(f"line {i+1}: wildcard import — import names explicitly")
    return warn, err


def _c28_bare_except(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if re.match(r'\s*except\s*:', line):
            warn.append(f"line {i+1}: bare except — specify exception type")
    return warn, err


def _c29_hardcoded_paths(lines, rel, *args, **kwargs):
    warn, err = [], []
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        if re.search(r'["\'][A-Z]:\\|["\']/home/|["\']/tmp/', line):
            warn.append(f"line {i+1}: hardcoded path — use settings or os.path")
    return warn, err


_C30_EXEMPT = ("/apis/", "creator/", "helpers/printing.py")


def _c30_raw_print(lines, rel, *args, **kwargs):
    warn, err = [], []
    if any(p in rel for p in _C30_EXEMPT): return warn, err
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        if re.match(r'\s*print\s*\(', line):
            warn.append(f"line {i+1}: raw print() — use logprint or move to API")
            break
    return warn, err


_LOGGING_ALLOWED = {"helpers/printing.py"}


def _c32_stdlib_logging(lines, rel, *args, **kwargs):
    warn, err = [], []
    if rel in _LOGGING_ALLOWED: return warn, err
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#'): continue
        if re.match(r'from logging\b', stripped) or (
                stripped.startswith('import ') and re.search(r'\blogging\b', stripped)):
            warn.append(f"line {i+1}: import logging — use logprint from helpers/printing")
            break
    return warn, err


_STRIP_ANSI_CANONICAL = "helpers/printing.py"


def _c34_strip_ansi_redef(lines, rel, *args, **kwargs):
    warn, err = [], []
    if rel == _STRIP_ANSI_CANONICAL: return warn, err
    for i, line in enumerate(lines):
        if re.match(r'\s*def strip_ansi_codes\(', line):
            warn.append(f"line {i+1}: strip_ansi_codes redefined — import from helpers/printing")
    return warn, err


def _c35_core_imports_app(lines, rel, *args, **kwargs):
    warn, err = [], []
    if not rel.startswith("core/"): return warn, err
    pat = re.compile(rf'(?:import|from)\s+{PKG}\.app\b')
    for i, line in enumerate(lines):
        if pat.search(line.split("#")[0]):
            err.append(f"line {i+1}: core module imports from app — core must be self-contained")
            break
    return warn, err


def _c40_helpers_purity(lines, rel, *args, **kwargs):
    warn, err = [], []
    if not rel.startswith("helpers/"): return warn, err
    pat_core = re.compile(rf'(?:import|from)\s+{PKG}\.core\b')
    pat_app = re.compile(rf'(?:import|from)\s+{PKG}\.app(?!\.settings\b)\b')
    for i, line in enumerate(lines):
        stripped = line.split("#")[0]
        if pat_core.search(stripped):
            err.append(f"line {i+1}: helpers imports from core — core may be absent in clones")
        elif pat_app.search(stripped):
            err.append(f"line {i+1}: helpers imports from app (except app.settings) — purity")
    return warn, err


_C36_SKIP_NAMES = {"__all__", "CHECKS", "PY2JSON", "_COMMON_LOCALS", "_C36_SKIP_NAMES"}
_C36_LITERALS = (ast.Dict, ast.List, ast.Set, ast.Tuple)
_C36_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _c36_inline_dict_size(lines, rel, *args, **kwargs):
    """Flag large dict/list/set/tuple literals assigned inside a function."""
    warn, err = [], []
    try: tree = ast.parse("".join(lines))
    except SyntaxError: return warn, err
    _c36_scan(tree, in_def=False, out=warn)
    return warn, err


def _c36_scan(node, *args, in_def: bool, out: list, **kwargs):
    if in_def: _c36_emit(node, out=out)
    deeper = in_def or isinstance(node, _C36_DEFS)
    for child in ast.iter_child_nodes(node):
        _c36_scan(child, in_def=deeper, out=out)


def _c36_emit(node, *args, out: list, **kwargs):
    if not isinstance(node, (ast.Assign, ast.AnnAssign)): return
    if not isinstance(node.value, _C36_LITERALS): return
    n = len(node.value.keys) if isinstance(node.value, ast.Dict) else len(node.value.elts)
    if n <= 8: return
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in targets:
        if isinstance(t, ast.Name) and t.id not in _C36_SKIP_NAMES:
            out.append(f"line {node.lineno}: '{t.id}' has >8 entries — consider settings/yaml")


_BASENAME_MAP = None


def _basename_map(*args, **kwargs) -> dict:
    """Lazy basename → [rel, ...] map across all source files."""
    global _BASENAME_MAP
    if _BASENAME_MAP is None:
        m = {}
        for rel in discover_sources():
            m.setdefault(os.path.basename(rel), []).append(rel)
        _BASENAME_MAP = m
    return _BASENAME_MAP


def _c41_filename_collision(lines, rel, *args, **kwargs):
    """Flag .py basenames that appear at >1 source location."""
    others = _basename_map().get(os.path.basename(rel), [])
    if len(others) <= 1: return [], []
    return [], [f"duplicate basename at {', '.join(others)}"]


# ── package-level checks ───────────────────────────────────────────────────────

_MOCK_PAT = re.compile(r'from unittest\.mock import|from unittest import mock|import mock\b')
_C38_SETUP_BLOCK = re.compile(
    r'def setUp\s*\([^)]*\)[^:]*:.*?(?=\n {0,4}def |\Z)', re.DOTALL)


def _iter_test_files(*args, **kwargs):
    for root, _, files in os.walk(sts.test_dir):
        for f in sorted(files):
            if not f.startswith("test_") or not f.endswith(".py"): continue
            path = os.path.join(root, f)
            yield path, os.path.relpath(path, SRC_ROOT)


def _setup_reimplements(*args, block: str, **kwargs) -> bool:
    return (bool(re.search(r'tempfile\.(mkdtemp|TemporaryDirectory)', block))
            and "os.chdir" in block and "os.makedirs" in block)


def check_mock_usage(*args, **kwargs) -> tuple:
    warn, err = [], []
    for path, rel in _iter_test_files():
        with open(path) as fh:
            if _MOCK_PAT.search(fh.read()):
                warn.append(f"[{rel}] uses mock — prefer real IT or testhelper.test_setup")
    return warn, err


def check_testhelper_candidates(*args, **kwargs) -> tuple:
    warn, err = [], []
    for path, rel in _iter_test_files():
        with open(path) as fh: text = fh.read()
        if "@testhelper.test_setup" in text or "@test_setup" in text: continue
        if any(_setup_reimplements(block=b) for b in _C38_SETUP_BLOCK.findall(text)):
            warn.append(
                f"[{rel}] setUp uses tempfile + os.chdir + os.makedirs"
                " — consider @testhelper.test_setup")
    return warn, err


def check_test_file_location(*args, **kwargs) -> tuple:
    """Flag test_*.py / testhelper.py files outside any test/ directory."""
    err = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs if d not in {"__pycache__"}]
        for f in files:
            if not (f.startswith("test_") or f == "testhelper.py"): continue
            rel = os.path.relpath(os.path.join(root, f), SRC_ROOT).replace(os.sep, "/")
            if "test/" not in rel: err.append(f"[{rel}] test file outside test/ dir")
    return [], err


def check_sync_drift(*args, project_dir=None, sync_log=None, **kwargs) -> tuple:
    """Flag framework files with mtime > last_synced. Skip if sync_log absent."""
    pdir = project_dir or sts.package_dir
    slog = sync_log or os.path.join(os.path.expanduser("~"), f".{PKG}", "sync_log.yaml")
    if not os.path.exists(slog): return [], []
    with open(slog) as f: data = yaml.safe_load(f) or {}
    cutoff = dt.fromisoformat(data["last_synced"]).timestamp()
    err = [f"[{rel}] drift: modified after last_synced" for rel in _framework_files(pdir)
           if os.path.getmtime(os.path.join(pdir, rel)) > cutoff]
    return [], err


def _framework_files(pdir, *args, **kwargs):
    """Yield rel paths of all files under framework scopes (core, helpers, test/core)."""
    for scope in ("core", "helpers", "test/core"):
        sdir = os.path.join(pdir, scope)
        if not os.path.isdir(sdir): continue
        for root, dirs, files in os.walk(sdir):
            dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
            for f in files:
                yield os.path.relpath(os.path.join(root, f), pdir).replace(os.sep, "/")


_PKG_CHECKS = [
    ("mock usage",            check_mock_usage),
    ("testhelper candidates", check_testhelper_candidates),
    ("test file location",    check_test_file_location),
    ("sync drift",            check_sync_drift),
]

_PKG_META = {
    "mock usage": (
        "Mocking hides real behavior — prefer real integration tests or testhelper.test_setup.",
        "Remove mock imports; use realistic inputs and testhelper.test_setup for temp dirs.",
    ),
    "testhelper candidates": (
        "setUp manually re-implements tmpdir+chdir setup that @testhelper.test_setup provides.",
        "Replace setUp with @testhelper.test_setup and remove manual tempfile/os.chdir calls.",
    ),
    "test file location": (
        "test_*.py files outside test/ are not collected by the runner and can shadow real modules.",
        "Move the file under src/<pkg>/test/ mirroring the module it tests.",
    ),
    "sync drift": (
        "Framework files modified after last_synced indicate manual drift from upstream.",
        "Run 'proto-admin sync' from upstream to restore state, or propagate the change upstream.",
    ),
}


# ── rule metadata ──────────────────────────────────────────────────────────────
# Each rule: {fn, scope, exceptions_apply, why, fix, auto?}
# exceptions_apply=False → mandatory (c1, c11, docstring rules) — no YAML suppression.
# scope ∈ {'def', 'module', 'line'} — coarse annotation on the violation locus.
# auto=True → auto_correct.py has a corrector for this rule.

CHECKS = {
    'c1':  {'fn': _c1_function_length,    'scope': 'def',    'exceptions_apply': False,
            'why': "Long functions often mix concerns — harder to test and reason about in isolation.",
            'fix': "Split into smaller focused methods, or extract a helper."},
    'c2':  {'fn': _c2_one_line_functions, 'scope': 'def',    'exceptions_apply': True,
            'why': "A one-liner wrapper adds a call frame without any abstraction value.",
            'fix': "Inline the expression at the call site and remove the wrapper."},
    'c3':  {'fn': _c3_module_length,      'scope': 'module', 'exceptions_apply': True,
            'why': "Long modules tend to accumulate unrelated concerns.",
            'fix': "Split into focused sub-modules; move helpers to the appropriate layer."},
    'c4':  {'fn': _c4_kwargs_access,      'scope': 'def',    'exceptions_apply': True,
            'why': "kwargs.get() bypasses named param forwarding — callers cannot rely on it passing through.",
            'fix': "Declare the parameter explicitly in the function signature."},
    'c5':  {'fn': _c5_kwargs_signature,   'scope': 'def',    'exceptions_apply': True,
            'why': "Missing *args/**kwargs breaks hook-compatible forwarding across the call stack.",
            'fix': "Add *args, **kwargs to the function signature."},
    'c6':  {'fn': _c6_statement_semicolon,'scope': 'line',   'exceptions_apply': True,
            'why': "';' joins statements on one line — hides control flow and blocks per-line diffs.",
            'fix': "Split joined statements onto separate lines, or extract a helper method."},
    'c7':  {'fn': _c7_eval_exec,          'scope': 'line',   'exceptions_apply': True,
            'why': "eval/exec execute arbitrary strings — a security risk and debuggability hazard.",
            'fix': "Use explicit data structures, importlib, or a dispatch dict instead."},
    'c8':  {'fn': _c8_class_presence,     'scope': 'module', 'exceptions_apply': True,
            'why': "OOP is the primary paradigm — function-only modules often signal a missing abstraction.",
            'fix': "Wrap related functions in a class, or confirm the module is intentionally stateless."},
    'c10': {'fn': _c10_flat_imports,      'scope': 'module', 'exceptions_apply': True,
            'why': "Imports outside app/core/helpers create hidden coupling and break clone portability.",
            'fix': "Use only app/, core/, or helpers/ sub-packages."},
    'c11': {'fn': _c11_line_length,       'scope': 'line',   'exceptions_apply': False,
            'why': "Long lines reduce readability in split-screen editors and diff views.",
            'fix': "Wrap at a natural expression boundary, or extract a local variable."},
    'c12': {'fn': _c12_class_count,       'scope': 'module', 'exceptions_apply': True,
            'why': "Multiple classes in one module suggest it has more than one responsibility.",
            'fix': "Split into focused modules — one primary class per file."},
    'c13': {'fn': _c13_class_before_function, 'scope': 'module', 'exceptions_apply': True,
            'why': "Consistent ordering (classes first) makes navigation predictable.",
            'fix': "Move all module-level functions below the class definitions."},
    'c14': {'fn': _c14_elif_chains,       'scope': 'line',   'exceptions_apply': True,
            'why': "Long elif chains are hard to extend, test exhaustively, and read at a glance.",
            'fix': "Replace with a lookup dict or a dispatch table keyed on the condition value."},
    'c15': {'fn': _c15_deep_nesting,      'scope': 'line',   'exceptions_apply': True,
            'why': "Deep nesting increases cognitive load and makes logic harder to test.",
            'fix': "Extract inner blocks to helper methods, or invert conditions to reduce nesting."},
    'c16': {'fn': _c16_pass_only,         'scope': 'def',    'exceptions_apply': True,
            'why': "A pass-only function signals incomplete work or dead code.",
            'fix': "Implement the function body, or delete it if no longer needed."},
    'c17': {'fn': _c17_docstring,         'scope': 'module', 'exceptions_apply': True,
            'why': "Module docstrings with script_path: enable traceability and tool support.",
            'fix': "Add a triple-quote docstring with script_path: and a description."},
    'c18': {'fn': _c18_test_pairing,      'scope': 'module', 'exceptions_apply': True,
            'why': "Unpaired modules have no automated contract verification.",
            'fix': "Create the missing test file with at least one integration test scenario."},
    'c19': {'fn': _c19_mutable_defaults,  'scope': 'def',    'exceptions_apply': True,
            'why': "Mutable defaults persist across calls — mutations accumulate unexpectedly.",
            'fix': "Use None as default and assign the mutable value inside the function body."},
    'c20': {'fn': _c20_name_guard,        'scope': 'module', 'exceptions_apply': True,
            'why': "Without a __main__ guard the module body runs on import, not only when executed directly.",
            'fix': "Add 'if __name__ == \"__main__\": main()' at the bottom of the file."},
    'c21': {'fn': _c21_repeated_locals,   'scope': 'def',    'exceptions_apply': True,
            'why': "Repeated locals across many functions suggest state that belongs on a class.",
            'fix': "Pass the value explicitly as a named parameter, or promote to a class attribute."},
    'c24': {'fn': _c24_def_spacing,       'scope': 'line',   'exceptions_apply': True, 'auto': True,
            'why': "Inconsistent blank-line spacing makes file structure harder to scan visually.",
            'fix': "Use exactly 1 blank line before defs, 2 before classes."},
    'c25': {'fn': _c25_local_imports,     'scope': 'module', 'exceptions_apply': True,
            'why': "Local imports hide dependencies, delay import errors, and usually signal a circular-import workaround.",
            'fix': "Move the import to the module-level block. If circular, refactor the coupling."},
    'c26': {'fn': _c26_relative_imports,  'scope': 'module', 'exceptions_apply': True, 'auto': True,
            'why': "Relative imports break grepability and make module moves fragile.",
            'fix': "Replace with absolute imports: 'from protolib.module import x'."},
    'c27': {'fn': _c27_wildcard_imports,  'scope': 'module', 'exceptions_apply': True,
            'why': "Wildcard imports hide dependencies and pollute the module namespace.",
            'fix': "Import only the names you use: 'from module import Foo, bar'."},
    'c28': {'fn': _c28_bare_except,       'scope': 'line',   'exceptions_apply': True, 'auto': True,
            'why': "Bare except masks KeyboardInterrupt and SystemExit — real errors get swallowed.",
            'fix': "Catch the specific exception type(s) you expect: 'except ValueError:'."},
    'c29': {'fn': _c29_hardcoded_paths,   'scope': 'line',   'exceptions_apply': True,
            'why': "Hardcoded paths break portability across machines and environments.",
            'fix': "Use settings (sts.*), os.path, or pathlib.Path with relative anchors."},
    'c30': {'fn': _c30_raw_print,         'scope': 'line',   'exceptions_apply': True,
            'why': "Raw print() is unstructured and cannot be routed, filtered, or silenced.",
            'fix': "Use logprint() from helpers/printing, or move output to an API module."},
    'c32': {'fn': _c32_stdlib_logging,    'scope': 'line',   'exceptions_apply': True,
            'why': "stdlib logging adds unnecessary configuration and duplicates logprint().",
            'fix': "Import and use logprint from helpers/printing instead."},
    'c34': {'fn': _c34_strip_ansi_redef,  'scope': 'line',   'exceptions_apply': True,
            'why': "Redefining strip_ansi_codes creates silent drift from the canonical version.",
            'fix': "Import strip_ansi_codes from helpers/printing instead of redefining it."},
    'c35': {'fn': _c35_core_imports_app,  'scope': 'module', 'exceptions_apply': True,
            'why': "core/ importing app/ creates circular dependency risk and breaks clones.",
            'fix': "Move shared logic to core/ or helpers/, then import from there."},
    'c36': {'fn': _c36_inline_dict_size,  'scope': 'line',   'exceptions_apply': True,
            'why': "Large inline dicts are hard to update without redeployment and obscure config intent.",
            'fix': "Move to settings.py or a yaml/json resource file and load at startup."},
    'c40': {'fn': _c40_helpers_purity,    'scope': 'module', 'exceptions_apply': True,
            'why': "helpers/ modules must be portable to clones — core/app imports break that.",
            'fix': "Remove the import; helpers/ may only depend on stdlib, app.settings, and other helpers/."},
    'c41': {'fn': _c41_filename_collision,'scope': 'module', 'exceptions_apply': True,
            'why': "Two source modules with the same basename make imports ambiguous and grep noisy.",
            'fix': "Rename one module, or declare a c41 governance_exception if the duplication is by design."},
}


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


# ── test class ─────────────────────────────────────────────────────────────────

class TestGovernance(unittest.TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        log = GovernanceLog()
        all_codes = list(CHECKS) + list(META_CHECKS)
        cls.warns   = {code: [] for code in all_codes}
        cls.errs    = {code: [] for code in all_codes}
        cls.records = {code: [] for code in all_codes}
        cls.exceptions = []
        active = set(discover_sources())
        for rel in active:
            cls._scan_file(rel=rel, log=log)
        log.prune(active_keys=active)
        log.save()
        _save_exceptions_log(cls.exceptions, EXCS_LOG_PATH)

    @classmethod
    def _scan_file(cls, *args, rel, log, **kwargs):
        abs_path = os.path.join(SRC_ROOT, rel)
        with open(abs_path) as f: src = f.read()
        lines = src.splitlines(keepends=True)
        tree = cls._safe_parse(src)
        all_w, all_e = [], []
        file_records = {code: [] for code in list(CHECKS) + list(META_CHECKS)}
        for code, meta in CHECKS.items():
            w, e = cls._run_check(code=code, meta=meta, lines=lines, rel=rel,
                                  tree=tree, file_records=file_records)
            all_w.extend(w); all_e.extend(e)
        for code, meta in META_CHECKS.items():
            w, e = cls._run_meta(code=code, meta=meta, rel=rel,
                                 tree=tree, file_records=file_records)
            all_w.extend(w); all_e.extend(e)
        cls.exceptions.extend(_collect_file_exceptions(tree, rel, file_records))
        status = "error" if all_e else ("warn" if all_w else "pass")
        log.record(key=rel, mtime=os.path.getmtime(abs_path),
                   status=status, warnings=all_w, errors=all_e)

    @classmethod
    def _safe_parse(cls, src, *args, **kwargs):
        try: return ast.parse(src)
        except SyntaxError: return None

    @classmethod
    def _run_check(cls, *args, code, meta, lines, rel, tree=None,
                   file_records=None, **kwargs):
        w, e = meta['fn'](lines, rel)
        cls._record(code=code, scope=meta['scope'], warns=w, errs=e,
                    file_records=file_records)
        if tree is not None:
            w = _filter_docstring_excs(w, code=code, tree=tree, rules=CHECKS)
            e = _filter_docstring_excs(e, code=code, tree=tree, rules=CHECKS)
        cls._render(code=code, rel=rel, warns=w, errs=e)
        return w, e

    @classmethod
    def _run_meta(cls, *args, code, meta, rel, tree, file_records, **kwargs):
        if meta['kind'] == 'tree':
            w, e = meta['fn'](tree, rel, rules=CHECKS)
        else:
            w, e = meta['fn'](tree, file_records, rules=CHECKS)
        cls._record(code=code, scope='module', warns=w, errs=e, file_records=file_records)
        cls._render(code=code, rel=rel, warns=w, errs=e)
        return w, e

    @classmethod
    def _record(cls, *args, code, scope, warns, errs, file_records=None, **kwargs):
        for m in warns: cls._record_one(code, scope, m, 'warn', file_records)
        for m in errs: cls._record_one(code, scope, m, 'error', file_records)

    @classmethod
    def _record_one(cls, code, scope, msg, level, file_records, *args, **kwargs):
        line, tech = _parse_legacy(msg)
        rec = _rec(line=line, scope=scope, technical=tech, level=level)
        cls.records[code].append(rec)
        if file_records is not None: file_records[code].append(rec)

    @classmethod
    def _render(cls, *args, code, rel, warns, errs, **kwargs):
        cls.warns[code].extend(f"  [{rel}] {m}" for m in warns)
        cls.errs[code].extend(f"  [{rel}] {m}" for m in errs)

    def _msg(self, all_v, *args, why='', fix='', auto=False, **kwargs):
        parts = ["\n".join(all_v)]
        if why: parts.append(f"  why: {why}")
        if fix: parts.append(f"  fix: {fix}")
        if auto: parts.append(f"  auto: {_AC}")
        return "\n".join(parts)

    def _report(self, warns, errs, *args, **kwargs):
        all_v = warns + errs
        if not all_v: return
        msg = self._msg(all_v, **kwargs)
        if errs: self.fail(msg)
        else: print(f"\n{'─' * 60}\n{msg}")

    def _check(self, *args, code, **kwargs):
        m = CHECKS[code]
        self._report(self.warns[code], self.errs[code],
                     why=m['why'], fix=m['fix'], auto=m.get('auto', False))

    def _check_meta(self, *args, code, **kwargs):
        m = META_CHECKS[code]
        self._report(self.warns[code], self.errs[code], why=m['why'], fix=m['fix'])

    # ── per-file checks ────────────────────────────────────────────

    def test_c1_function_length(self, *args, **kwargs): self._check(code='c1')
    def test_c2_one_line_functions(self, *args, **kwargs): self._check(code='c2')
    def test_c3_module_length(self, *args, **kwargs): self._check(code='c3')
    def test_c4_kwargs_access(self, *args, **kwargs): self._check(code='c4')
    def test_c5_kwargs_signature(self, *args, **kwargs): self._check(code='c5')
    def test_c6_statement_semicolon(self, *args, **kwargs): self._check(code='c6')
    def test_c7_eval_exec(self, *args, **kwargs): self._check(code='c7')
    def test_c8_class_presence(self, *args, **kwargs): self._check(code='c8')
    def test_c10_flat_imports(self, *args, **kwargs): self._check(code='c10')
    def test_c11_line_length(self, *args, **kwargs): self._check(code='c11')
    def test_c12_class_count(self, *args, **kwargs): self._check(code='c12')
    def test_c13_class_before_function(self, *args, **kwargs): self._check(code='c13')
    def test_c14_elif_chains(self, *args, **kwargs): self._check(code='c14')
    def test_c15_deep_nesting(self, *args, **kwargs): self._check(code='c15')
    def test_c16_pass_only(self, *args, **kwargs): self._check(code='c16')
    def test_c17_docstring(self, *args, **kwargs): self._check(code='c17')
    def test_c18_test_pairing(self, *args, **kwargs): self._check(code='c18')
    def test_c19_mutable_defaults(self, *args, **kwargs): self._check(code='c19')
    def test_c20_name_guard(self, *args, **kwargs): self._check(code='c20')
    def test_c21_repeated_locals(self, *args, **kwargs): self._check(code='c21')
    def test_c24_def_spacing(self, *args, **kwargs): self._check(code='c24')
    def test_c25_local_imports(self, *args, **kwargs): self._check(code='c25')
    def test_c26_relative_imports(self, *args, **kwargs): self._check(code='c26')
    def test_c27_wildcard_imports(self, *args, **kwargs): self._check(code='c27')
    def test_c28_bare_except(self, *args, **kwargs): self._check(code='c28')
    def test_c29_hardcoded_paths(self, *args, **kwargs): self._check(code='c29')
    def test_c30_raw_print(self, *args, **kwargs): self._check(code='c30')
    def test_c32_stdlib_logging(self, *args, **kwargs): self._check(code='c32')
    def test_c34_strip_ansi_redef(self, *args, **kwargs): self._check(code='c34')
    def test_c35_core_imports_app(self, *args, **kwargs): self._check(code='c35')
    def test_c36_inline_dict_size(self, *args, **kwargs): self._check(code='c36')
    def test_c40_helpers_purity(self, *args, **kwargs): self._check(code='c40')
    def test_c41_filename_collision(self, *args, **kwargs): self._check(code='c41')

    # ── meta-rules ─────────────────────────────────────────────────

    def test_c_dfmt_docstring_format(self, *args, **kwargs): self._check_meta(code='c_dfmt')
    def test_c_dscope_exception_scope(self, *args, **kwargs): self._check_meta(code='c_dscope')
    def test_c_dorph_orphan_exception(self, *args, **kwargs): self._check_meta(code='c_dorph')

    # ── package-level checks ───────────────────────────────────────

    def test_pkg_mock_usage(self, *args, **kwargs):
        w, e = check_mock_usage()
        self._report(w, e, **{k: v for k, v in zip(('why', 'fix'), _PKG_META["mock usage"])})

    def test_pkg_testhelper_candidates(self, *args, **kwargs):
        w, e = check_testhelper_candidates()
        self._report(w, e,
            **{k: v for k, v in zip(('why', 'fix'), _PKG_META["testhelper candidates"])})

    def test_pkg_test_file_location(self, *args, **kwargs):
        w, e = check_test_file_location()
        self._report(w, e,
            **{k: v for k, v in zip(('why', 'fix'), _PKG_META["test file location"])})

    def test_pkg_sync_drift(self, *args, **kwargs):
        w, e = check_sync_drift()
        self._report(w, e,
            **{k: v for k, v in zip(('why', 'fix'), _PKG_META["sync drift"])})

    # ── zero-warning invariant (runs last) ─────────────────────────

    def test_zz_zero_warnings(self, *args, **kwargs):
        """Aggregate guard: any warning from c1–c_dorph fails the suite."""
        lines = [f"[{code}] {m}" for code, ws in self.warns.items() for m in ws]
        if lines:
            self.fail(f"{len(lines)} governance warning(s):\n" + "\n".join(lines))


class TestSyncDrift(unittest.TestCase):
    """c_sync_drift: detects framework-file modifications post-sync via mtime > last_synced."""

    def setUp(self, *args, **kwargs):
        import tempfile, shutil  # noqa: local to avoid polluting module imports
        self._shutil = shutil
        self.root = tempfile.mkdtemp()
        self.pkg_dir = os.path.join(self.root, "pkg")
        os.makedirs(os.path.join(self.pkg_dir, "core"))
        os.makedirs(os.path.join(self.pkg_dir, "helpers"))
        self.file = os.path.join(self.pkg_dir, "core", "settings.py")
        with open(self.file, "w") as f: f.write("x=1\n")
        self.sync_log = os.path.join(self.root, "sync_log.yaml")

    def tearDown(self, *args, **kwargs):
        self._shutil.rmtree(self.root)

    def _write_log(self, *args, ts: str, **kwargs):
        with open(self.sync_log, "w") as f:
            f.write(yaml.dump({"last_synced": ts, "synced_by": "protolib", "files": []}))

    def test_no_sync_log_skipped(self, *args, **kwargs):
        warn, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertEqual((warn, err), ([], []))

    def test_no_drift_when_files_older_than_last_synced(self, *args, **kwargs):
        self._write_log(ts="2099-01-01T00:00:00")
        _, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertEqual(err, [])

    def test_drift_detected_when_file_newer(self, *args, **kwargs):
        self._write_log(ts="1990-01-01T00:00:00")
        _, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertTrue(any("core/settings.py" in line for line in err))
