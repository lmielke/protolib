"""
script_path: src/protolib/test/app/test_contracts.py
purpose: "Integration tests for app/contracts.py — kwarg cleaning and validation."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
from protolib.app.contracts import (
    checks, clean_kwargs, check_missing_kwargs,
    get_package_data, clean_paths, normalize_path,
)


class TestCleanKwargs(unittest.TestCase):
    """clean_kwargs: strip whitespace from keys and string values."""

    def test_strips_string_values(self, *args, **kwargs):
        result = clean_kwargs(name="  hello  ", count=5)
        assert result["name"] == "hello"

    def test_strips_single_quotes(self, *args, **kwargs):
        result = clean_kwargs(name="'world'")
        assert result["name"] == "world"

    def test_preserves_non_strings(self, *args, **kwargs):
        result = clean_kwargs(count=42, flag=True)
        assert result["count"] == 42
        assert result["flag"] is True

    def test_strips_key_whitespace(self, *args, **kwargs):
        result = clean_kwargs(**{" key ": "val"})
        assert "key" in result


class TestCheckMissingKwargs(unittest.TestCase):
    """check_missing_kwargs: validate required args per API."""

    def test_non_clone_api_passes(self, *args, **kwargs):
        check_missing_kwargs(api="info")

    def test_clone_api_with_all_keys(self, *args, **kwargs):
        check_missing_kwargs(
            api="clone", new_pr_name="x", new_pg_name="y",
            new_alias="z", tgt_dir="/tmp",
        )


class TestGetPackageData(unittest.TestCase):
    """get_package_data: derive paths from settings."""

    def test_returns_dict_with_keys(self, *args, **kwargs):
        result = get_package_data()
        assert "work_dir" in result
        assert "pg_name" in result
        assert result["is_package"] is True

    def test_work_dir_is_absolute(self, *args, **kwargs):
        result = get_package_data()
        assert os.path.isabs(result["work_dir"])

    def test_custom_work_dir(self, *args, **kwargs):
        result = get_package_data(work_dir="/tmp")
        assert result["work_dir"] == "/tmp"


class TestNormalizePath(unittest.TestCase):
    """normalize_path: canonicalize user-supplied paths."""

    def test_expands_home(self, *args, **kwargs):
        result = normalize_path("~/test")
        assert "~" not in result
        assert os.path.isabs(result)

    def test_resolves_relative(self, *args, **kwargs):
        result = normalize_path("relative/path")
        assert os.path.isabs(result)

    def test_empty_returns_empty(self, *args, **kwargs):
        result = normalize_path("")
        assert result == ""

    def test_absolute_unchanged(self, *args, **kwargs):
        result = normalize_path("/usr/local/bin")
        assert result == "/usr/local/bin"


class TestCleanPaths(unittest.TestCase):
    """clean_paths: normalize all _dir/_path kwargs."""

    def test_normalizes_dir_keys(self, *args, **kwargs):
        result = clean_paths(work_dir="~/test", name="keep")
        assert "work_dir" in result
        assert "name" not in result

    def test_normalizes_path_keys(self, *args, **kwargs):
        result = clean_paths(file_path="relative/file.py")
        assert os.path.isabs(result["file_path"])


class TestChecks(unittest.TestCase):
    """checks: full pipeline clean+validate+enrich."""

    def test_returns_enriched_kwargs(self, *args, **kwargs):
        result = checks(api="info", verbose=0)
        assert "work_dir" in result
        assert "pg_name" in result
        assert result["api"] == "info"


if __name__ == '__main__':
    unittest.main()
