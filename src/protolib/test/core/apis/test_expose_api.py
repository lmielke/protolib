"""
script_path: src/protolib/test/core/apis/test_expose_api.py
purpose: "Integration tests for app/apis/expose_api.py — API signature export."
update_rules: "Append scenarios. Never remove existing tests."
"""
import json, unittest
from protolib.core.apis.expose_api import main


class TestExposeApiMain(unittest.TestCase):
    """main: return API signatures as JSON."""

    def test_returns_json_string(self, *args, **kwargs):
        result = main()
        assert isinstance(result, str)
        data = json.loads(result)
        assert "id" in data
        assert "apis" in data

    def test_contains_info_api(self, *args, **kwargs):
        result = main()
        data = json.loads(result)
        assert "info" in data["apis"]


if __name__ == '__main__':
    unittest.main()
