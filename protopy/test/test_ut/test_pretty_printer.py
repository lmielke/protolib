# test_pretty_printer.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers

from protopy.helpers.pretty_printer import PrettyPrinter

class Test_PrettyPrinter(unittest.TestCase):
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

    # def test_wrap_text(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     out = True
    #     # tests and asserts
    #     self.assertEqual(out, expected)

    # def test_pretty_tables(self, *args, **kwargs):
    #     expected = False
    #     # initialize test class
    #     pretty_printer = PrettyPrinter()
    #     pretty_printer.pretty_tables(data)
    #     # tests and asserts
    #     # self.assertEqual(out, expected)


data = {
    'base': {
        'name': 'FunctionToJson._find_method',
        'description': "\n        Finds a method in a given class within a module, "
                       "adjusting for test naming conventions.\n    "
                       "\n            Args:\n                cl_name (str): The name of the class, "
                       "'Test_' prefix removed.\n                    Options:\n                        "
                       "- FunctionToJson\n                        - Test_FunctionToJson\n                "
                       "mth_name (str): The name of the method, 'test_' prefix removed.\n                "
                       "module: The module where the class and method are expected to be found.\n    "
                       "\n            Returns:\n                Callable: The found method or None if not found.\n        ",
        'import': 'protopy.gp.data.tool_choice',
        'module_path': 'C:\\Users\\lars\\python_venvs\\libs\\protolib\\protopy\\gp\\data\\tool_choice.py',
        'parameters': {
            'type': 'object',
            'properties': {
                'self': {'type': 'object', 'default': None, 'required': True},
                'cl_name': {'type': "<class 'str'>", 'default': None, 'required': True},
                'mth_name': {'type': "<class 'str'>", 'default': None, 'required': True},
                'module': {'type': "<class 'object'>", 'default': None, 'required': True}
            }
        },
        'body': 'def _find_method(self, cl_name: str, mth_name: str, module: object) -> Callable:\n'
                '        """\n        Finds a method in a given class within a module, adjusting for test naming \n'
                '        conventions.\n    \n            Args:\n                cl_name (str): The name of the class, '
                '\'Test_\' prefix removed.\n                    Options:\n                        - FunctionToJson\n'
                '                        - Test_FunctionToJson\n                mth_name (str): The name of the method, '
                '\'test_\' prefix removed.\n                module: The module where the class and method are expected '
                'to be found.\n    \n            Returns:\n                Callable: The found method or None if not found.\n'
                '        """\n        cl_name = cl_name.replace(\'Test_\', \'\')\n        mth_name = mth_name.replace(\'test_\', \'\')\n'
                '        found_class = getattr(module, cl_name, None)\n        if found_class is not None:\n            return '
                'getattr(found_class, mth_name, None)\n        return None',
        'returns': 'typing.Callable',
        'example': '@f_json.open_ai_function(apis={"open_ai_api_", "jo_api"}, write=False, file_name=\'#ut_\')\n'
                   '    def test__find_method(self, *args, **kwargs):\n        expected = "<function FunctionToJson._find_method at"\n'
                   '        # initialize test class\n        fj = FunctionToJson()\n        module = fj._find_method(\n'
                   '                                    cl_name=\'Test_FunctionToJson\',\n'
                   '                                    mth_name=\'test__find_method\',\n'
                   '                                    module=sys.modules[__name__],\n'
    }
}

if __name__ == "__main__":
    unittest.main()
