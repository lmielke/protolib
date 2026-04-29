"""
script_path: src/protolib/test/core/gov/helpers/c12.py
paths: ["**/*.py"]
purpose: "Helper: c12 — class count per module."
description: |-
  Counts top-level ClassDef nodes in the module body. Emits 'warn' when
  count exceeds max_classes — usually means the module owns more than
  one responsibility.
update_rules: "Do not modify in clones. Threshold arrives via **params from settings.yml."
"""
import ast


def run(*args, tree, max_classes, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    n = sum(1 for node in tree.body if isinstance(node, ast.ClassDef))
    if n <= max_classes: return []
    msg = f"{n} classes in module (>{max_classes}) — consider splitting"
    return [{"line": 1, "scope": "module", "level": "warn", "technical_message": msg}]
