"""
script_path: src/protolib/test/helpers/test_tree.py
description: >-
  Provides integration tests for the Tree class and its helper functions within the protolib
  package. Validates initialization defaults, pattern matching logic, and directory traversal
  behavior. Ensures file content loading and colorization utilities operate correctly under
  various verbosity settings.
tags:
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import os, unittest
import protolib.test.core.helpers as testhelper
from protolib.helpers.tree import Tree
import protolib.helpers.printing as pr


class TestTreeInit(unittest.TestCase):
    """Tree.__init__: default style applied, empty match lists."""

    def test_default_style_attributes_set(self, *args, **kwargs):
        t = Tree(yes=True)
        assert hasattr(t, 'dir_sym') and hasattr(t, 'file_sym') and hasattr(t, 'fold_sym')

    def test_matched_files_empty_on_init(self, *args, **kwargs):
        assert Tree(yes=True).matched_files == []

    def test_loaded_files_empty_on_init(self, *args, **kwargs):
        assert Tree(yes=True).loaded_files == []

    def test_verbosity_with_yes_flag(self, *args, **kwargs):
        assert Tree(verbose=3, yes=True).verbose == 3


class TestIsIgnored(unittest.TestCase):
    """_is_ignored: exact match, glob, and suffix-like patterns."""

    def test_exact_match(self, *args, **kwargs):
        assert Tree(yes=True)._is_ignored(".git", {".git", "build"}) is True

    def test_no_match(self, *args, **kwargs):
        assert Tree(yes=True)._is_ignored("src", {".git", "build"}) is False

    def test_glob_match(self, *args, **kwargs):
        assert Tree(yes=True)._is_ignored("mypackage.egg-info", {"*.egg-info"}) is True

    def test_suffix_like_match(self, *args, **kwargs):
        assert Tree(yes=True)._is_ignored("core_helpers", {"*helpers"}) is True


class TestMatchPat(unittest.TestCase):
    """_match_pat: exact, substring, and extension matching."""

    def test_exact_match(self, *args, **kwargs):
        assert Tree(yes=True)._match_pat(f="readme.md", p="readme.md") is True

    def test_extension_match(self, *args, **kwargs):
        assert Tree(yes=True)._match_pat(f="script.py", p=".py") is True

    def test_substring_match(self, *args, **kwargs):
        assert Tree(yes=True)._match_pat(f="test_helper.py", p="helper") is True

    def test_no_match(self, *args, **kwargs):
        assert Tree(yes=True)._match_pat(f="data.json", p=".py") is False


class TestIgnoredFile(unittest.TestCase):
    """_ignored_file: hide file contents below verbosity threshold."""

    def test_unknown_filename_not_ignored(self, *args, **kwargs):
        assert Tree(verbose=0, yes=True)._ignored_file("unique_filename_xyz.txt") is False

    def test_custom_rules_apply(self, *args, **kwargs):
        import protolib.app.settings as app_sts
        original = getattr(app_sts, "ignore_files", None)
        try:
            app_sts.ignore_files = {5: {"__init__.py"}}
            assert Tree(verbose=0, yes=True)._ignored_file("__init__.py") is True
            assert Tree(verbose=6, yes=True)._ignored_file("__init__.py") is False
        finally:
            if original is None:
                if hasattr(app_sts, "ignore_files"): delattr(app_sts, "ignore_files")
            else:
                app_sts.ignore_files = original

    def test_unknown_file_not_ignored(self, *args, **kwargs):
        assert Tree(verbose=0, yes=True)._ignored_file("my_module.py") is False


class TestIsAbbrevDir(unittest.TestCase):
    """_is_abbrev_dir: abbreviate listing for log-like directories."""

    @testhelper.test_setup(temp_file=None)
    def test_log_dir_is_abbreviated(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        log_dir = os.path.join(tmpdir, "log")
        os.makedirs(log_dir)
        assert Tree(yes=True)._is_abbrev_dir(log_dir) is True

    @testhelper.test_setup(temp_file=None)
    def test_src_dir_not_abbreviated(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src_dir = os.path.join(tmpdir, "src")
        os.makedirs(src_dir)
        assert Tree(yes=True)._is_abbrev_dir(src_dir) is False


class TestTrackMatch(unittest.TestCase):
    """_track_match: append unique paths to matched_files."""

    def test_adds_path(self, *args, **kwargs):
        t = Tree(yes=True)
        t._track_match(path="/tmp/a.py")
        assert "/tmp/a.py" in t.matched_files

    def test_no_duplicates(self, *args, **kwargs):
        t = Tree(yes=True)
        t._track_match(path="/tmp/a.py")
        t._track_match(path="/tmp/a.py")
        assert len(t.matched_files) == 1

    def test_none_path_skipped(self, *args, **kwargs):
        t = Tree(yes=True)
        t._track_match(path=None)
        assert len(t.matched_files) == 0


class TestPromoteWorkfile(unittest.TestCase):
    """_promote_workfile: move work file to front of matched_files."""

    def test_promotes_to_front(self, *args, **kwargs):
        t = Tree(yes=True)
        t.matched_files = ["/tmp/a.py", "/tmp/b.py", "/tmp/target.py"]
        t._promote_workfile(work_file_name="target")
        assert t.matched_files[0] == "/tmp/target.py"

    def test_noop_when_not_found(self, *args, **kwargs):
        t = Tree(yes=True)
        t.matched_files = ["/tmp/a.py"]
        t._promote_workfile(work_file_name="missing")
        assert t.matched_files == ["/tmp/a.py"]

    def test_noop_when_no_work_file(self, *args, **kwargs):
        t = Tree(yes=True)
        t.matched_files = ["/tmp/a.py"]
        t._promote_workfile(work_file_name=None)
        assert t.matched_files == ["/tmp/a.py"]


class TestMkTree(unittest.TestCase):
    """mk_tree: walk temp directory, produce hierarchy and contents."""

    @testhelper.test_setup(temp_file=None)
    def test_hierarchy_contains_dir_names(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f: f.write("print('hello')")
        tree_str, _ = Tree(verbose=0, yes=True).mk_tree(project_dir=tmpdir)
        assert "src" in tree_str

    @testhelper.test_setup(temp_file=None)
    def test_hierarchy_contains_files(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f: f.write("print('hello')")
        tree_str, _ = Tree(verbose=0, yes=True).mk_tree(project_dir=tmpdir)
        assert "main.py" in tree_str

    @testhelper.test_setup(temp_file=None)
    def test_ignored_dir_truncated(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, ".git"), exist_ok=True)
        tree_str, _ = Tree(verbose=0, yes=True).mk_tree(project_dir=tmpdir, ignores={".git"})
        assert ".git" in tree_str

    @testhelper.test_setup(temp_file=None)
    def test_max_depth_limits_traversal(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        deep = os.path.join(tmpdir, "a", "b", "c")
        os.makedirs(deep, exist_ok=True)
        with open(os.path.join(deep, "deep.py"), "w") as f: f.write("pass")
        tree_str, _ = Tree(verbose=0, yes=True).mk_tree(project_dir=tmpdir, max_depth=1)
        assert "deep.py" not in tree_str

    @testhelper.test_setup(temp_file=None)
    def test_file_match_regex_tracks_matches(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "src"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "main.py"), "w") as f: f.write("pass")
        t = Tree(verbose=0, yes=True)
        t.mk_tree(project_dir=tmpdir, file_match_regex=r"\.py$")
        assert any("main.py" in p for p in t.matched_files)


class TestCallable(unittest.TestCase):
    """Tree.__call__: returns dict with required keys."""

    @testhelper.test_setup(temp_file=None)
    def test_returns_dict_with_expected_keys(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        with open(os.path.join(tmpdir, "example.py"), "w") as f: f.write("x = 1")
        result = Tree(verbose=0, yes=True)(project_dir=tmpdir)
        assert isinstance(result, dict)
        assert all(k in result for k in ("tree", "contents", "file_matches",
                                         "selected_files", "loaded_files"))


class TestLoadFileContent(unittest.TestCase):
    """load_file_content: read file, handle errors gracefully."""

    @testhelper.test_setup(temp_file=None)
    def test_reads_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "test_read.py")
        with open(fp, "w") as f: f.write("hello world")
        assert Tree(verbose=0, yes=True).load_file_content(file_path=fp) == "hello world"

    def test_missing_file_returns_empty(self, *args, **kwargs):
        assert Tree(verbose=0, yes=True).load_file_content(file_path="/nonexistent/file.py") == ""


class TestColorize(unittest.TestCase):
    """_colorize: injects ANSI codes, preserves original text."""

    def test_colorized_output_contains_original_text(self, *args, **kwargs):
        raw = "|-- src\n    |- main.py"
        clean = pr.strip_ansi_codes(Tree(verbose=0, yes=True)._colorize(raw))
        assert "src" in clean and "main.py" in clean

    def test_py_extension_gets_colorized(self, *args, **kwargs):
        assert "\x1b[" in Tree(verbose=0, yes=True)._colorize("|- script.py")


if __name__ == '__main__':
    unittest.main()
