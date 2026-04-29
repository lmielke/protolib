"""
script_path: src/protolib/test/core/gov/helpers/c10.py
paths: ["**/*.py"]
purpose: "Helper: c10 — flat imports must route through app/core/helpers/test."
description: |-
  Scans for `import PKG.X` or `from PKG.X` and emits 'error' when X is
  not in allowed_subpkgs. PKG arrives via params from core_sts at master
  load time so clones automatically validate against their own package
  name.
update_rules: "Do not modify in clones. PKG / allowed_subpkgs via params."
"""
import re


def run(*args, lines, pkg, allowed_subpkgs, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    pat = re.compile(rf'(?:import|from)\s+{re.escape(pkg)}\.(\w+)')
    allowed = set(allowed_subpkgs)
    return [_rec(i=i, pkg=pkg, sub=m.group(1)) for i, line in enumerate(lines)
            if (m := pat.search(line.split("#", 1)[0])) and m.group(1) not in allowed]


def _rec(*args, i, pkg, sub, **kwargs) -> dict:
    """purpose: 'Build one error record for a flat-import line.'"""
    return {"level": "error", "line": i + 1, "scope": "module",
            "technical_message": f"flat import '{pkg}.{sub}' — use app/core/helpers only"}
