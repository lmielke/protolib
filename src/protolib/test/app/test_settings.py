"""
script_path: src/protolib/test/app/test_settings.py
purpose: "Integration tests for app/settings.py — app-layer configuration."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
import protolib.app.settings as sts


class TestPathResolution(unittest.TestCase):
    """Verify Django-style path resolution produces valid directories."""

    def test_root_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.root_dir)

    def test_package_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.package_dir)

    def test_apis_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.apis_dir)


class TestPackageName(unittest.TestCase):
    """package_name derived from directory name."""

    def test_package_name_is_protolib(self, *args, **kwargs):
        assert sts.package_name == "protolib"


class TestConfigValues(unittest.TestCase):
    """Static config values are present and sensible."""

    def test_ignore_dirs_is_set(self, *args, **kwargs):
        assert isinstance(sts.ignore_dirs, set)
        assert ".git" in sts.ignore_dirs

    def test_ignore_files_is_dict(self, *args, **kwargs):
        assert isinstance(sts.ignore_files, dict)

    def test_resources_dir_exists(self, *args, **kwargs):
        assert os.path.isdir(sts.resources_dir)

    def test_user_settings_path_set(self, *args, **kwargs):
        assert sts.user_settings_path.endswith("settings.yml")


class TestLoadUserSettings(unittest.TestCase):
    """load_user_settings: reads YAML config file."""

    def test_returns_dict(self, *args, **kwargs):
        result = sts.load_user_settings()
        assert isinstance(result, dict)

    def test_contains_package_name(self, *args, **kwargs):
        result = sts.load_user_settings()
        if result:
            assert "package_name" in result


if __name__ == '__main__':
    unittest.main()
