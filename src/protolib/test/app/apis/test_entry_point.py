"""
script_path: src/protolib/test/app/apis/test_entry_point.py
purpose: "Integration tests for app/apis/entry_point.py — example API."
update_rules: "Append scenarios. Never remove existing tests."
"""
import unittest


class TestEntryPoint(unittest.TestCase):
    """entry_point: example API wrapper."""

    def test_main_callable(self, *args, **kwargs):
        from protolib.app.apis.entry_point import main
        assert callable(main)


if __name__ == '__main__':
    unittest.main()
