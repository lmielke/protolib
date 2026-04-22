"""
script_path: src/protolib/test/core/test_kwargs.py
purpose: "AST-based kwargs convention validator. Used as PostToolUse hook."
description: |
  Replaces the regex-based shell hook. Reads JSON on stdin with
  tool_input.file_path, parses the target file with ast, and rejects any
  FunctionDef / AsyncFunctionDef missing *args or **kwargs.

  Exit codes match the hook protocol: 0 = pass, 2 = block with stderr.
  Unparseable files pass (syntax errors surface elsewhere).
"""
import ast, json, os, sys


def _extract_path(*args, **kwargs):
    raw = sys.stdin.read().strip()
    if not raw: return ""
    try: payload = json.loads(raw)
    except json.JSONDecodeError: return ""
    return payload.get("tool_input", {}).get("file_path") or ""


def _should_skip(*args, path, **kwargs):
    if not path.endswith(".py"): return True
    base = os.path.basename(path)
    return "/test/" in path or base.startswith("test_")


def _try_parse(*args, path, **kwargs):
    try:
        with open(path) as f: return ast.parse(f.read())
    except (SyntaxError, OSError): return None


def _violations(*args, tree, **kwargs):
    types = (ast.FunctionDef, ast.AsyncFunctionDef)
    return [n for n in ast.walk(tree) if isinstance(n, types)
            and (n.args.vararg is None or n.args.kwarg is None)]


def _report(*args, path, bad, **kwargs):
    sys.stderr.write(f"kwargs convention violation in {os.path.basename(path)}:\n")
    for n in bad:
        sys.stderr.write(f"  Line {n.lineno}: def {n.name}(...)\n")
    sys.stderr.write("All function definitions must include *args, **kwargs"
                     " (except external library calls).\n")


def _check(*args, path, **kwargs):
    tree = _try_parse(path=path)
    if tree is None: return 0
    bad = _violations(tree=tree)
    if not bad: return 0
    _report(path=path, bad=bad)
    return 2


def main(*args, **kwargs):
    path = _extract_path()
    if _should_skip(path=path): return 0
    return _check(path=path)


if __name__ == "__main__":
    sys.exit(main())
