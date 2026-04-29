"""
script_path: src/protolib/test/core/gov/helpers/c11.py
paths: ["**/*.py"]
purpose: "Helper: c11 — line length. Emit violation records per long line."
description: |-
  Per-line character-count check. Emits 'error' when len(line) > params['max'],
  'warn' when len(line) > params['warn']. Composes own technical_message /
  display_message inline from params.
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""


def run(*args, lines, warn, max, **params) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    records = []
    for i, line in enumerate(lines):
        if rec := _check(line=line, lineno=i + 1, warn=warn, max=max):
            records.append(rec)
    return records


def _check(*args, line, lineno, warn, max, **kwargs) -> dict:
    """purpose: 'Return violation record if line trips threshold else {}.'"""
    n = len(line)
    level = "error" if n > max else ("warn" if n > warn else None)
    if level is None: return {}
    tech = f"line length {n} (max {max})" if level == "error" \
           else f"line length {n} (warn >{warn}, error >{max})"
    return {"level": level, "line": lineno, "scope": "module",
            "technical_message": tech}
