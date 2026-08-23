"""
script_path: src/protolib/test/core/creator/test_gate.py
description: >-
  Runs integration tests for the core creator gate module, verifying pre-flight validation
  logic. Checks that the gate passes on green pytest runs and aborts with exit code 2 on failures
  or missing results. Validates that the gate invokes uv run pytest in the correct project
  directory. Consumed by the protolib test suite to ensure gate behavior remains stable.
tags:
- governance
- testing
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from protolib.core.creator.gate import Gate, run_gate


class TestGate(unittest.TestCase):
    """Gate.run: passes on green pytest + failed=0; aborts otherwise."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "pyproject.toml").write_text('[project]\nname = "mypkg"\n')
        self.home = self.root / "home"
        (self.home / ".mypkg").mkdir(parents=True)
        self.results = self.home / ".mypkg" / "test_results.json"
        self._home_patch = mock.patch("protolib.core.creator.gate.Path.home",
                                      return_value=self.home)
        self._home_patch.start()

    def tearDown(self, *args, **kwargs):
        self._home_patch.stop()
        import shutil
        shutil.rmtree(self.root)

    def _run_rc(self, rc: int, *args, **kwargs):
        """description: Build a subprocess.run mock that returns the given rc."""
        return mock.Mock(returncode=rc)

    def test_gate_passes_on_green(self, *args, **kwargs):
        self.results.write_text(json.dumps({"failed": 0}))
        with mock.patch("protolib.core.creator.gate.subprocess.run",
                        return_value=self._run_rc(0)):
            run_gate(self.project)

    def test_gate_aborts_on_pytest_rc_nonzero(self, *args, **kwargs):
        self.results.write_text(json.dumps({"failed": 0}))
        with mock.patch("protolib.core.creator.gate.subprocess.run",
                        return_value=self._run_rc(1)):
            with self.assertRaises(SystemExit) as ctx:
                run_gate(self.project)
        self.assertEqual(ctx.exception.code, 2)

    def test_gate_aborts_on_failed_count(self, *args, **kwargs):
        self.results.write_text(json.dumps({"failed": 3}))
        with mock.patch("protolib.core.creator.gate.subprocess.run",
                        return_value=self._run_rc(0)):
            with self.assertRaises(SystemExit) as ctx:
                run_gate(self.project)
        self.assertEqual(ctx.exception.code, 2)

    def test_gate_aborts_when_results_missing(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.gate.subprocess.run",
                        return_value=self._run_rc(0)):
            with self.assertRaises(SystemExit) as ctx:
                run_gate(self.project)
        self.assertEqual(ctx.exception.code, 2)

    def test_gate_invokes_uv_pytest_in_project_dir(self, *args, **kwargs):
        self.results.write_text(json.dumps({"failed": 0}))
        with mock.patch("protolib.core.creator.gate.subprocess.run",
                        return_value=self._run_rc(0)) as m:
            run_gate(self.project)
        args_, kwargs_ = m.call_args
        self.assertEqual(args_[0][:3], ["uv", "run", "pytest"])
        self.assertEqual(kwargs_["cwd"], str(self.project))


if __name__ == "__main__":
    unittest.main()
