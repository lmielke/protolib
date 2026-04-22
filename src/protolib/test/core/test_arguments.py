"""
script_path: src/protolib/test/core/test_arguments.py
purpose: "Integration tests for core/arguments.py — admin CLI argparse."
"""
import sys
import unittest
from unittest.mock import patch

from protolib.core import arguments as admin_args


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
