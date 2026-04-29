"""
script_path: src/protolib/test/core/gov/catalog.py
purpose: "Build CHECKS / META_CHECKS by parsing master governance.py at import."
description: |-
  Imports the master module (executes module body — helper PATTERNS attached,
  etc.), then parses the source text for ## cN markers + following docstring
  blocks. Each rule resolves to a helper module and run callable. Enforces
  orphan-pair invariant (every helper has master block, every master block has
  helper file) and PATTERNS-keys invariant (tech_templates keys 1:1 with
  helper.PATTERNS keys when both present). Failures raise CatalogError.
update_rules: "Do not modify in clones."
governance_exceptions:
  - c1: "_validate_pair_invariants reads filesystem; clarity > line count"
"""
import importlib
import re
from pathlib import Path

import yaml

HELPERS_DIR = Path(__file__).parent / "helpers"
MASTER_PATH = Path(__file__).parent / "governance.py"
MARKER_RE = re.compile(r'^##\s+(c\d+(?:_\d+)?)\s*$', re.MULTILINE)
DOCSTRING_RE = re.compile(r'"""\s*\n(.*?)"""', re.DOTALL)


class CatalogError(Exception):
    """purpose: 'Raised on master/helper mismatch or invariant violation.'"""


def parse_master(*args, master_path: Path = MASTER_PATH, **kwargs) -> dict:
    """purpose: 'Parse master ## cN blocks; return dict[code -> RuleSpec dict].'"""
    text = Path(master_path).read_text()
    matches = list(MARKER_RE.finditer(text))
    rules = {}
    for i, m in enumerate(matches):
        code = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        rules[code] = _parse_block(code=code, block=text[m.end():end])
    return rules


def _parse_block(*args, code: str, block: str, **kwargs) -> dict:
    """purpose: 'Parse one ## cN block — extract docstring YAML + resolve helper.'"""
    ds = DOCSTRING_RE.search(block)
    if not ds: raise CatalogError(f"{code}: missing docstring block after ## marker")
    spec = yaml.safe_load(ds.group(1)) or {}
    _require_fields(code=code, spec=spec)
    helper = importlib.import_module(f"protolib.test.core.gov.helpers.{code}")
    spec["helper"] = helper
    spec["fn"] = helper.run
    return spec


def _require_fields(*args, code: str, spec: dict, **kwargs) -> None:
    """purpose: 'Assert master block declares name/rule/purpose/description + tech*.'"""
    for field in ("name", "rule", "purpose", "description"):
        if field not in spec: raise CatalogError(f"{code}: missing '{field}' in master block")
    if "tech" not in spec and "tech_templates" not in spec:
        raise CatalogError(f"{code}: master block needs 'tech:' or 'tech_templates:'")


def _orphan_check(*args, rules: dict, **kwargs) -> None:
    """purpose: 'Every helpers/cN.py has master block; every master block has helper file.'"""
    helper_codes = {p.stem for p in HELPERS_DIR.glob("c*.py")
                    if not p.stem.endswith("_auto_correct") and p.stem != "__init__"}
    master_codes = set(rules)
    if missing := helper_codes - master_codes:
        raise CatalogError(f"helpers without master block: {sorted(missing)}")
    if missing := master_codes - helper_codes:
        raise CatalogError(f"master blocks without helper: {sorted(missing)}")


def _patterns_invariant(*args, rules: dict, **kwargs) -> None:
    """purpose: 'tech_templates keys 1:1 with helper.PATTERNS keys when both present.'"""
    for code, spec in rules.items():
        if "tech_templates" not in spec: continue
        helper = spec["helper"]
        if not hasattr(helper, "PATTERNS"): continue
        if (tk := set(spec["tech_templates"])) != (pk := set(helper.PATTERNS)):
            raise CatalogError(f"{code}: tech_templates keys {tk} != PATTERNS keys {pk}")


# Build at import — fail loud on any invariant breach.
importlib.import_module("protolib.test.core.gov.governance")
CHECKS: dict = parse_master()
_orphan_check(rules=CHECKS)
_patterns_invariant(rules=CHECKS)
META_CHECKS: dict = {c: s for c, s in CHECKS.items() if c.startswith("c9")}
