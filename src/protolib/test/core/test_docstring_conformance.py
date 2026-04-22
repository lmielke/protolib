"""
script_path: src/protolib/test/core/test_docstring_conformance.py
purpose: >-
  Pre-flight test: every protolib source module parses as canonical
  front-matter docstrings (YAML head + required keys per scope).
update_rules: "Run on every commit. Breaks if a docstring drifts from the template."
"""
import ast, os, unittest, yaml
from pathlib import Path
from protolib.helpers.collections import load_docstring_schema

SRC_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SRC_ROOT.parents[1]
SKIP_DIRS = {"test", "resources", "__pycache__"}
SKIP_FILES = {"__init__.py", "__main__.py", "auto_correct.py"}

_DS = load_docstring_schema()
ALLOWED = {s: v['allowed'] for s, v in _DS.items()}
REQUIRED = {s: v['required'] for s, v in _DS.items()}


class TestDocstringConformance(unittest.TestCase):

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.issues = []
        for path in _walk_sources():
            cls.issues.extend(_check_file(path))

    def test_all_docstrings_conform(self, *args, **kwargs):
        if self.issues:
            self.fail("\n".join(self.issues))


def _walk_sources(*args, **kwargs):
    for p in sorted(SRC_ROOT.rglob("*.py")):
        parts = p.relative_to(SRC_ROOT).parts
        if any(part in SKIP_DIRS for part in parts): continue
        if p.name in SKIP_FILES or p.name.startswith("test_"): continue
        yield p


def _check_file(path, *args, **kwargs) -> list:
    src = path.read_text()
    tree = ast.parse(src)
    issues = []
    for node, scope in _docstring_nodes(tree):
        ds = ast.get_docstring(node, clean=False)
        if ds is None:
            if scope == 'module':
                issues.append(f"{_rel(path)}: module has no docstring")
            continue
        issues += _validate(ds, scope, path, node)
    return issues


def _docstring_nodes(tree, *args, **kwargs):
    yield tree, 'module'
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef): yield n, 'class'
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): yield n, 'def'


def _validate(ds, scope, path, node, *args, **kwargs) -> list:
    meta = _parse_head(ds)
    loc = f"{_rel(path)}:{getattr(node, 'lineno', 1)} [{scope}]"
    if not isinstance(meta, dict):
        return [f"{loc}: docstring head is not YAML mapping"]
    issues = [f"{loc}: missing {k}" for k in REQUIRED[scope] if k not in meta]
    issues += [f"{loc}: unexpected key {k!r}" for k in meta if k not in ALLOWED[scope]]
    if scope == 'module':
        issues += _check_script_path(meta, path, loc)
    return issues


def _check_script_path(meta, path, loc, *args, **kwargs) -> list:
    got = meta.get('script_path')
    want = os.path.relpath(path, REPO_ROOT).replace(os.sep, '/')
    if got != want:
        return [f"{loc}: script_path mismatch: {got!r} != {want!r}"]
    return []


def _parse_head(ds, *args, **kwargs):
    head = ds.split("\n\n", 1)[0]
    try: return yaml.safe_load(head)
    except yaml.YAMLError: return None


def _rel(path, *args, **kwargs) -> str:
    return os.path.relpath(path, REPO_ROOT).replace(os.sep, '/')


if __name__ == "__main__":
    unittest.main()
