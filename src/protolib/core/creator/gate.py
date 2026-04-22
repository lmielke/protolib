"""
script_path: src/protolib/core/creator/gate.py
purpose: Run the source package test suite as a pre-flight gate before clone/sync.
description: |-
  Runs `uv run pytest src/<pkg>/test/ -q` in the source project dir. Reads
  ~/.{pkg}/test_results.json (written by conftest.py) and aborts if any test
  failed or if pytest itself errored. Shared by clone.py and sync.py.
"""
import json, subprocess, sys
from pathlib import Path

from protolib.core.creator.clones import _pkg_name


class Gate:
    """
    purpose: Run source package test suite and read pass/fail from test_results.json.
    """

    def __init__(self, *args, project_dir, **kwargs):
        """purpose: Bind to a source project_dir; resolve package name up-front."""
        self.project_dir = Path(project_dir)
        self.pkg = _pkg_name(self.project_dir)

    def run(self, *args, **kwargs) -> None:
        """purpose: Run pytest; abort on any failure. No-op if tests pass."""
        rc = self._run_pytest()
        failed = self._read_failed()
        if rc == 0 and failed == 0: return
        print(f"[gate] pytest rc={rc}, failed={failed} — aborting.")
        sys.exit(2)

    def _run_pytest(self, *args, **kwargs) -> int:
        """purpose: Run pytest in project_dir; return process exit code."""
        cmd = ["uv", "run", "pytest", f"src/{self.pkg}/test/", "-q"]
        return subprocess.run(cmd, cwd=str(self.project_dir)).returncode

    def _read_failed(self, *args, **kwargs) -> int:
        """purpose: Read failed count from ~/.{pkg}/test_results.json; 1 if missing."""
        results = Path.home() / f".{self.pkg}" / "test_results.json"
        if not results.exists(): return 1
        return json.loads(results.read_text()).get("failed", 1)

def run_gate(project_dir, *args, **kwargs) -> None:
    """purpose: Module-level entry point for clone.py and sync.py."""
    Gate(project_dir=project_dir).run()


if __name__ == "__main__":
    import protolib.core.settings as sts
    run_gate(sts.project_dir)
