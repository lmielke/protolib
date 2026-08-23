"""
script_path: src/protolib/test/core/creator/test_python_versions.py
description: >-
  Runs integration tests for the PythonVersions class to verify Python version discovery logic.
  Validates command execution, pyenv detection, PATH scanning, and uv installation lookup.
  Ensures version sorting and info string formatting meet expected invariants for the creator
  module.
tags:
- infra
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import os, unittest
import protolib.test.core.helpers as testhelper
from protolib.core.creator.python_versions import PythonVersions


class TestRunCmd(unittest.TestCase):
    """PythonVersions.run_cmd: execute shell command and return stdout or empty string."""

    def test_valid_command(self, *args, **kwargs):
        self.assertEqual(PythonVersions.run_cmd(cmd=["echo", "hello"]), "hello")

    def test_invalid_command_returns_empty(self, *args, **kwargs):
        self.assertEqual(PythonVersions.run_cmd(cmd=["nonexistent_binary_xyz_123"]), "")


class TestFromPyenv(unittest.TestCase):
    """PythonVersions.from_pyenv: discover pyenv-managed python executables."""

    @testhelper.test_setup(temp_file=None)
    def test_finds_pyenv_versions(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_home = os.environ.get("HOME", "")
        bin_dir = os.path.join(tmpdir, ".pyenv", "versions", "3.11.5", "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "python3"), "w") as f: f.write("#!/bin/sh\n")
        os.environ["HOME"] = tmpdir
        try:
            self.assertIn(os.path.join(bin_dir, "python3"), PythonVersions.from_pyenv())
        finally:
            os.environ["HOME"] = orig_home

    @testhelper.test_setup(temp_file=None)
    def test_empty_when_no_pyenv(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_home = os.environ.get("HOME", "")
        os.environ["HOME"] = tmpdir
        try:
            self.assertEqual(PythonVersions.from_pyenv(), set())
        finally:
            os.environ["HOME"] = orig_home


class TestFromPath(unittest.TestCase):
    """PythonVersions.from_path: discover python executables on PATH."""

    @testhelper.test_setup(temp_file=None)
    def test_finds_python3_on_path(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_path = os.environ.get("PATH", "")
        with open(os.path.join(tmpdir, "python3"), "w") as f: f.write("#!/bin/sh\n")
        os.environ["PATH"] = tmpdir
        try:
            self.assertIn(os.path.abspath(os.path.join(tmpdir, "python3")),
                          PythonVersions.from_path())
        finally:
            os.environ["PATH"] = orig_path

    @testhelper.test_setup(temp_file=None)
    def test_empty_when_no_match(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_path = os.environ.get("PATH", "")
        empty_dir = os.path.join(tmpdir, "empty")
        os.makedirs(empty_dir)
        os.environ["PATH"] = empty_dir
        try:
            self.assertEqual(PythonVersions.from_path(), set())
        finally:
            os.environ["PATH"] = orig_path


class TestFromUv(unittest.TestCase):
    """PythonVersions.from_uv: discover uv-managed python installs."""

    @testhelper.test_setup(temp_file=None)
    def test_finds_uv_python(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_home = os.environ.get("HOME", "")
        bin_dir = os.path.join(tmpdir, ".local", "share", "uv", "python",
                               "cpython-3.12.0", "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "python3"), "w") as f: f.write("#!/bin/sh\n")
        os.environ["HOME"] = tmpdir
        try:
            self.assertIn(os.path.join(bin_dir, "python3"), PythonVersions.from_uv())
        finally:
            os.environ["HOME"] = orig_home

    @testhelper.test_setup(temp_file=None)
    def test_empty_when_no_uv_dir(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        orig_home = os.environ.get("HOME", "")
        os.environ["HOME"] = tmpdir
        try:
            self.assertEqual(PythonVersions.from_uv(), set())
        finally:
            os.environ["HOME"] = orig_home


class TestAllVersions(unittest.TestCase):
    """PythonVersions.all/full/latest: aggregate, sort, and pick versions."""

    def test_all_returns_list(self, *args, **kwargs):
        self.assertIsInstance(PythonVersions().all(), list)

    def test_versions_are_sorted(self, *args, **kwargs):
        result = PythonVersions().all()
        if len(result) < 2: return
        tuples = [tuple(int(x) for x in v.split(".")) for v in result]
        self.assertEqual(tuples, sorted(tuples))

    def test_contains_short_and_full(self, *args, **kwargs):
        result = PythonVersions().all()
        full = [v for v in result if v.count(".") == 2]
        short = [v for v in result if v.count(".") == 1]
        if full: self.assertTrue(len(short) > 0)

    def test_latest_is_in_full(self, *args, **kwargs):
        pv = PythonVersions()
        latest = pv.latest()
        if latest is not None: self.assertIn(latest, pv.full())


class TestVersionOf(unittest.TestCase):
    """PythonVersions.version_of and _VER_RX: parse Python --version output."""

    def test_version_regex(self, *args, **kwargs):
        m = PythonVersions._VER_RX.search("Python 3.12.4")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "3.12.4")

    def test_no_match(self, *args, **kwargs):
        self.assertIsNone(PythonVersions._VER_RX.search("not a version"))


class TestInfoString(unittest.TestCase):
    """PythonVersions.info_string: rendered usage banner."""

    def test_contains_proto_clone(self, *args, **kwargs):
        self.assertIn("proto clone", PythonVersions().info_string())

    def test_contains_available_section(self, *args, **kwargs):
        self.assertIn("Available Python versions", PythonVersions().info_string())


if __name__ == '__main__':
    unittest.main()
