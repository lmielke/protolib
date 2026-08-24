"""
script_path: src/protolib/core/creator/gate.py
description: >-
  Executes the source package test suite via uv and pytest as a pre-flight check before clone
  or sync operations. Reads the failed test count from a local JSON results file and aborts
  the process if any test fails or the runner errors. Serves as a shared gate for the clone
  and sync modules.
tags:
- cli
- hook
- testing
"""
import json, subprocess, sys
from pathlib import Path

from protolib.core.creator.clones import _pkg_name


class Gate:
    """
    description: Run source package test suite and read pass/fail from test_results.json.
    """

    def __init__(self, *args, project_dir, **kwargs):
        """description: Bind to a source project_dir; resolve package name up-front."""
        self.project_dir = Path(project_dir)
        self.pkg = _pkg_name(self.project_dir, *args, **kwargs)

    def run(self, *args, **kwargs) -> None:
        """description: Run pytest; abort on any failure. No-op if tests pass."""
        rc = self._run_pytest(*args, **kwargs)
        failed = self._read_failed(*args, **kwargs)
        if rc == 0 and failed == 0: return
        print(f"[gate] pytest rc={rc}, failed={failed} — aborting.")
        sys.exit(2)

    def _run_pytest(self, *args, **kwargs) -> int:
        """description: Run pytest in project_dir; return process exit code."""
        cmd = ["uv", "run", "pytest", f"src/{self.pkg}/test/", "-q"]
        return subprocess.run(cmd, cwd=str(self.project_dir)).returncode

    def _read_failed(self, *args, **kwargs) -> int:
        """description: Read failed count from ~/.{pkg}/test_results.json; 1 if missing."""
        results = Path.home() / f".{self.pkg}" / "test_results.json"
        if not results.exists(): return 1
        return json.loads(results.read_text()).get("failed", 1)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return f"Gate(project_dir={str(self.project_dir)!r})"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short text showing bound package and project path.'"""
        return f"Gate(pkg={self.pkg}, dir={self.project_dir})"

def run_gate(project_dir, *args, **kwargs) -> None:
    """description: Module-level entry point for clone.py and sync.py."""
    Gate(project_dir=project_dir).run()


if __name__ == "__main__":
    import protolib.core.settings as sts
    run_gate(sts.project_dir)
