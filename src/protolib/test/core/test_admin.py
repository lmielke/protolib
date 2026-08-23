"""
script_path: src/protolib/test/core/test_admin.py
description: >-
  Verifies AdminDispatcher routing logic by asserting that known commands resolve to their
  specific handler methods. Confirms that unknown commands trigger a SystemExit and that the
  dispatch method invokes the resolved handler. Serves as the integration test suite for the
  core admin module.
tags:
- cli
- testing
"""
import sys
import unittest
from unittest.mock import patch

from protolib.core.admin import AdminDispatcher


class TestAdminDispatcher(unittest.TestCase):
    """AdminDispatcher._handler returns the correct handler per command."""

    def test_clone_resolves(self, *args, **kwargs):
        d = AdminDispatcher()
        handler = d._handler(command="clone")
        self.assertEqual(handler, d._clone)

    def test_sync_resolves(self, *args, **kwargs):
        d = AdminDispatcher()
        handler = d._handler(command="sync")
        self.assertEqual(handler, d._sync)

    def test_unknown_command_exits(self, *args, **kwargs):
        d = AdminDispatcher()
        with self.assertRaises(SystemExit):
            d._handler(command="bogus")

    def test_dispatch_calls_handler(self, *args, **kwargs):
        d = AdminDispatcher()
        with patch.object(d, "_clone") as mock_clone:
            d.dispatch(command="clone", verbose=0)
            mock_clone.assert_called_once()


if __name__ == "__main__":
    unittest.main()
