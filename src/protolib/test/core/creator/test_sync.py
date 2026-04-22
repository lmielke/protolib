"""
script_path: src/protolib/test/core/creator/test_sync.py
purpose: "Integration tests for core/creator/sync.py — upstream-to-target framework sync."
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


import yaml
from datetime import datetime

from protolib.core.creator.sync import (Synchronizer, _sync_to_clone,
                                         _transform_target, _trigger_child_sync,
                                         _write_sync_log)


class TestSynchronizer(unittest.TestCase):
    """Synchronizer.sync: copy scoped files from source to target."""

    def setUp(self, *args, **kwargs):
        self.root = tempfile.mkdtemp()
        self.source = os.path.join(self.root, "source")
        self.target = os.path.join(self.root, "target")
        self._mk(self.source, rel="core/settings.py", body="port = 9001\n")
        self._mk(self.source, rel="helpers/printing.py", body="def log(): pass\n")
        self._mk(self.source, rel="app/protopy.py", body="# app-only\n")
        self._mk(self.target, rel="core/settings.py", body="port = 9001\n")
        self._mk(self.target, rel="helpers/printing.py", body="def log(): pass\n")

    def tearDown(self, *args, **kwargs):
        shutil.rmtree(self.root)

    def _mk(self, base, *args, rel: str, body: str, **kwargs):
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(body)

    def _read(self, base, *args, rel: str, **kwargs):
        return open(os.path.join(base, rel)).read()

    def test_syncs_changed_files(self, *args, **kwargs):
        self._mk(self.source, rel="core/settings.py", body="port = 9999\n")
        Synchronizer(source_dir=self.source, target_dir=self.target).sync()
        self.assertIn("9999", self._read(self.target, rel="core/settings.py"))

    def test_app_files_are_not_synced(self, *args, **kwargs):
        Synchronizer(source_dir=self.source, target_dir=self.target).sync()
        self.assertFalse(os.path.exists(os.path.join(self.target, "app/protopy.py")))

    def test_added_source_file_is_copied(self, *args, **kwargs):
        self._mk(self.source, rel="core/new_module.py", body="# added\n")
        Synchronizer(source_dir=self.source, target_dir=self.target).sync()
        self.assertTrue(os.path.exists(os.path.join(self.target, "core/new_module.py")))

    def test_report_lists_copied_files(self, *args, **kwargs):
        self._mk(self.source, rel="core/new_module.py", body="# added\n")
        report = Synchronizer(source_dir=self.source, target_dir=self.target).sync()
        self.assertIn("core/new_module.py", report["copied"])

    def test_helpers_are_synced(self, *args, **kwargs):
        self._mk(self.source, rel="helpers/printing.py", body="def log(): return 1\n")
        Synchronizer(source_dir=self.source, target_dir=self.target).sync()
        self.assertIn("return 1", self._read(self.target, rel="helpers/printing.py"))


class TestSyncToClone(unittest.TestCase):
    """_sync_to_clone: propagates core/ changes from source to a registered clone entry."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())
        self.source = self.root / "source"
        clone_root = self.root / "myclone"
        self.target = clone_root / "src" / "mypkg"
        for p in (self.source / "core", self.source / "helpers", self.target / "core"):
            p.mkdir(parents=True)
        (self.source / "core" / "settings.py").write_text("port = 9001\n")
        (self.target / "core" / "settings.py").write_text("port = 9001\n")
        (clone_root / "pyproject.toml").write_text('[project]\nname = "mypkg"\n')
        self.entry = {"path": str(clone_root), "name": "mypkg"}
        self._orig_pkg_dir = __import__("protolib.core.settings", fromlist=["package_dir"]).package_dir
        import protolib.core.settings as s
        s.package_dir = str(self.source)

    def tearDown(self, *args, **kwargs):
        import protolib.core.settings as s
        s.package_dir = self._orig_pkg_dir
        shutil.rmtree(self.root)

    def test_sync_to_clone_copies_changed_file(self, *args, **kwargs):
        (self.source / "core" / "settings.py").write_text("port = 9999\n")
        _sync_to_clone(self.entry, verbose=0)
        self.assertIn("9999", (self.target / "core" / "settings.py").read_text())

    def test_sync_to_clone_returns_copied_list(self, *args, **kwargs):
        (self.source / "core" / "new_module.py").write_text("# new\n")
        report = _sync_to_clone(self.entry, verbose=0)
        self.assertIn("core/new_module.py", report["copied"])


class TestWriteSyncLog(unittest.TestCase):
    """_write_sync_log: writes ~/.{pkg}/sync_log.yaml after each push."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())
        self._home_patch = mock.patch("protolib.core.creator.sync.Path.home",
                                      return_value=self.root)
        self._home_patch.start()
        self.entry = {"path": "/tmp/myclone", "name": "myclone"}
        self.log = self.root / ".myclone" / "sync_log.yaml"

    def tearDown(self, *args, **kwargs):
        self._home_patch.stop()
        shutil.rmtree(self.root)

    def test_sync_log_file_created(self, *args, **kwargs):
        _write_sync_log(self.entry, ["core/settings.py"])
        self.assertTrue(self.log.exists())

    def test_sync_log_timestamp_is_iso(self, *args, **kwargs):
        _write_sync_log(self.entry, ["core/settings.py"])
        data = yaml.safe_load(self.log.read_text())
        datetime.fromisoformat(data["last_synced"])  # raises if malformed

    def test_sync_log_files_sorted(self, *args, **kwargs):
        _write_sync_log(self.entry, ["core/z.py", "core/a.py", "helpers/m.py"])
        data = yaml.safe_load(self.log.read_text())
        self.assertEqual(data["files"], ["core/a.py", "core/z.py", "helpers/m.py"])

    def test_sync_log_synced_by_source(self, *args, **kwargs):
        _write_sync_log(self.entry, [])
        data = yaml.safe_load(self.log.read_text())
        self.assertEqual(data["synced_by"], "protolib")


class TestTriggerChildSync(unittest.TestCase):
    """_trigger_child_sync: runs `uv run proto-admin sync` inside the clone path."""

    def setUp(self, *args, **kwargs):
        self.entry = {"path": "/tmp/myclone", "name": "myclone"}

    def test_invokes_uv_proto_admin_sync(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.sync.subprocess.run") as m:
            _trigger_child_sync(self.entry)
        args_, _ = m.call_args
        self.assertEqual(args_[0], ["uv", "run", "proto-admin", "sync"])

    def test_subprocess_cwd_is_clone_path(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.sync.subprocess.run") as m:
            _trigger_child_sync(self.entry)
        _, kwargs_ = m.call_args
        self.assertEqual(kwargs_["cwd"], "/tmp/myclone")

    def test_uses_target_alias_when_settings_present(self, *args, **kwargs):
        root = Path(tempfile.mkdtemp())
        try:
            pkg = root / "proj" / "src" / "mypkg" / "app"
            pkg.mkdir(parents=True)
            (pkg / "settings.py").write_text('alias = "tcl"\n')
            entry = {"path": str(root / "proj"), "name": "mypkg"}
            with mock.patch("protolib.core.creator.sync.subprocess.run") as m:
                _trigger_child_sync(entry)
            args_, _ = m.call_args
            self.assertEqual(args_[0], ["uv", "run", "tcl-admin", "sync"])
        finally:
            shutil.rmtree(root)


class TestTransformTarget(unittest.TestCase):
    """_transform_target: rewrite caller→target identity in synced scopes."""

    def setUp(self, *args, **kwargs):
        self.root = Path(tempfile.mkdtemp())
        clone_root = self.root / "testproj"
        pkg_dir = clone_root / "src" / "testpkg"
        (pkg_dir / "app").mkdir(parents=True)
        (pkg_dir / "core").mkdir()
        (pkg_dir / "helpers").mkdir()
        (pkg_dir / "app" / "settings.py").write_text(
            'project_name = "testproj"\npackage_name = "testpkg"\n'
            'alias = "tpk"\nport = 9777\n')
        (pkg_dir / "core" / "x.py").write_text(
            'import protolib.core as c\nPORT = 9001\nfrom proto import q\n')
        (pkg_dir / "helpers" / "h.py").write_text(
            '# protolib helper; Protolib is the source.\n')
        (pkg_dir / "app" / "y.py").write_text('import protolib.app\n')
        self.entry = {"path": str(clone_root), "name": "testpkg"}

    def tearDown(self, *args, **kwargs):
        shutil.rmtree(self.root)

    def _read(self, rel: str) -> str:
        return (self.root / "testproj" / "src" / "testpkg" / rel).read_text()

    def test_core_pkg_name_rewritten(self, *args, **kwargs):
        _transform_target(entry=self.entry, verbose=0)
        txt = self._read("core/x.py")
        self.assertIn("testpkg.core", txt)
        self.assertNotIn("protolib.core", txt)

    def test_core_alias_rewritten(self, *args, **kwargs):
        _transform_target(entry=self.entry, verbose=0)
        self.assertIn("from tpk import", self._read("core/x.py"))

    def test_core_port_rewritten(self, *args, **kwargs):
        _transform_target(entry=self.entry, verbose=0)
        txt = self._read("core/x.py")
        self.assertIn("9777", txt)
        self.assertNotIn("9001", txt)

    def test_helpers_rewritten(self, *args, **kwargs):
        _transform_target(entry=self.entry, verbose=0)
        txt = self._read("helpers/h.py")
        self.assertIn("testpkg helper", txt)
        self.assertIn("Testpkg", txt)

    def test_app_not_rewritten(self, *args, **kwargs):
        _transform_target(entry=self.entry, verbose=0)
        self.assertIn("protolib.app", self._read("app/y.py"))

    def test_missing_app_settings_noop(self, *args, **kwargs):
        entry = {"path": str(self.root / "noapp"), "name": "x"}
        (self.root / "noapp" / "src" / "x" / "core").mkdir(parents=True)
        _transform_target(entry=entry, verbose=0)  # must not raise


if __name__ == "__main__":
    unittest.main()
