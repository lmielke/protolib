"""
script_path: src/protolib/test/core/apis/test_server.py
description: >-
  Runs integration tests for the core API server module, covering HTTP dispatch and parameter
  handling. Validates query string casting, parameter building, and content negotiation logic.
  Verifies API loading rules and JSON serialization behavior. Consumed by the protolib test
  suite to ensure server stability.
tags:
- cli
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import unittest
import protolib.core.settings as sts
from protolib.core.apis.server import (
    _build_params, _cast_value, _strip_ansi,
    ProtoControlHandler,
)


def _stub_handler(path, headers, *args, **kwargs):
    h = ProtoControlHandler.__new__(ProtoControlHandler)
    h.path, h.headers = path, headers
    return h


class TestCastValue(unittest.TestCase):
    """_cast_value: parse query string values to typed Python values."""

    def test_digit_to_int(self, *args, **kwargs):
        assert _cast_value("42") == 42

    def test_true_string(self, *args, **kwargs):
        assert _cast_value("true") is True

    def test_false_string(self, *args, **kwargs):
        assert _cast_value("False") is False

    def test_plain_string(self, *args, **kwargs):
        assert _cast_value("hello") == "hello"


class TestBuildParams(unittest.TestCase):
    """_build_params: convert parsed query dict to typed params."""

    def test_basic_query(self, *args, **kwargs):
        qp = {"verbose": ["1"], "name": ["test"]}
        result = _build_params(qp)
        assert result["verbose"] == 1
        assert result["name"] == "test"

    def test_infos_kept_as_list(self, *args, **kwargs):
        qp = {"infos": ["package", "python"]}
        result = _build_params(qp)
        assert result["infos"] == ["package", "python"]

    def test_defaults_verbose_zero(self, *args, **kwargs):
        result = _build_params({})
        assert result["verbose"] == 0

    def test_bool_conversion(self, *args, **kwargs):
        qp = {"flag": ["true"]}
        result = _build_params(qp)
        assert result["flag"] is True

    def test_empty_value_skipped(self, *args, **kwargs):
        qp = {"key": []}
        result = _build_params(qp)
        assert "key" not in result

    def test_format_key_stripped(self, *args, **kwargs):
        qp = {"format": ["json"], "name": ["test"]}
        result = _build_params(qp)
        assert "format" not in result
        assert result["name"] == "test"


class TestNegotiate(unittest.TestCase):
    """_negotiate: choose JSON or HTML from ?format override and Accept header."""

    def test_accept_html(self, *args, **kwargs):
        h = _stub_handler("/info/", {"Accept": "text/html"})
        assert h._negotiate() == "html"

    def test_accept_json(self, *args, **kwargs):
        h = _stub_handler("/info/", {"Accept": "application/json"})
        assert h._negotiate() == "json"

    def test_format_override_beats_accept(self, *args, **kwargs):
        h = _stub_handler("/info/?format=json", {"Accept": "text/html"})
        assert h._negotiate() == "json"

    def test_default_is_json(self, *args, **kwargs):
        h = _stub_handler("/info/", {})
        assert h._negotiate() == "json"


class TestAsJson(unittest.TestCase):
    """_as_json: wrap API output as a JSON-serializable object."""

    def test_dict_passthrough(self, *args, **kwargs):
        h = _stub_handler("/", {})
        assert h._as_json({"a": 1}) == {"a": 1}

    def test_list_passthrough(self, *args, **kwargs):
        h = _stub_handler("/", {})
        assert h._as_json([1, 2]) == [1, 2]

    def test_string_wrapped_and_stripped(self, *args, **kwargs):
        h = _stub_handler("/", {})
        assert h._as_json("\x1b[31mhi\x1b[0m") == {"result": "hi"}


class TestStripAnsi(unittest.TestCase):
    """_strip_ansi: remove ANSI color escape codes."""

    def test_removes_color_codes(self, *args, **kwargs):
        assert _strip_ansi("\x1b[1;32mok\x1b[0m") == "ok"

    def test_plain_text_unchanged(self, *args, **kwargs):
        assert _strip_ansi("plain") == "plain"


class TestLoadApis(unittest.TestCase):
    """ProtoControlHandler.load_apis: discover API modules."""

    def test_loads_apis(self, *args, **kwargs):
        ProtoControlHandler.load_apis()
        apis = ProtoControlHandler.available_apis
        assert isinstance(apis, dict)
        assert len(apis) > 0

    def test_does_not_load_self(self, *args, **kwargs):
        ProtoControlHandler.load_apis()
        assert "server" not in ProtoControlHandler.available_apis

    def test_all_apis_have_main(self, *args, **kwargs):
        ProtoControlHandler.load_apis()
        for name, mod in ProtoControlHandler.available_apis.items():
            assert hasattr(mod, "main"), f"API '{name}' missing main()"


class TestTryLoadApi(unittest.TestCase):
    """_try_load_api: filter and import individual API files."""

    def test_skips_private_files(self, *args, **kwargs):
        result = ProtoControlHandler._try_load_api("_private.py", "server", pkg_prefix=f"{sts.package_name}.core.apis")
        assert result is None

    def test_skips_non_python(self, *args, **kwargs):
        result = ProtoControlHandler._try_load_api("readme.md", "server", pkg_prefix=f"{sts.package_name}.core.apis")
        assert result is None

    def test_skips_self(self, *args, **kwargs):
        result = ProtoControlHandler._try_load_api("server.py", "server", pkg_prefix=f"{sts.package_name}.core.apis")
        assert result is None

    def test_loads_valid_api(self, *args, **kwargs):
        result = ProtoControlHandler._try_load_api("info.py", "server", pkg_prefix=f"{sts.package_name}.core.apis")
        assert result is not None
        assert result[0] == "info"


if __name__ == '__main__':
    unittest.main()
