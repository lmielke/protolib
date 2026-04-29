"""
script_path: src/protolib/test/core/test_settings.py
purpose: "Integration tests for core/settings.py — path resolution and config."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
import protolib.core.settings as sts


class TestPathResolution(unittest.TestCase):
    """Verify Django-style path resolution produces valid directories."""

    def test_core_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.core_dir)

    def test_package_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.package_dir)

    def test_src_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.src_dir)

    def test_project_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.project_dir)

    def test_apis_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.apis_dir)

    def test_test_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.test_dir)


class TestPackageName(unittest.TestCase):
    """package_name / project_name derived from directory names."""

    def test_package_name_is_protolib(self, *args, **kwargs):
        assert sts.package_name == "protolib"


class TestConfigValues(unittest.TestCase):
    """Static config values are present and sensible."""

    def test_ignore_dirs_is_set(self, *args, **kwargs):
        assert isinstance(sts.ignore_dirs, set)
        assert ".git" in sts.ignore_dirs

    def test_registry_port_is_int(self, *args, **kwargs):
        assert isinstance(sts.registry_port, int)
        assert 1 <= sts.registry_port <= 65535

    def test_table_max_chars_is_positive(self, *args, **kwargs):
        assert sts.table_max_chars > 0

    def test_extensions_set(self, *args, **kwargs):
        assert sts.eext == ".yml"
        assert sts.fext == ".json"


if __name__ == '__main__':
    unittest.main()
