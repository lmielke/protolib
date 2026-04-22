"""
script_path: conftest.py
purpose: Write test_results.json to ~/.<package>/ after every pytest session.
description: Excludes test_governance.py — those are tracked in the governance column separately.
"""
import json, tomllib
from datetime import datetime
from pathlib import Path

_failed_nodeids = set()
_EXCLUDED = "test_governance.py"
_ROOT = Path(__file__).parent
_PKG = tomllib.loads((_ROOT / "pyproject.toml").read_text()).get("project", {}).get("name", "protolib")


def pytest_runtest_logreport(report, *args, **kwargs):
    if report.failed and report.when == "call" and _EXCLUDED not in report.nodeid:
        _failed_nodeids.add(report.nodeid)


def pytest_sessionfinish(session, exitstatus, *args, **kwargs):
    items = [i for i in (session.items or []) if _EXCLUDED not in i.nodeid]
    total = len(items)
    failed = len(_failed_nodeids)
    out = Path.home() / f".{_PKG}" / "test_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "tests": total,
        "passed": total - failed,
        "failed": failed,
        "failures": sorted(_failed_nodeids),
        "timestamp": datetime.now().isoformat(timespec='seconds'),
    }, indent=2) + "\n")
