"""
script_path: src/protolib/test/core/gov/helpers/c3.py
paths: ["**/*.py"]
purpose: "Helper: c3 — module length. Emit module-scope record on threshold trip."
description: |-
  Counts total source lines in the module. Emits 'error' when n > max,
  'warn' when n > warn. Skips modules below min_lines (tiny stubs ok).
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""


def run(*args, lines, warn, max, min_lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    n = len(lines)
    if n < min_lines: return []
    level = "error" if n > max else ("warn" if n > warn else None)
    if level is None: return []
    tech = f"module has {n} lines (max {max})" if level == "error" \
           else f"module has {n} lines (warn >{warn}, error >{max})"
    return [{"level": level, "line": 1, "scope": "module", "technical_message": tech}]
