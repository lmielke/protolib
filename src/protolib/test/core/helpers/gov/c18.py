"""
script_path: src/protolib/test/core/helpers/gov/c18.py
purpose: "[TO_DELETE] c18 — test pairing check. Every module must have a matching test_*.py file."
description: "Uses test_results.yaml if present; else falls back to filesystem lookup."
update_rules: "Do not modify in clones."
"""
import os, yaml
import protolib.core.settings as sts
from protolib.test.core.helpers.gov.base import SRC_ROOT


def _c18_test_pairing(lines, rel, *args, **kwargs):
    """purpose: Flag modules that lack a paired test file."""
    warn, err = [], []
    results_path = os.path.join(sts.test_dir, "test_results.yaml")
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = yaml.safe_load(f) or {}
        entry = results.get("modules", {}).get(rel.replace(os.sep, "/"), {})
        if entry.get("status") == "missing":
            err.append(f"test missing: {entry.get('test_file', '?')} (from test_results.yaml)")
    else:
        parts = rel.replace(os.sep, "/").split("/")
        test_rel = "/".join(["test"] + parts[:-1] + [f"test_{parts[-1]}"])
        if not os.path.exists(os.path.join(SRC_ROOT, test_rel.replace("/", os.sep))):
            err.append(f"no test file — create {test_rel}")
    return warn, err
