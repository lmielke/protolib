"""
script_path: src/protolib/test/core/helpers/gov/base.py
purpose: "[TO_DELETE] Pure AST utilities for governance checks — no I/O, no classes."
description: |-
  Source-scanning primitives used by all gov/cN check modules.
  discover_sources walks SRC_ROOT; parse_defs/find_body_end/_signature_text
  extract def regions; _code_lines drops comments and docstrings.
update_rules: "Do not modify in clones."
"""
import os, re
import protolib.core.settings as sts

SRC_ROOT = sts.package_dir
SCAN_SKIP_DIRS = {"test", "resources", "__pycache__"}
SKIP_FILES = {"__init__.py", "__main__.py", "auto_correct.py"}


def discover_sources(*args, **kwargs) -> list:
    """purpose: List relative paths of all source files under SRC_ROOT."""
    paths = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = sorted(x for x in dirs if x not in SCAN_SKIP_DIRS and not x.startswith("__"))
        for f in sorted(files):
            if not f.endswith(".py") or f in SKIP_FILES: continue
            if f.startswith("test_"): continue
            paths.append(os.path.relpath(os.path.join(root, f), SRC_ROOT))
    return paths


def find_body_end(lines, start, indent, *args, **kwargs) -> int:
    """purpose: Find line index where a def body ends (dedent back to parent)."""
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if not line.strip(): continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= indent and not line.lstrip().startswith(('#', ')', ']', '}')):
            return i
    return len(lines)


def parse_defs(lines, *args, **kwargs) -> list:
    """purpose: Extract (start, indent, name, body_lines) for each def in lines."""
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
    """purpose: Join def line through matching close paren."""
    buf, depth = [], 0
    for i in range(start, len(lines)):
        buf.append(lines[i])
        depth += lines[i].count('(') - lines[i].count(')')
        if depth == 0 and buf: return ''.join(buf)
    return ''.join(buf)


def _code_lines(body, *args, **kwargs) -> list:
    """purpose: Filter body to executable code — drop comments and triple-quoted strings."""
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
