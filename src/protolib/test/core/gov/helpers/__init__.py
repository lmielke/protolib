"""
script_path: src/protolib/test/core/gov/helpers/__init__.py
purpose: "Package marker for per-check governance helpers."
description: |-
  Each cN.py exposes a `run(*args, lines, rel, tree, **kwargs) -> (warns, errs)`
  callable. Auto-correct pairs (cN_auto_correct.py) expose `fix(*args, path, rel,
  **kwargs) -> bool`. base.py carries shared AST/source utilities.
update_rules: "Add new cN modules; do not put rule logic here."
governance_exceptions:
  - c18: "package marker — no IT pairing required"
"""
