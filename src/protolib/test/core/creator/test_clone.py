"""
script_path: src/protolib/test/core/creator/test_clone.py
description: >-
  Runs integration tests for the core creator clone module, covering CloneParams, Cloner,
  and Validator. Verifies text replacement mappings, file rename rules, and pre-flight validation
  logic for ports and Python versions. Ensures post-flight gate execution behaves correctly
  based on installation flags.
tags:
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import os
import unittest
from unittest import mock

import protolib.core.settings as sts
from protolib.core.creator.clone import CloneParams, Cloner, Validator, clone_info


class TestCloneParams(unittest.TestCase):
    """CloneParams.text_repls and file_rules: build replacement and rename mappings."""

    def _build(self, *args, **kwargs):
        old = {"pr_name": "protolib", "pg_name": "protolib", "alias": "proto", "port": 9001}
        new = {"pr_name": "mylib", "pg_name": "mypkg", "alias": "my", "port": 9006}
        new.update(kwargs)
        return CloneParams(old=old, new=new)

    def test_basic_text_repls(self, *args, **kwargs):
        # Old pr_name == pg_name == "protolib"; pg_name wins (dict dedupe, last insertion).
        repls = self._build().text_repls()
        self.assertEqual(repls["protolib"], "mypkg")
        self.assertEqual(repls["proto"], "my")

    def test_case_variants(self, *args, **kwargs):
        repls = self._build().text_repls()
        self.assertEqual(repls["PROTOLIB"], "MYPKG")
        self.assertEqual(repls["Protolib"], "Mypkg")

    def test_none_alias_skipped(self, *args, **kwargs):
        repls = self._build(alias=None).text_repls()
        self.assertIn("protolib", repls)
        self.assertNotIn("proto", repls)

    def test_port_in_repls(self, *args, **kwargs):
        repls = self._build().text_repls()
        self.assertEqual(repls["9001"], "9006")

    def test_file_rules(self, *args, **kwargs):
        rules = self._build().file_rules()
        # pg_name wins over pr_name for the shared 'protolib' key.
        self.assertEqual(rules, {"protolib": "mypkg", "proto": "my"})

    def test_file_rules_no_alias(self, *args, **kwargs):
        rules = self._build(alias=None).file_rules()
        self.assertNotIn("proto", rules)

    def test_from_settings(self, *args, **kwargs):
        class _Stub:
            project_name = "protolib"
            package_name = "protolib"
            alias = "proto"
            port = 9001
        p = CloneParams.from_settings(
            _Stub(), new_pr_name="newlib", new_pg_name="newpkg",
            new_alias="new", new_port=9010,
        )
        self.assertEqual(p.text_repls()["protolib"], "newpkg")
        self.assertEqual(p.text_repls()["9001"], "9010")


class TestValidator(unittest.TestCase):
    """Validator.check: port + python version pre-flight checks."""

    def test_missing_port_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit): Validator().check(port=None)

    def test_invalid_port_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit): Validator().check(port=99999)

    def test_valid_port_passes(self, *args, **kwargs):
        Validator().check(port=9006)

    def test_install_without_py_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit):
            Validator().check(port=9006, install=True, py_version=None)

    def test_invalid_py_format_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit):
            Validator().check(port=9006, py_version="not.a.version")

    def test_short_alias_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit):
            Validator().check(port=9006, new_alias="ap")

    def test_valid_alias_passes(self, *args, **kwargs):
        Validator().check(port=9006, new_alias="pro")

    def test_none_alias_passes(self, *args, **kwargs):
        Validator().check(port=9006, new_alias=None)


class TestCloneInfo(unittest.TestCase):
    """clone_info: module function returns rendered usage banner."""

    def test_returns_string(self, *args, **kwargs):
        info = clone_info()
        self.assertIsInstance(info, str)
        self.assertIn("proto clone", info)


class TestPostFlight(unittest.TestCase):
    """Cloner._post_gate: runs pytest in new clone when install=True; skips when False."""

    def setUp(self, *args, **kwargs):
        self.cloner = Cloner("/src", verbose=0, source_settings=mock.Mock())

    def test_runs_gate_when_install_true(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.clone.run_gate") as m:
            self.cloner._post_gate("/new/path", install=True)
        m.assert_called_once_with("/new/path")

    def test_skips_gate_when_install_false(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.clone.run_gate") as m:
            self.cloner._post_gate("/new/path", install=False)
        m.assert_not_called()

    def test_gate_failure_aborts(self, *args, **kwargs):
        with mock.patch("protolib.core.creator.clone.run_gate",
                        side_effect=SystemExit(2)):
            with self.assertRaises(SystemExit) as ctx:
                self.cloner._post_gate("/new/path", install=True)
        self.assertEqual(ctx.exception.code, 2)


class TestBlueprintScaffold(unittest.TestCase):
    """Cloner.scaffold_blueprint: every clone starts flipped on the bpm lane."""

    def test_scaffold_creates_blueprint_tree(self, *args, **kwargs):
        import tempfile
        cloner = Cloner("/src", verbose=0, source_settings=mock.Mock())
        with tempfile.TemporaryDirectory() as project_path:
            cloner.scaffold_blueprint(project_path)
            expected = os.path.join(project_path, "blueprint", "experiments", "prototype")
            self.assertTrue(os.path.isdir(expected))
            # idempotent — a re-run on an existing tree must not raise
            cloner.scaffold_blueprint(project_path)

    def test_source_blueprint_never_copied(self, *args, **kwargs):
        # the copy ignores source blueprint dirs; only the fresh scaffold may exist
        self.assertIn("blueprint", sts.ignore_dirs)
        self.assertEqual(sts.blueprint_scaffold_dirs,
                         [os.path.join("blueprint", "experiments", "prototype")])


if __name__ == '__main__':
    unittest.main()
