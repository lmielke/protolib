"""
script_path: src/protolib/test/core/creator/test_clones.py
description: >-
  Runs integration tests for the Clones class and _pkg_name helper in core/creator/clones.py.
  Verifies add, remove, load, and deduplication behavior against a temporary clones.yml file.
  Also checks package name extraction from pyproject.toml with a dirname fallback. Consumed
  by the protolib test suite.
tags:
- parsing
- testing
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from protolib.core.creator.clones import Clones, _pkg_name


def _make_project(root: Path, name: str) -> Path:
    project = root / name
    (project / "src" / name).mkdir(parents=True)
    (project / "pyproject.toml").write_text(f'[project]\nname = "{name}"\n')
    return project


class TestClones(unittest.TestCase):
    """Clones: add/remove entries in clones.yml, load them back."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())
        self.clones = Clones(path=self.root / "clones.yml")

    def tearDown(self, *args, **kwargs):
        shutil.rmtree(self.root)

    def test_load_returns_empty_when_no_file(self, *args, **kwargs):
        self.assertEqual(self.clones.load(), [])

    def test_add_creates_entry(self, *args, **kwargs):
        project = _make_project(self.root, "mypkg")
        self.clones.add(str(project))
        entries = self.clones.load()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "mypkg")
        self.assertEqual(Path(entries[0]["path"]).resolve(), project.resolve())

    def test_add_deduplicates_by_path(self, *args, **kwargs):
        project = _make_project(self.root, "mypkg")
        self.clones.add(str(project))
        self.clones.add(str(project))
        self.assertEqual(len(self.clones.load()), 1)

    def test_add_multiple_clones(self, *args, **kwargs):
        self.clones.add(str(_make_project(self.root, "pkga")))
        self.clones.add(str(_make_project(self.root, "pkgb")))
        names = {e["name"] for e in self.clones.load()}
        self.assertEqual(names, {"pkga", "pkgb"})

    def test_add_updates_existing_entry(self, *args, **kwargs):
        project = _make_project(self.root, "mypkg")
        self.clones.add(str(project))
        ts_first = self.clones.load()[0]["cloned_at"]
        self.clones.add(str(project))
        ts_second = self.clones.load()[0]["cloned_at"]
        self.assertGreaterEqual(ts_second, ts_first)

    def test_remove_drops_entry(self, *args, **kwargs):
        project = _make_project(self.root, "mypkg")
        self.clones.add(str(project))
        self.clones.remove(str(project))
        self.assertEqual(self.clones.load(), [])

    def test_remove_unknown_path_is_noop(self, *args, **kwargs):
        project = _make_project(self.root, "mypkg")
        self.clones.add(str(project))
        self.clones.remove(str(self.root / "not_there"))
        self.assertEqual(len(self.clones.load()), 1)


class TestPkgName(unittest.TestCase):
    """_pkg_name: reads name from pyproject.toml."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self, *args, **kwargs):
        shutil.rmtree(self.root)

    def test_reads_package_name(self, *args, **kwargs):
        project = _make_project(self.root, "somepkg")
        self.assertEqual(_pkg_name(project), "somepkg")

    def test_falls_back_to_dirname_when_no_project_section(self, *args, **kwargs):
        project = self.root / "fallbackpkg"
        project.mkdir()
        (project / "pyproject.toml").write_text("[tool.uv]\n")
        self.assertEqual(_pkg_name(project), "fallbackpkg")


if __name__ == "__main__":
    unittest.main()
