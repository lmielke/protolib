# test_protopy.py
import inspect
import logging
import os, re, time
import shutil
import unittest
import yaml

from protopy.helpers.sys_exec.code_file import CodeFile
import protopy.settings as sts
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_CodeFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cf = CodeFile()
        cls.verbose = 0
        cls.test_file = "test_data_py_module.py"
        cls.test_data_path = os.path.join(sts.test_data_dir, cls.test_file)
        cls.test_file_path = cls.mk_test_data()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_file_path):
            os.remove(cls.test_file_path)
            

    @classmethod
    def mk_test_data(cls):
        test_file_name = f"_{cls.test_file}"
        test_file_path = os.path.join(sts.test_data_dir, test_file_name)
        shutil.copyfile(cls.test_data_path, test_file_path)
        return test_file_path


    def test_modify_python_module(self):
        new_method = """
    @staticmethod
    def additional_method():
        print("This is a new method to be added to the codebase.")"""
        self.cf.add_python_method(  content=new_method, 
                                    below_method = "get_user_guess",
                                    module_path=self.test_file_path,
                                    )
        with open(self.test_file_path, "r") as f:
            new_content = f.read()
            self.assertIn("additional_method", new_content)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
