"""
script_path: src/protolib/test/core/gov/helpers/c20.py
paths: ["**/*.py"]
purpose: "Helper: c20 — module-level main() must guard on __name__ == '__main__'."
description: |-
  When any line matches `^def main\\(`, the module must also contain a
  `if __name__ == '__main__'` line. Otherwise emit one warn at the top.
update_rules: "Do not modify in clones. No thresholds."
"""
import re

_MAIN = re.compile(r'^def main\(')
_GUARD = re.compile(r'if __name__\s*==\s*[\'"]__main__[\'"]')


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    if not any(_MAIN.match(l) for l in lines): return []
    if any(_GUARD.match(l) for l in lines): return []
    return [{"level": "warn", "line": 1, "scope": "module",
             "technical_message": "has main() but no if __name__ == '__main__' guard"}]
