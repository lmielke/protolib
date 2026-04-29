"""
script_path: src/protolib/helpers/docstrings.py
purpose: "Parse YAML front-matter docstrings into typed Docstring objects."
description: |-
  Shared helper used by test.core.helpers.auto_correct (c_dfmt fixer) and the governance
  registry. Keeps parsing logic in one place. Pure — ast + yaml only.
update_rules: "Do not modify in clones."
"""
import ast, yaml


class Docstring:
    """
    purpose: "Wrap a raw docstring; expose YAML front-matter meta and body."
    description: "Empty or malformed YAML yields meta=None, body=''."
    """

    def __init__(self, raw, *args, **kwargs):
        self.raw = raw or ""
        self.meta, self.body = self._parse(self.raw)

    def _parse(self, raw, *args, **kwargs) -> tuple:
        """purpose: Split on first blank line; parse head as YAML."""
        if not raw: return None, ""
        parts = raw.split("\n\n", 1)
        head, body = parts[0], (parts[1] if len(parts) > 1 else "")
        try: meta = yaml.safe_load(head)
        except yaml.YAMLError: return None, ""
        return (meta, body) if isinstance(meta, dict) else (None, "")

    def get(self, *args, key, default=None, **kwargs):
        """purpose: Lookup a meta key; return default when meta is None or absent."""
        return (self.meta or {}).get(key, default)


class Docstrings:
    """
    purpose: "Factories for Docstring objects from AST nodes or classes."
    description: "from_node → single Docstring. from_class → dict keyed by method."
    """

    @staticmethod
    def from_node(node, *args, **kwargs) -> "Docstring":
        """purpose: Docstring built from ast.get_docstring of any node type."""
        return Docstring(ast.get_docstring(node, clean=False))

    @staticmethod
    def from_class(tree, *args, class_name, **kwargs) -> dict:
        """purpose: Map method name → Docstring for every def in the named class."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return {m.name: Docstring(ast.get_docstring(m, clean=False))
                        for m in node.body
                        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        return {}
