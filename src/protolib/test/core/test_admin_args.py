"""
script_path: src/protolib/test/core/test_admin_args.py
description: >-
  Runs integration tests for the admin_args module to verify CLI argument parsing behavior.
  Validates that mk_args correctly dispatches subcommands like clone and sync with expected
  field values. Confirms that missing commands trigger a SystemExit. Consumed by the protolib
  test suite to ensure admin CLI stability.
tags:
- cli
- testing
"""
import sys
import unittest
from unittest.mock import patch

from protolib.core import admin_args


class TestMkArgs(unittest.TestCase):
    """mk_args dispatches subcommands with correct fields."""

    def _run(self, *args, argv: list, **kwargs):
        with patch.object(sys, "argv", ["proto-admin", *argv]):
            return admin_args.mk_args()

    def test_clone_parses(self, *args, **kwargs):
        ns = self._run(argv=["clone", "-n", "mypkg", "-t", "/tmp", "--port", "9010"])
        self.assertEqual(ns.command, "clone")
        self.assertEqual(ns.new_pg_name, "mypkg")
        self.assertEqual(ns.port, "9010")

    def test_sync_parses(self, *args, **kwargs):
        ns = self._run(argv=["sync"])
        self.assertEqual(ns.command, "sync")
        self.assertEqual(ns.verbose, 0)

    def test_sync_verbose(self, *args, **kwargs):
        ns = self._run(argv=["sync", "-v", "2"])
        self.assertEqual(ns.command, "sync")
        self.assertEqual(ns.verbose, 2)

    def test_missing_command_exits(self, *args, **kwargs):
        with self.assertRaises(SystemExit):
            self._run(argv=[])


if __name__ == "__main__":
    unittest.main()
