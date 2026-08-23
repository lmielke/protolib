"""
script_path: src/protolib/test/app/apis/test_entry_point.py
description: >-
  Verifies the entry point API wrapper by asserting that the main function is callable. Serves
  as an integration test baseline for the example API module. Follows append-only update rules
  to preserve existing test scenarios.
tags:
- api
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import unittest


class TestEntryPoint(unittest.TestCase):
    """entry_point: example API wrapper."""

    def test_main_callable(self, *args, **kwargs):
        from protolib.app.apis.entry_point import main
        assert callable(main)


if __name__ == '__main__':
    unittest.main()
