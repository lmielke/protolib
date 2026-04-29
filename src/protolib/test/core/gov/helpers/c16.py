"""
script_path: src/protolib/test/core/gov/helpers/c16.py
paths: ["**/*.py"]
purpose: "Helper: c16 — pass-only function bodies (warn)."
description: |-
  Walks parse_defs(). Defs whose real body equals exactly ['pass'] emit
  a warn unless the name is in exempt_names (default __init__).
update_rules: "Do not modify in clones. exempt_names via params."
"""
from protolib.test.core.gov.base import parse_defs


def run(*args, lines, exempt_names, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    exempt = set(exempt_names)
    return [r for lineno, _, name, body in parse_defs(lines)
            if (r := _check(lineno=lineno, name=name, body=body, exempt=exempt))]


def _check(*args, lineno, name, body, exempt, **kwargs) -> dict:
    """purpose: 'Return record if body is exactly pass and not exempt.'"""
    real = [l.strip() for l in body if l.strip() and not l.strip().startswith("#")]
    if real != ["pass"] or name in exempt: return {}
    return {"level": "warn", "line": lineno + 1, "scope": "def",
            "technical_message": f"{name}() is pass-only — implement or remove"}
