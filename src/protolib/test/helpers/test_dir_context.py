"""
script_path: src/protolib/test/helpers/test_dir_context.py
purpose: "Integration tests for helpers/dir_context.py — DirContext dataclass."
update_rules: "Append scenarios. Never remove existing tests."
"""
import ast, os, tempfile, shutil, unittest
from protolib.helpers.dir_context import DirContext
import protolib.app.settings as sts


class TestAbsPath(unittest.TestCase):
    """_abs_path: resolve to absolute path, default to cwd."""

    def test_none_returns_cwd(self):
        result = DirContext._abs_path(None)
        assert result == os.path.abspath(os.getcwd())

    def test_relative_becomes_absolute(self):
        result = DirContext._abs_path("sub/file.py")
        assert os.path.isabs(result)
        assert result.endswith("sub/file.py")

    def test_absolute_unchanged(self):
        result = DirContext._abs_path("/usr/local/bin")
        assert result == "/usr/local/bin"


class TestDeriveWorkDir(unittest.TestCase):
    """_derive_work_dir: dir stays dir, file becomes its parent."""

    def test_directory_returns_itself(self):
        result = DirContext._derive_work_dir("/tmp")
        assert result == "/tmp"

    def test_file_returns_parent_dir(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        try:
            result = DirContext._derive_work_dir(tmp.name)
            assert result == os.path.dirname(tmp.name)
        finally:
            os.unlink(tmp.name)


class TestFindRoot(unittest.TestCase):
    """_find_root: walk up to find project root by key file."""

    def test_finds_protolib_root(self):
        start = os.path.join(sts.project_dir, "src", "protolib")
        result = DirContext._find_root(start, "pyproject.toml")
        assert result == sts.project_dir

    def test_returns_none_when_not_found(self):
        result = DirContext._find_root("/tmp", "nonexistent_marker_file.xyz")
        assert result is None


class TestFindPackageDir(unittest.TestCase):
    """_find_package_dir: locate subdir containing package_key."""

    def test_finds_package_in_project(self):
        # protolib project has src/protolib/ which contains __main__.py
        src = os.path.join(sts.project_dir, "src")
        result = DirContext._find_package_dir(src, "__main__.py")
        assert result is not None
        assert "protolib" in result


class TestFileFacet(unittest.TestCase):
    """_file_facet: split path into (file_path, file_name, file_dir)."""

    def test_directory_returns_nones(self):
        result = DirContext._file_facet("/tmp")
        assert result == (None, None, None)

    def test_file_returns_components(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        tmp.close()
        try:
            fp, fn, fd = DirContext._file_facet(tmp.name)
            assert fp == tmp.name
            assert fn == os.path.basename(tmp.name)
            assert fd == os.path.dirname(tmp.name)
        finally:
            os.unlink(tmp.name)


class TestImportPath(unittest.TestCase):
    """_import_path: convert file path to dotted import path."""

    def test_converts_to_dotted_path(self):
        root = "/home/user/project"
        fp = "/home/user/project/src/pkg/mod.py"
        result = DirContext._import_path(fp, root)
        assert result == "src.pkg.mod"

    def test_none_when_outside_root(self):
        result = DirContext._import_path("/other/path.py", "/home/user/project")
        assert result is None

    def test_none_when_missing_args(self):
        assert DirContext._import_path(None, "/root") is None
        assert DirContext._import_path("/file.py", None) is None


class TestTestCmd(unittest.TestCase):
    """_test_cmd: produce unittest command from file path."""

    def test_produces_unittest_command(self):
        root = "/home/user/project"
        fp = "/home/user/project/src/pkg/test_mod.py"
        result = DirContext._test_cmd(fp, root)
        assert "python -m unittest" in result
        assert "src.pkg.test_mod" in result

    def test_none_when_missing(self):
        assert DirContext._test_cmd(None, "/root") is None


class TestLineIdx(unittest.TestCase):
    """_line_idx: cursor offset to line number."""

    def test_first_line(self):
        assert DirContext._line_idx("hello\nworld\n", 0) == 0

    def test_second_line(self):
        assert DirContext._line_idx("hello\nworld\n", 6) == 1

    def test_end_of_text(self):
        text = "a\nb\nc\n"
        result = DirContext._line_idx(text, 100)
        assert result == 2  # last line


class TestAstSymbols(unittest.TestCase):
    """_class_at_line / _func_at_line: find class/function at cursor."""

    def test_finds_class(self):
        src = "class Foo:\n    pass\n"
        tree = ast.parse(src)
        assert DirContext._class_at_line(tree, 0) == "Foo"

    def test_finds_function(self):
        src = "def bar():\n    pass\n"
        tree = ast.parse(src)
        assert DirContext._func_at_line(tree, 0) == "bar"

    def test_no_match_returns_none(self):
        src = "x = 1\n"
        tree = ast.parse(src)
        assert DirContext._class_at_line(tree, 0) is None
        assert DirContext._func_at_line(tree, 0) is None


class TestDirContextConstruction(unittest.TestCase):
    """DirContext(path=...): full construction from a real path."""

    def test_from_project_file(self):
        fp = os.path.join(sts.project_dir, "src", "protolib", "app", "settings.py")
        dc = DirContext(path=fp)
        assert dc.project_dir == sts.project_dir
        assert dc.file_name == "settings.py"
        assert dc.import_path == "src.protolib.app.settings"

    def test_from_directory(self):
        dc = DirContext(path=sts.project_dir)
        assert dc.project_dir == sts.project_dir
        assert dc.file_path is None
        assert dc.file_name is None

    def test_package_detection_depth_limit(self):
        # _find_package_dir only searches 1 level deep from project root
        # protolib's __main__.py is 2 levels deep (src/protolib/__main__.py)
        # so package_dir is None from project root — this is current behavior
        dc = DirContext(path=sts.project_dir)
        assert dc.package_dir is None
        assert dc.is_package is False


class TestSnapshot(unittest.TestCase):
    """snapshot: returns flat dict with all context fields."""

    def test_returns_dict_with_core_keys(self):
        dc = DirContext(path=sts.project_dir)
        snap = dc.snapshot()
        assert isinstance(snap, dict)
        for key in ("work_dir", "project_dir", "is_package", "file_path"):
            assert key in snap


class TestToKwargs(unittest.TestCase):
    """to_kwargs: emit flags compatible with legacy callers."""

    def test_non_package_with_info_flags_gets_pg_tree(self):
        dc = DirContext(path=sts.project_dir)
        # is_package is False, but package_info still set; pg_tree allowed
        result = dc.to_kwargs(package_info=["pg_tree", "pg_info"], verbose=False)
        assert result["package_info"] is True
        assert result["pg_tree"] is True

    def test_no_package_info(self):
        dc = DirContext(path=sts.project_dir)
        result = dc.to_kwargs()
        assert result["package_info"] is False


if __name__ == '__main__':
    unittest.main()
