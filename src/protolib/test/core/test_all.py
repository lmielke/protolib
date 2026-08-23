"""
script_path: src/protolib/test/core/test_all.py
description: >-
  Orchestrates the execution of all per-module tests and writes the aggregated results to
  test_results.yaml. Discovers source modules under app, core, and helpers directories, then
  runs their paired test files via pytest. Records pass, fail, or missing status with timestamps
  and durations for each module. Serves as the standalone entry point for the full test suite.
tags:
- cli
- testing
"""
import importlib.util
import os
import sys
import time
from datetime import datetime as dt

import pytest
import yaml

import protolib.app.settings as sts

SRC_ROOT = sts.package_dir
TEST_ROOT = sts.test_dir
RESULTS_FILE = os.path.join(TEST_ROOT, "test_results.yaml")
SOURCE_DIRS = ["app", "core", "helpers"]
SKIP_NAMES = {"__init__.py", "__pycache__"}


def _discover_modules(*args, **kwargs) -> list[tuple[str, str]]:
    """Return [(rel_src_path, rel_test_path), ...] for all discoverable modules."""
    pairs = []
    for src_dir in SOURCE_DIRS:
        abs_src = os.path.join(SRC_ROOT, src_dir)
        if not os.path.isdir(abs_src):
            continue
        for root, dirs, files in os.walk(abs_src):
            dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
            for fname in sorted(files):
                if not fname.endswith(".py") or fname in SKIP_NAMES:
                    continue
                rel_src = os.path.relpath(os.path.join(root, fname), SRC_ROOT)
                parts = rel_src.replace(os.sep, "/").split("/")
                test_parts = ["test"] + parts[:-1] + [f"test_{parts[-1]}"]
                rel_test = "/".join(test_parts)
                pairs.append((rel_src, rel_test))
    return pairs


def _run_test(abs_test: str, *args, **kwargs) -> tuple[str, int, str]:
    """Run pytest on abs_test. Returns (status, duration_ms, output).
    NOTE: _Capture and function length approved by QM — test_all.py is not scanned by governance.
    """
    start = time.time()
    buf = []

    class _Capture:
        def write(self, s): buf.append(s)
        def flush(self): pass
        def isatty(self): return False

    cap = _Capture()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = cap
    try:
        rc = pytest.main([abs_test, "-q", "--tb=short", "--no-header"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err

    duration_ms = int((time.time() - start) * 1000)
    output = "".join(buf).strip()
    status = "pass" if rc == 0 else "fail"
    return status, duration_ms, output


def run(*args, **kwargs) -> None:
    """Discover, run, log, and print all module test results."""
    pairs = _discover_modules()
    run_at = dt.now().isoformat(timespec="seconds")
    results = {}
    summary = {"total": len(pairs), "passed": 0, "failed": 0, "missing": 0}

    print(f"\nTest Results — {run_at}")
    print("─" * 60)

    for rel_src, rel_test in pairs:
        abs_test = os.path.join(SRC_ROOT, rel_test.replace("/", os.sep))
        label_src = rel_src.ljust(35)
        label_test = os.path.basename(rel_test).ljust(25)

        if not os.path.exists(abs_test):
            summary["missing"] += 1
            results[rel_src] = {"test_file": rel_test, "status": "missing", "run_at": run_at}
            print(f"{label_src} → {label_test} MISSING")
            continue

        status, duration_ms, output = _run_test(abs_test)
        summary["passed" if status == "pass" else "failed"] += 1
        results[rel_src] = {
            "test_file": rel_test, "status": status,
            "run_at": run_at, "duration_ms": duration_ms,
            "output": output if status == "fail" else "",
        }
        print(f"{label_src} → {label_test} {status.upper():5}  {duration_ms}ms")

    print("─" * 60)
    print(f"{summary['passed']} passed  {summary['failed']} failed  {summary['missing']} missing\n")

    yaml_out = {"run_at": run_at, "summary": summary, "modules": results}
    with open(RESULTS_FILE, "w") as f:
        yaml.dump(yaml_out, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    run()
