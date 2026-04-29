"""
script_path: src/protolib/test/core/gov/settings.py
purpose: "Load gov/settings.yml — engine config (scan filters, log header)."
description: |-
  Reads settings.yml once at import; exposes top-level keys as module-level
  attributes. Per-rule thresholds live inline in governance.py cN_params
  blocks — this module only carries engine-wide config.
update_rules: "Do not add threshold literals here. Inline them in governance.py."
governance_exceptions:
  - c1: "loop body sets module-level attrs — single concern, kept inline"
"""
import yaml
from pathlib import Path
from types import SimpleNamespace

_PATH = Path(__file__).parent / "settings.yml"
_DATA = yaml.safe_load(_PATH.read_text()) or {}

checks = _DATA                                  # literate dict-access: sts.checks['<key>']

for _code, _ns in _DATA.items():
    globals()[_code] = SimpleNamespace(**_ns) if isinstance(_ns, dict) else _ns
