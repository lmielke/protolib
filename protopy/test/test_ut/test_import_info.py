# test_import_info.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers

from protopy.helpers.sys_info.import_info import PackageInfo
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()


class Test_PackageInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        cls.testData = cls.mk_test_data(*args, **kwargs)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        pass

    @classmethod
    def mk_test_data(cls, *args, **kwargs):
        out = None
        # with open(os.path.join(sts.test_data_dir, "someFile.yml"), "r") as f:
        #     out = yaml.safe_load(f)
        return out

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test_analyze_package_imports(self, *args, **kwargs):
        """
        This test generates an openai function json file from the decorated function.
        verbose is set to 0, so the output is only the graphviz dot file.
        """
        
        expected = "// Package Dependency Graph\ndigraph"
        # initialize test class
        informer = PackageInfo()
        dot_file = informer.analyze_package_imports(main_file_name='protopy.py', verbose=0)
        # tests and asserts
        self.assertIn(expected, dot_file[:len(expected)])

    # def test_find_root_dir(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_build_graph(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_finalize_graph(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_create_import_graph(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_parse_imports(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_resolve_module_path_to_file(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_locate_file(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

if __name__ == "__main__":
    unittest.main()
