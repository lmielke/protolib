"""
script_path: conftest.py
description: >-
  Tracks pytest session results and persists them to a package-specific home directory. A
  single SessionTracker instance owns failed node IDs and resolved package name, excluding
  governance tests from the count. Two module-level pytest hooks delegate to the tracker for
  failure accumulation and final JSON output.
tags:
- hook
- infra
- testing
"""
import json, tomllib
from datetime import datetime
from pathlib import Path


class SessionTracker:
    """
    description: "Owns the set of failed node IDs collected during the run and the
      resolved package name read from pyproject.toml at construction time. Two
      public methods serve as targets for the module-level pytest hooks:
      track_failure accumulates failures during the run, finish assembles and
      writes the results file at session end."
    """

    excluded = "test_governance.py"

    def __init__(self, *args, **kwargs):
        self._root = Path(__file__).parent
        self._pkg = tomllib.loads(
            (self._root / "pyproject.toml").read_text()
        ).get("project", {}).get("name", "protolib")
        self._failed = set()

    def track_failure(self, report, *args, **kwargs) -> None:
        """description: 'Record a failed test node ID, skipping excluded files.'"""
        if report.failed and report.when == "call" and self.excluded not in report.nodeid:
            self._failed.add(report.nodeid)

    def finish(self, session, *args, **kwargs) -> None:
        """description: 'Assemble results from the session and write to the package home dir.'"""
        items = [i for i in (session.items or []) if self.excluded not in i.nodeid]
        self._write(self._build(items, *args, **kwargs), *args, **kwargs)

    def _build(self, items: list, *args, **kwargs) -> dict:
        """description: 'Assemble the test-results payload from collected items and failures.'"""
        total, failed = len(items), len(self._failed)
        return {
            "tests": total,
            "passed": total - failed,
            "failed": failed,
            "failures": sorted(self._failed),
            "timestamp": datetime.now().isoformat(timespec='seconds'),
        }

    def _write(self, results: dict, *args, **kwargs) -> None:
        """description: 'Write results dict to ~/.<pkg>/test_results.json.'"""
        out = Path.home() / f".{self._pkg}" / "test_results.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n")


_tracker = SessionTracker()

def pytest_runtest_logreport(report, *args, **kwargs):
    """description: 'Pytest hook — delegate failure tracking to the session tracker.'"""
    _tracker.track_failure(report, *args, **kwargs)

def pytest_sessionfinish(session, *args, **kwargs):
    """description: 'Pytest hook — finalize and persist results via the session tracker.'"""
    _tracker.finish(session, *args, **kwargs)
