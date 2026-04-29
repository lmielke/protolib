"""
script_path: src/protolib/test/core/gov/meta.py
purpose: "Record formatter — total-reuse template path from master ## cN blocks."
description: |-
  _rec resolves name/rule verbatim from CHECKS[code] and formats display_message
  (from purpose template) and technical_message (from tech / tech_templates[kind])
  against the merged runtime+config namespace. KeyError on unresolved placeholder
  surfaces as build failure — no silent fallback.
update_rules: "Do not modify in clones. Template formatter only."
governance_exceptions:
  - c1: "_rec assembles the record dict; pieces stay together for clarity"
"""
from protolib.test.core.gov import settings as sts


def _rec(*args, code: str, kind=None, params: dict, scope_meta: dict, spec: dict, **kwargs) -> dict:
    """purpose: 'Format one record per total-reuse contract. Returns dict.'"""
    ns = _ns(code=code, params=params)
    tech_tpl = spec["tech_templates"][kind] if kind else spec["tech"]
    return {
        "name":   spec["name"],
        "rule":   spec["rule"],
        "helper": f"src/protolib/test/core/gov/helpers/{code}.py",
        "line":   scope_meta["line"],
        "scope":  scope_meta["scope"],
        "technical_message": tech_tpl.format(**ns),
        "display_message":   spec["purpose"].format(**ns),
    }


def _ns(*args, code: str, params: dict, **kwargs) -> dict:
    """purpose: 'Merge runtime params with config params from sts.<code>.* namespace.'"""
    cfg = vars(getattr(sts, code)) if hasattr(sts, code) else {}
    return {**cfg, **params}
