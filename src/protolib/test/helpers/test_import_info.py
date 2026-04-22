"""
script_path: src/protolib/test/helpers/test_import_info.py
purpose: "Integration tests for helpers/import_info.py — PackageInfo graph builder."
update_rules: "Append scenarios. Never remove existing tests."
"""
import os, unittest
import protolib.test.core.testhelper as testhelper
from protolib.helpers.import_info import PackageInfo, select_files
import protolib.app.settings as sts


class TestFindRootDir(unittest.TestCase):
    """find_root_dir: locate project root by __main__.py."""

    def test_finds_root_from_cwd(self, *args, **kwargs):
        orig = os.getcwd()
        try:
            os.chdir(sts.project_dir)
            pkg = PackageInfo.__new__(PackageInfo)
            result = pkg.find_root_dir()
            assert result is not None
            root_dir, pkg_name = result
            assert os.path.isdir(root_dir) and pkg_name == "protolib"
        finally:
            os.chdir(orig)

    @testhelper.test_setup(temp_file=None, temp_chdir='temp_file')
    def test_returns_none_when_no_main(self, tempDataPath, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        assert pkg.find_root_dir() is None


class TestLocateFile(unittest.TestCase):
    """locate_file: recursively find a file in a directory."""

    def test_finds_existing_file(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        result = pkg.locate_file("settings.py", os.path.join(sts.project_dir, "src"))
        assert result is not None and result.endswith("settings.py")

    def test_returns_none_for_missing_file(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        assert pkg.locate_file("nonexistent_xyz.py", sts.project_dir) is None


class TestResolveModulePath(unittest.TestCase):
    """resolve_module_path_to_file: dot path to file path."""

    def test_resolves_known_module(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir = os.path.join(sts.project_dir, "src")
        result = pkg.resolve_module_path_to_file("protolib.app.settings")
        assert result is not None and result.endswith("settings.py")

    def test_returns_none_for_unknown(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir = os.path.join(sts.project_dir, "src")
        assert pkg.resolve_module_path_to_file("nonexistent.module.xyz") is None


class TestParseImports(unittest.TestCase):
    """parse_imports: extract local import statements from a file."""

    def test_finds_protolib_imports(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir = os.path.join(sts.project_dir, "src")
        pkg.package_name = "protolib"
        fp = os.path.join(sts.project_dir, "src", "protolib", "app", "settings.py")
        assert isinstance(pkg.parse_imports(fp), list)

    @testhelper.test_setup(temp_file=None)
    def test_empty_for_no_local_imports(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        tmpfile = os.path.join(tmpdir, "standalone.py")
        with open(tmpfile, "w") as f: f.write("import os\nx = 1\n")
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir = tmpdir
        pkg.package_name = "mypkg"
        assert pkg.parse_imports(tmpfile) == []


class TestBuildGraph(unittest.TestCase):
    """build_graph: recursive graph construction."""

    @testhelper.test_setup(temp_file=None)
    def test_visits_file(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        pkg_dir = os.path.join(tmpdir, "mypkg")
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "a.py"), "w") as f: f.write("x = 1\n")
        import graphviz
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir, pkg.package_name = tmpdir, "mypkg"
        pkg.visited_files, pkg.visited_paths, pkg.incoming_edges = set(), set(), {}
        pkg.graph = graphviz.Digraph()
        pkg.build_graph(os.path.join(pkg_dir, "a.py"))
        assert "a.py" in pkg.visited_files

    @testhelper.test_setup(temp_file=None)
    def test_no_revisit(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        pkg_dir = os.path.join(tmpdir, "mypkg")
        os.makedirs(pkg_dir)
        with open(os.path.join(pkg_dir, "a.py"), "w") as f: f.write("x = 1\n")
        import graphviz
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.root_dir, pkg.package_name = tmpdir, "mypkg"
        pkg.visited_files = {"a.py"}
        pkg.visited_paths, pkg.incoming_edges = set(), {}
        pkg.graph = graphviz.Digraph()
        pkg.build_graph(os.path.join(pkg_dir, "a.py"))
        assert len(pkg.visited_files) == 1


class TestGetFileList(unittest.TestCase):
    """get_file_list: return visited files as dicts."""

    @testhelper.test_setup(temp_file=None)
    def test_returns_file_dicts(self, tempDataPath, *args, **kwargs):
        tmpdir = os.path.dirname(tempDataPath)
        tmpfile = os.path.join(tmpdir, "mod.py")
        with open(tmpfile, "w") as f: f.write("x = 1\n")
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.visited_paths = {tmpfile}
        result = pkg.get_file_list()
        assert len(result) == 1
        assert result[0]["file_path"] == tmpfile and "x = 1" in result[0]["file_content"]

    def test_empty_when_no_visits(self, *args, **kwargs):
        pkg = PackageInfo.__new__(PackageInfo)
        pkg.visited_paths = set()
        assert pkg.get_file_list() == []


class TestSelectFiles(unittest.TestCase):
    """select_files: convenience function for import graph traversal."""

    def test_returns_empty_for_directory(self, *args, **kwargs):
        assert select_files(path=sts.project_dir) == []


class TestCreateGraph(unittest.TestCase):
    """create_graph: full graph construction from main file."""

    def test_creates_graph_for_settings(self, *args, **kwargs):
        orig = os.getcwd()
        try:
            os.chdir(sts.project_dir)
            pkg = PackageInfo(main_file="settings.py")
            assert pkg.create_graph() is not None and len(pkg.visited_files) >= 1
        finally:
            os.chdir(orig)


if __name__ == '__main__':
    unittest.main()
