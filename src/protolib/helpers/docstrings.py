"""
script_path: src/protolib/helpers/docstrings.py
description: >-
  Parses YAML front-matter docstrings into typed Docstring objects by splitting on the first
  blank line and loading the head as YAML. Exposes a get method for safe key lookup and provides
  factory methods to build instances from AST nodes or entire classes. Consumed by the test
  auto-correct fixer and the governance registry to centralize parsing logic.
tags:
- governance
- parsing
- testing
update_rules: Do not modify in clones.
"""
import ast, yaml


class Docstring:
    """
    description: "Empty or malformed YAML yields meta=None, body=''."
    """

    def __init__(self, raw, *args, **kwargs):
        self.raw = raw or ""
        self.meta, self.body = self._parse(self.raw, *args, **kwargs)

    def _parse(self, raw, *args, **kwargs) -> tuple:
        """description: Structural scan to bound YAML head; parse head; body is remainder."""
        if not raw: return None, ""
        head_end = self._head_end(raw.splitlines(), *args, **kwargs)
        lines = raw.splitlines()
        head = "\n".join(lines[:head_end])
        body = "\n".join(lines[head_end:]).lstrip("\n")
        try: meta = yaml.safe_load(head)
        except yaml.YAMLError: return None, ""
        return (meta, body) if isinstance(meta, dict) else (None, "")

    def _head_end(self, lines, *args, **kwargs) -> int:
        """description: Walk lines; stop at a blank gap that is not a block continuation."""
        i, n = 0, len(lines)
        while i < n:
            if lines[i] != "":
                i += 1
                continue
            j = self._skip_gap(lines, i + 1, n, *args, **kwargs)
            if j is None: return i
            i = j
        return n

    def _skip_gap(self, lines, start, n, *args, **kwargs) -> "int | None":
        """description: Skip blank lines; return next index if continuation, else None."""
        j = start
        while j < n and lines[j] == "":
            j += 1
        return j if j < n and lines[j].startswith((" ", "\t", "- ")) else None

    def get(self, *args, key, default=None, **kwargs):
        """description: Lookup a meta key; return default when meta is None or absent."""
        return (self.meta or {}).get(key, default)


class Docstrings:
    """
    description: "from_node → single Docstring. from_class → dict keyed by method."
    """

    @staticmethod
    def from_node(node, *args, **kwargs) -> "Docstring":
        """description: Docstring built from ast.get_docstring of any node type."""
        return Docstring(ast.get_docstring(node, clean=False))

    @staticmethod
    def from_class(tree, *args, class_name, **kwargs) -> dict:
        """description: Map method name → Docstring for every def in the named class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return {m.name: Docstring(ast.get_docstring(m, clean=False))
                        for m in node.body
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        return {}
