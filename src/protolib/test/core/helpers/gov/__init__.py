"""
script_path: src/protolib/test/core/helpers/gov/__init__.py
purpose: "[TO_DELETE] Governance package entry point — build CHECKS from catalog, expose helpers."
description: |-
  CHECKS is built at import time via catalog.build_checks() which parses
  test_governance.py docstrings. META_CHECKS comes from meta.py as a static dict.
update_rules: "Do not modify in clones."
"""
from protolib.test.core.helpers.gov.catalog import build_checks
from protolib.test.core.helpers.gov.meta import META_CHECKS

CHECKS = build_checks()
