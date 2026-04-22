"""
script_path: src/protolib/test/core/apis/test_server.py
purpose: "Integration tests for core/apis/server.py — HTTP server and API dispatch."
update_rules: "Append scenarios. Never remove existing tests."
"""
import unittest
import protolib.core.settings as sts
from protolib.core.apis.server import (
    _build_params, _cast_value,
    ProtoControlHandler,
)


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
