# test_tools.py

import json, os, re, shutil, sys, time, yaml
import unittest

# test package imports
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers

from protopy.gp.models.openai.funcs import Function

class Test_Function(unittest.TestCase):
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

    # def test___init__(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_collect_function_data(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     fs = Function()

    #     out = fs.collect_function_data()
    #     print(f"{fs.executables = }")
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_load_apis_json(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_get_func_call(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

if __name__ == "__main__":
    unittest.main()
