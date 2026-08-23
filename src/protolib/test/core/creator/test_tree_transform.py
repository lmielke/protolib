"""
script_path: src/protolib/test/core/creator/test_tree_transform.py
description: >-
  Runs integration tests for the TreeTransformer class, verifying file and directory renaming,
  regex-based removal, and text replacement logic. Validates that mapping rules correctly
  rename entities while skipping null values or non-matching names. Confirms that pyproject.toml
  version updates and marked line removals behave as expected. Consumed by the protolib test
  suite to ensure core creator transformations remain stable.
tags:
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import os, unittest
import protolib.test.core.helpers as testhelper
from protolib.core.creator.tree_transform import TreeTransformer


class TestRenameFiles(unittest.TestCase):
    """TreeTransformer.rename_files: rename files based on mapping rules."""

    @testhelper.test_setup(temp_file=None)
    def test_renames_matching_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "protopy_main.py")
        with open(src, "w") as f: f.write("pass")
        TreeTransformer(tmpdir).rename_files(
            root=tmpdir, files=["protopy_main.py"], rules={"protopy": "mypackage"})
        assert os.path.exists(os.path.join(tmpdir, "mypackage_main.py"))
        assert not os.path.exists(src)

    @testhelper.test_setup(temp_file=None)
    def test_skips_none_value(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "protopy_main.py")
        with open(src, "w") as f: f.write("pass")
        TreeTransformer(tmpdir).rename_files(
            root=tmpdir, files=["protopy_main.py"], rules={"protopy": None})
        assert os.path.exists(src)

    @testhelper.test_setup(temp_file=None)
    def test_no_rename_when_no_match(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "other.py")
        with open(src, "w") as f: f.write("pass")
        TreeTransformer(tmpdir).rename_files(
            root=tmpdir, files=["other.py"], rules={"protopy": "mypackage"})
        assert os.path.exists(src)


class TestRenameDirs(unittest.TestCase):
    """TreeTransformer.rename_dirs: rename dirs whose name matches a rule."""

    @testhelper.test_setup(temp_file=None)
    def test_renames_matching_dir(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "protopy")
        os.makedirs(src)
        TreeTransformer(tmpdir).rename_dirs(
            root=tmpdir, dirs=["protopy"], rules={"protopy": "mypackage"})
        assert os.path.exists(os.path.join(tmpdir, "mypackage"))
        assert not os.path.exists(src)

    @testhelper.test_setup(temp_file=None)
    def test_skips_none_value(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "protopy")
        os.makedirs(src)
        TreeTransformer(tmpdir).rename_dirs(
            root=tmpdir, dirs=["protopy"], rules={"protopy": None})
        assert os.path.exists(src)

    @testhelper.test_setup(temp_file=None)
    def test_no_rename_when_no_match(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "other")
        os.makedirs(src)
        TreeTransformer(tmpdir).rename_dirs(
            root=tmpdir, dirs=["other"], rules={"protopy": "mypackage"})
        assert os.path.exists(src)


class TestRemoveFiles(unittest.TestCase):
    """TreeTransformer.remove_files: remove files matching regex patterns."""

    @testhelper.test_setup(temp_file=None)
    def test_removes_matching_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "app.log")
        with open(fp, "w") as f: f.write("log")
        TreeTransformer(tmpdir).remove_files(tmpdir, ["app.log"], patterns=[r'.*\.log$'])
        assert not os.path.exists(fp)

    @testhelper.test_setup(temp_file=None)
    def test_keeps_non_matching_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "app.py")
        with open(fp, "w") as f: f.write("code")
        TreeTransformer(tmpdir).remove_files(tmpdir, ["app.py"], patterns=[r'.*\.log$'])
        assert os.path.exists(fp)

    @testhelper.test_setup(temp_file=None)
    def test_default_patterns_preserve_clone_py(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "clone.py")
        with open(fp, "w") as f: f.write("clone")
        TreeTransformer(tmpdir).remove_files(tmpdir, ["clone.py"])
        assert os.path.exists(fp)


class TestReplaceText(unittest.TestCase):
    """TreeTransformer.replace_text: text substitution in files."""

    @testhelper.test_setup(temp_file=None)
    def test_replaces_text(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "settings.py")
        with open(fp, "w") as f: f.write("package_name = 'protolib'\n")
        TreeTransformer(tmpdir).replace_text(
            root=tmpdir, files=["settings.py"], repls={"protolib": "mylib"})
        content = open(fp).read()
        assert "mylib" in content and "protolib" not in content

    @testhelper.test_setup(temp_file=None)
    def test_handles_case_variants(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "readme.txt")
        with open(fp, "w") as f: f.write("protolib PROTOLIB Protolib\n")
        TreeTransformer(tmpdir).replace_text(
            root=tmpdir, files=["readme.txt"], repls={"protolib": "mylib"})
        content = open(fp).read()
        assert "mylib" in content and "MYLIB" in content and "Mylib" in content

    @testhelper.test_setup(temp_file=None)
    def test_skips_none_replacement(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "test.py")
        with open(fp, "w") as f: f.write("protolib code\n")
        TreeTransformer(tmpdir).replace_text(
            root=tmpdir, files=["test.py"], repls={"protolib": None})
        assert "protolib" in open(fp).read()

    @testhelper.test_setup(temp_file=None)
    def test_skips_non_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "subdir"))
        TreeTransformer(tmpdir).replace_text(
            root=tmpdir, files=["subdir"], repls={"protolib": "mylib"})


class TestRemoveMarkedLines(unittest.TestCase):
    """TreeTransformer.remove_marked_lines: strip lines with REMOVE_MARKER."""

    @testhelper.test_setup(temp_file=None)
    def test_removes_marked_lines(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "code.py")
        with open(fp, "w") as f:
            f.write("keep_this\nremove_this  # clone_remove_line\nalso_keep\n")
        TreeTransformer(tmpdir).remove_marked_lines(root=tmpdir, files=["code.py"])
        content = open(fp).read()
        assert "remove_this" not in content
        assert "keep_this" in content and "also_keep" in content

    @testhelper.test_setup(temp_file=None)
    def test_no_marker_no_change(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "clean.py")
        original = "line1\nline2\nline3\n"
        with open(fp, "w") as f: f.write(original)
        TreeTransformer(tmpdir).remove_marked_lines(root=tmpdir, files=["clean.py"])
        assert open(fp).read() == original


class TestSetPyprojectVersion(unittest.TestCase):
    """TreeTransformer.set_pyproject_version: update requires-python."""

    @testhelper.test_setup(temp_file=None)
    def test_updates_version(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "pyproject.toml")
        with open(fp, "w") as f: f.write('[project]\nrequires-python = ">=3.11"\n')
        TreeTransformer(tmpdir).set_pyproject_version(fp, "3.13.1")
        assert 'requires-python = ">=3.13"' in open(fp).read()

    @testhelper.test_setup(temp_file=None)
    def test_skips_when_no_version(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "pyproject.toml")
        with open(fp, "w") as f: f.write('[project]\nrequires-python = ">=3.11"\n')
        TreeTransformer(tmpdir).set_pyproject_version(fp, None)
        assert ">=3.11" in open(fp).read()

    @testhelper.test_setup(temp_file=None)
    def test_handles_missing_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        TreeTransformer(tmpdir).set_pyproject_version(
            os.path.join(tmpdir, "nonexistent.toml"), "3.12")

    @testhelper.test_setup(temp_file=None)
    def test_warns_when_key_missing(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        fp = os.path.join(tmpdir, "pyproject.toml")
        with open(fp, "w") as f: f.write("[project]\nname = 'test'\n")
        TreeTransformer(tmpdir).set_pyproject_version(fp, "3.12")
        assert "requires-python" not in open(fp).read()


class TestRestructureAndRewrite(unittest.TestCase):
    """TreeTransformer.restructure + rewrite: end-to-end on a small tree."""

    @testhelper.test_setup(temp_file=None)
    def test_full_transform(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        os.makedirs(os.path.join(tmpdir, "protopy"))
        with open(os.path.join(tmpdir, "protopy", "settings.py"), "w") as f:
            f.write("package = 'protolib'\nport = 9001  # clone_remove_line\n")
        with open(os.path.join(tmpdir, "protopy_main.py"), "w") as f:
            f.write("from protopy import settings\n")
        tx = TreeTransformer(tmpdir)
        tx.restructure({"protopy": "newpkg", "protolib": "newlib"})
        tx.rewrite({"protopy": "newpkg", "protolib": "newlib"})
        assert os.path.exists(os.path.join(tmpdir, "newpkg", "settings.py"))
        assert os.path.exists(os.path.join(tmpdir, "newpkg_main.py"))
        content = open(os.path.join(tmpdir, "newpkg", "settings.py")).read()
        assert "newlib" in content
        assert "clone_remove_line" in content


if __name__ == '__main__':
    unittest.main()
