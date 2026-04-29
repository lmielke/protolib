"""
script_path: src/protolib/test/core/gov/helpers/c18.py
paths: ["**/*.py"]
purpose: "Helper: c18 — every module must have a paired test_<module>.py file."
description: |-
  Filesystem lookup against base.SRC_ROOT. Builds the expected test path
  by mirroring `rel` under `test/` with a `test_` prefix on the leaf
  filename. Emits one error record per missing pairing.
update_rules: "Do not modify in clones. SRC_ROOT taken from base."
"""
import os

from protolib.test.core.gov.base import SRC_ROOT


def run(*args, rel, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    parts = rel.replace(os.sep, "/").split("/")
    test_rel = "/".join(["test"] + parts[:-1] + [f"test_{parts[-1]}"])
    if os.path.exists(os.path.join(SRC_ROOT, test_rel.replace("/", os.sep))): return []
    return [{"level": "error", "line": 1, "scope": "module",
             "technical_message": f"no test file — create {test_rel}"}]
