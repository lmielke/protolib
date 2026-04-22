"""
script_path: src/protolib/test/helpers/test_collections.py
purpose: "Integration tests for helpers/collections.py — path, dict, text, and dir utilities."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
import protolib.test.core.testhelper as testhelper
import protolib.helpers.collections as col
import protolib.app.settings as sts


class TestUnaliasPath(unittest.TestCase):
    """unalias_path: tilde expansion, dot/dotdot resolution, %USERPROFILE%, normpath."""

    def test_tilde_expands_to_home(self, *args, **kwargs):
        result = col.unalias_path("~/Documents")
        assert result == os.path.normpath(os.path.join(os.path.expanduser("~"), "Documents"))

    def test_single_dot_resolves_to_cwd(self, *args, **kwargs):
        result = col.unalias_path("./sub")
        assert result == os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), "sub")))

    def test_double_dot_resolves_to_parent(self, *args, **kwargs):
        result = col.unalias_path("../sibling")
        parent = os.path.dirname(os.getcwd())
        assert result == os.path.normpath(os.path.abspath(os.path.join(parent, "sibling")))

    def test_userprofile_replaced_with_home(self, *args, **kwargs):
        result = col.unalias_path(r"%USERPROFILE%/Desktop")
        assert os.path.expanduser("~") in result
        assert "Desktop" in result

    def test_absolute_path_returned_unchanged(self, *args, **kwargs):
        assert col.unalias_path("/usr/local/bin") == "/usr/local/bin"


class TestFindDictEntry(unittest.TestCase):
    """find_dict_entry: recursive key lookup in nested dicts."""

    def test_top_level_key_found(self, *args, **kwargs):
        assert col.find_dict_entry({"name": "proto", "version": "1.0"}, "name") == {"name": "proto"}

    def test_nested_key_found(self, *args, **kwargs):
        assert col.find_dict_entry({"outer": {"inner": {"target": 42}}}, "target") == {"target": 42}

    def test_missing_key_returns_none(self, *args, **kwargs):
        assert col.find_dict_entry({"a": 1, "b": {"c": 2}}, "missing") is None

    def test_empty_dict_returns_none(self, *args, **kwargs):
        assert col.find_dict_entry({}, "any") is None

    def test_first_match_wins(self, *args, **kwargs):
        result = col.find_dict_entry({"x": {"target": "deep"}, "target": "top"}, "target")
        assert result is not None and "target" in result


class TestGroupText(unittest.TestCase):
    """group_text: text wrapping — list joining, empty handling."""

    def test_none_returns_none_string(self, *args, **kwargs):
        assert col.group_text(None, 40) == "None"

    def test_empty_string_returns_none_string(self, *args, **kwargs):
        assert col.group_text("", 40) == "None"

    def test_list_values_joined_and_wrapped(self, *args, **kwargs):
        result = col.group_text(["alpha", "beta", "gamma", "delta"], 80)
        assert all(item in result for item in ["alpha", "beta", "gamma", "delta"])

    def test_list_result_starts_with_newline(self, *args, **kwargs):
        assert col.group_text(["a", "b"], 80).startswith("\n")

    def test_string_wrapped_at_width(self, *args, **kwargs):
        result = col.group_text("word " * 20, 30)
        assert result.startswith("\n")
        assert all(len(line) <= 30 for line in result.strip().split('\n'))


class TestCollectIgnoredDirs(unittest.TestCase):
    """collect_ignored_dirs: walk directory tree, match against regex patterns."""

    @testhelper.test_setup(temp_file=None)
    def test_matches_exact_dir_name(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        for d in ["src/main", ".git", "build", "src/deep"]:
            os.makedirs(os.path.join(tmpdir, d), exist_ok=True)
        names = {os.path.basename(p) for p in col.collect_ignored_dirs(tmpdir, [r"\.git"])}
        assert ".git" in names

    @testhelper.test_setup(temp_file=None)
    def test_matches_multiple_patterns(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        for d in ["src/main", ".git", "build"]:
            os.makedirs(os.path.join(tmpdir, d), exist_ok=True)
        names = {os.path.basename(p) for p in col.collect_ignored_dirs(tmpdir, [r"\.git", r"build"])}
        assert ".git" in names and "build" in names

    @testhelper.test_setup(temp_file=None)
    def test_non_matching_dirs_excluded(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        for d in ["src/main", ".git"]:
            os.makedirs(os.path.join(tmpdir, d), exist_ok=True)
        names = {os.path.basename(p) for p in col.collect_ignored_dirs(tmpdir, [r"\.git"])}
        assert "src" not in names and "main" not in names

    @testhelper.test_setup(temp_file=None)
    def test_empty_patterns_returns_empty(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        assert len(col.collect_ignored_dirs(tmpdir, [])) == 0


class TestTempChdir(unittest.TestCase):
    """temp_chdir: context manager changes cwd and restores on exit."""

    @testhelper.test_setup(temp_file=None)
    def test_changes_to_target_and_restores(self, tempDataPath, *args, **kwargs):
        target = os.path.dirname(tempDataPath)
        original = os.getcwd()
        with col.temp_chdir(target):
            assert os.getcwd() == target
        assert os.getcwd() == original

    @testhelper.test_setup(temp_file=None)
    def test_restores_on_exception(self, tempDataPath, *args, **kwargs):
        target = os.path.dirname(tempDataPath)
        original = os.getcwd()
        try:
            with self.assertRaises(ValueError):
                with col.temp_chdir(target):
                    raise ValueError("test")
        finally:
            assert os.getcwd() == original


class TestFindFilePath(unittest.TestCase):
    """_find_file_path: locate a file by name within a project tree."""

    @testhelper.test_setup(temp_file=None)
    def test_finds_existing_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "src", "mod"), exist_ok=True)
        target = os.path.join(tmpdir, "src", "mod", "target.py")
        open(target, "w").close()
        result = col._find_file_path("target.py", project_dir=tmpdir)
        assert result is not None and result.endswith("target.py") and os.path.isfile(result)

    @testhelper.test_setup(temp_file=None)
    def test_returns_none_for_missing_file(self, tempDataPath, *args, **kwargs):
        assert col._find_file_path("nonexistent.py", project_dir=os.path.dirname(tempDataPath)) is None

    def test_returns_none_for_empty_input(self, *args, **kwargs):
        assert col._find_file_path(None, project_dir="/tmp") is None

    @testhelper.test_setup(temp_file=None)
    def test_respects_max_depth(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "src", "mod"), exist_ok=True)
        open(os.path.join(tmpdir, "src", "mod", "target.py"), "w").close()
        assert col._find_file_path("target.py", project_dir=tmpdir, max_depth=1) is None


if __name__ == '__main__':
    unittest.main()
