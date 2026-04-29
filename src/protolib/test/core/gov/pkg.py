"""
script_path: src/protolib/test/core/gov/pkg.py
purpose: "Package-level checks (c50..c55) — stubs only; full bodies land in batch 2."
description: |-
  Each check has the uniform helper-style contract:
  `(*args, sources, **kwargs) -> tuple[list[tuple], list[tuple]]` emitting
  `(kind, params, scope_meta)`. The runner formats records via meta._rec
  against master ## cN templates; pkg.py composes no prose.
update_rules: "Stub bodies only — do not implement logic until batch 2."
governance_exceptions:
  - c1: "stub bodies are 1-line returns by design"
"""


def check_mock_usage(*args, sources, **kwargs) -> tuple:
    """purpose: 'c50 — flag unittest.mock imports under test/. Stub.'"""
    return [], []


def check_testhelper_candidates(*args, sources, **kwargs) -> tuple:
    """purpose: 'c51 — flag manual setUp matching @test_setup pattern. Stub.'"""
    return [], []


def check_test_file_location(*args, sources, **kwargs) -> tuple:
    """purpose: 'c52 — flag test_*.py outside test/. Stub.'"""
    return [], []


def check_sync_drift(*args, sources, **kwargs) -> tuple:
    """purpose: 'c53 — flag framework files modified after last_synced. Stub.'"""
    return [], []


def check_test_core_helper_location(*args, sources, **kwargs) -> tuple:
    """purpose: 'c54 — flag non-test, non-helper files in test/core/. Stub.'"""
    return [], []


def check_test_imports_test_file(*args, sources, **kwargs) -> tuple:
    """purpose: 'c55 — flag test_*.py importing another test_*.py. Stub.'"""
    return [], []
