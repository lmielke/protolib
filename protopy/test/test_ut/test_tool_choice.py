# test_tool_choice.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers

from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()

class Test_FunctionToJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        cls.testData = cls.mk_test_data(*args, **kwargs)
        cls.msg = f' >>>> NOT IMPLEMENTED <<<< '

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
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     # should return not implemented error
    #     self.no

    # def test_open_ai_function(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test_handle_returns_inspect(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test_map_to_open_ai_function(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test_dump_to_json(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test__get_object_names(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    @f_json.open_ai_function(apis={"open_ai_api_", "jo_api"}, write=False, file_name='#ut_')
    def test__find_method(self, *args, **kwargs):
        expected = "<function FunctionToJson._find_method at"
        # initialize test class
        fj = FunctionToJson()
        module = fj._find_method(
                                    cl_name='Test_FunctionToJson',
                                    mth_name='test__find_method',
                                    module=sys.modules[__name__],
                                    )
        # tests and asserts
        self.assertEqual(str(module)[:len(expected)], expected)

    # def test_get_function_code(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test_get_function_params_json(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

    # def test_parse_docstring(self, *args, **kwargs):
    #     expected = True
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(self.msg, expected)

if __name__ == "__main__":
    unittest.main()
