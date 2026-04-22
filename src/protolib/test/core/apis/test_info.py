"""
script_path: src/protolib/test/core/apis/test_info.py
purpose: "Integration tests for app/apis/info.py — package information API."
update_rules: "Append scenarios. Never remove existing tests."
"""
import unittest
from protolib.core.apis.info import (
    collect_infos, venv_is_active, user_info, server_info,
)


class TestCollectInfos(unittest.TestCase):
    """collect_infos: accumulate info messages."""

    def test_init_clears_list(self, *args, **kwargs):
        collect_infos("first")
        collect_infos("", init=True)
        result = collect_infos("")
        assert len(result) == 0

    def test_appends_message(self, *args, **kwargs):
        collect_infos("", init=True)
        collect_infos("hello")
        result = collect_infos("")
        assert "hello" in result

    def test_returns_list(self, *args, **kwargs):
        result = collect_infos("test", init=True)
        assert isinstance(result, list)


class TestVenvIsActive(unittest.TestCase):
    """venv_is_active: detect .venv in executable path."""

    def test_detects_venv(self, *args, **kwargs):
        assert venv_is_active("/home/user/project/.venv/bin/python") is True

    def test_no_venv(self, *args, **kwargs):
        assert venv_is_active("/usr/bin/python3") is False


class TestUserInfo(unittest.TestCase):
    """user_info: collect user section header."""

    def test_adds_to_infos(self, *args, **kwargs):
        collect_infos("", init=True)
        user_info()
        result = collect_infos("")
        assert len(result) > 0


class TestServerInfo(unittest.TestCase):
    """server_info: collect server section."""

    def test_adds_to_infos(self, *args, **kwargs):
        collect_infos("", init=True)
        server_info()
        result = collect_infos("")
        assert len(result) > 0


if __name__ == '__main__':
    unittest.main()
