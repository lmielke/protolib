"""
script_path: src/protolib/test/core/gov/helpers/c2.py
paths: ["**/*.py"]
purpose: "Helper: c2 — module-level one-line functions (warn)."
description: |-
  Walks parse_defs() output. Module-level (indent==0) defs whose body is
  a single non-comment real line emit a warn. Dunders and names listed
  in exempt_names are excluded.
update_rules: "Do not modify in clones. exempt_names via params."
"""
from protolib.test.core.gov.base import parse_defs


def run(*args, lines, exempt_names, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    exempt = set(exempt_names)
    return [r for lineno, indent, name, body in parse_defs(lines)
            if (r := _check(lineno=lineno, indent=indent, name=name, body=body, exempt=exempt))]


def _check(*args, lineno, indent, name, body, exempt, **kwargs) -> dict:
    """purpose: 'Return record if def is a module-level one-liner else {}.'"""
    if indent != 0: return {}
    if name in exempt or (name.startswith('__') and name.endswith('__')): return {}
    real = [l for l in body if not l.strip().startswith("#")]
    if len(real) != 1: return {}
    return {"level": "warn", "line": lineno + 1, "scope": "def",
            "technical_message": f"{name}() is one-line — candidate to inline"}
