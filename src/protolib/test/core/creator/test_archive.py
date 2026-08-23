"""
script_path: src/protolib/test/core/creator/test_archive.py
description: >-
  Runs integration tests for the core creator archive module, verifying directory collection,
  ignore filtering, and path preparation logic. Validates that archive helpers correctly handle
  source and target directory structures. Consumed by the protolib test suite to ensure backup
  and staging operations remain stable.
tags:
- backup
- staging
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import os, unittest
import protolib.test.core.helpers as testhelper
from protolib.core.creator.archive import (
    collect_ignored_dirs, custom_ignore, archive, mk_tgt_dir, prep_paths,
)


class TestCollectIgnoredDirs(unittest.TestCase):
    """collect_ignored_dirs: walk and collect matching directories."""

    def _mk_tree(self, *args, tmpdir, **kwargs):
        os.makedirs(os.path.join(tmpdir, "src", "pkg"))
        os.makedirs(os.path.join(tmpdir, ".git", "objects"))
        os.makedirs(os.path.join(tmpdir, "__pycache__"))

    @testhelper.test_setup(temp_file=None)
    def test_finds_git_dir(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        self._mk_tree(tmpdir=tmpdir)
        paths = [os.path.basename(p) for p in collect_ignored_dirs(tmpdir, [r"\.git"])]
        assert ".git" in paths

    @testhelper.test_setup(temp_file=None)
    def test_finds_pycache(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        self._mk_tree(tmpdir=tmpdir)
        paths = [os.path.basename(p) for p in collect_ignored_dirs(tmpdir, [r"__pycache__"])]
        assert "__pycache__" in paths

    @testhelper.test_setup(temp_file=None)
    def test_no_match_returns_empty(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        self._mk_tree(tmpdir=tmpdir)
        assert len(collect_ignored_dirs(tmpdir, [r"nonexistent_xyz"])) == 0


class TestCustomIgnore(unittest.TestCase):
    """custom_ignore: creates shutil.copytree ignore function."""

    def test_returns_callable(self, *args, **kwargs):
        assert callable(custom_ignore(set()))

    def test_filters_ignored(self, *args, **kwargs):
        func = custom_ignore({"/tmp/test/skip_me"})
        result = func("/tmp/test", ["skip_me", "keep_me"])
        assert "skip_me" in result
        assert "keep_me" not in result


class TestMkTgtDir(unittest.TestCase):
    """mk_tgt_dir: create timestamped target dir name."""

    def test_direct_mode(self, *args, **kwargs):
        assert "test_backup" in mk_tgt_dir(comment="test_backup", direct=True)

    def test_with_comment(self, *args, **kwargs):
        result = mk_tgt_dir(comment="my_archive_name")
        assert "my_archive_name" in result
        assert "/" not in result


class TestPrepPaths(unittest.TestCase):
    """prep_paths: join sources and target directory into path tuples."""

    @testhelper.test_setup(temp_file=None)
    def test_returns_path_tuples(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "src_dir")
        os.makedirs(src)
        with open(os.path.join(src, "file.txt"), "w") as f: f.write("test")
        tgt = os.path.join(tmpdir, "archive", "backup")
        paths = prep_paths(tgt, defaultSources=[src])
        assert len(paths) == 1
        assert paths[0][0] == os.path.normpath(src)

    @testhelper.test_setup(temp_file=None)
    def test_missing_source_skipped(self, tempDataPath, *args, **kwargs):
        tgt = os.path.join(os.path.dirname(tempDataPath), "archive", "backup")
        assert len(prep_paths(tgt, defaultSources=["/nonexistent/xyz"])) == 0


class TestArchive(unittest.TestCase):
    """archive: copy files from source to target."""

    @testhelper.test_setup(temp_file=None)
    def test_copies_directory(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src = os.path.join(tmpdir, "src")
        tgt = os.path.join(tmpdir, "tgt")
        os.makedirs(src)
        with open(os.path.join(src, "a.txt"), "w") as f: f.write("hello")
        paths = [(src, tgt)]
        assert archive(paths, ignore_dirs=[]) == paths
        assert os.path.exists(os.path.join(tgt, "a.txt"))

    @testhelper.test_setup(temp_file=None)
    def test_copies_single_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        src_file = os.path.join(tmpdir, "src", "a.txt")
        tgt_file = os.path.join(tmpdir, "tgt", "b.txt")
        os.makedirs(os.path.dirname(src_file))
        os.makedirs(os.path.dirname(tgt_file), exist_ok=True)
        with open(src_file, "w") as f: f.write("hello")
        archive([(src_file, tgt_file)], ignore_dirs=[])
        assert os.path.exists(tgt_file)


if __name__ == '__main__':
    unittest.main()
