"""
script_path: src/protolib/test/core/apis/test_register.py
purpose: "Integration tests for app/apis/register.py — outbound registration."
update_rules: "Append scenarios. Never remove existing tests."
"""
import json, unittest
from protolib.core.apis.register import _do_register, main


class TestDoRegister(unittest.TestCase):
    """_do_register: one-shot registration attempt."""

    def test_returns_dict(self, *args, **kwargs):
        result = _do_register()
        assert isinstance(result, dict)
        assert "ok" in result
        assert "service_id" in result

    def test_unreachable_registry(self, *args, **kwargs):
        result = _do_register(registry_url="http://127.0.0.1:1")
        assert result["ok"] is False


class TestRegisterMain(unittest.TestCase):
    """main: register and return JSON output."""

    def test_returns_json_string(self, *args, **kwargs):
        result = main()
        assert isinstance(result, str)
        data = json.loads(result)
        assert "ok" in data


if __name__ == '__main__':
    unittest.main()
