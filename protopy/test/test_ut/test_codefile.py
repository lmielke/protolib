# test_protopy.py
import inspect
import logging
import os, re, time
import unittest
import yaml

from protopy.helpers.sys_exec.code_file import CodeFile
import protopy.settings as sts
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_CodeFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system = CodeFile()
        cls.verbose = 0
        cls.testData = cls.mk_test_data()
        cls.content = """
                                Certainly! To create your package named `myclocklib` in your temp directory, run the following command in your terminal:  ```shell pipenv run proto clone -pr 'myclock' -n 'myclock' -a 'clock' -t 'C:\\temp' -p 3.11 --install ```  \nThis will clone `protolib` to `C:/Users/lars/myclock`, set up the environment, and install dependencies.
                            """
        cls.code_blocks = """
            You can list all files in the current directory using the `ls` command on Unix-
           like systems or the `dir` command on Windows. Since you're using Windows, you
           can use the following command in your shell:

           ```shell

           dir

           ```

           If you want to list the files in a format similar to Unix systems, you can use:

           ```shell

           dir /B

           ```
        """

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_create_python_module_dir):
            for f in os.listdir(cls.test_create_python_module_dir):
                os.remove(os.path.join(cls.test_create_python_module_dir, f))
            os.rmdir(cls.test_create_python_module_dir)

    @classmethod
    def mk_test_data(cls):
        # setup test data directory for test_create_python_module
        # that test must write a python file
        cls.test_create_python_module_dir = os.path.join(
                                                            sts.test_data_dir, 
                                                            'test_create_python_module'
                                            )
        if not os.path.exists(cls.test_create_python_module_dir):
            os.mkdir(cls.test_create_python_module_dir)
        with open(os.path.join(sts.package_dir, f"{sts.package_name}.py"), 'r') as f:
            cls.code = f.read()
        code = '\n'.join([f"{i:<3}: {l}" for i, l in enumerate(cls.code.split('\n'), 1)])

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test_create_python_module(self):
        """
        This is an example on how to use create_python_module.
        IMPORTANT: Adhere to modified PEP8 at all times!
        """
        system = CodeFile()
        # create a meaninful module_name
        module_name='test_create_python_module.py'
        # the module directory is a relative path to the package dir
        module_dir = os.path.relpath(self.test_create_python_module_dir, sts.project_dir)
        # create the python module
        # this is how we call the function
        r = system.create_python_module(
                            module_name=module_name, 
                            module_dir=module_dir, 
                            content=self.code,# testing only, example code from the docstring
                )
        # we check the status for success, status returns true if successful
        self.assertTrue(r.get('status'))
        # we import the created file to assert its correctness
        module_path = os.path.join(module_dir, module_name)
        dot_path = os.path.splitext(module_path)[0].replace(os.sep, '.')
        import importlib
        module = importlib.import_module(dot_path)
        self.assertEqual(
                            inspect.getdoc(module).replace(' ', '').strip(), 
                            self.code.split('"""')[1].replace(' ', '').strip(),
                            )
    

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test_add_python_method(self):
        """
        This is an example on how to use add_python_method.
        """
        system = CodeFile()
        module_name = 'test_add_python_method.py'
        module_dir = os.path.relpath(self.test_create_python_module_dir, sts.project_dir)
        
        # Initial content for the module
        initial_code = """
    def existing_method():
        return 'Existing method!'

    def another_method():
        return 'Another method!'
"""
        
        # New method to add
        new_method_content = """
        def new_method():
            return 'New method!'
"""
        
        # Replace method content
        replace_method_content = """
    def replaced_existing_method():
        return 'Replaced method!'
"""
        
        # Create the initial python module
        r = system.create_python_module(
            module_name=module_name,
            module_dir=module_dir,
            content=initial_code
        )
        self.assertTrue(r.get('status'))
        
        # Test inserting a new method after existing_method
        r = system.add_python_method(
            content=new_method_content,
            below_method='existing_method',
            replace_method=None,
            module_path=os.path.join(module_dir, module_name)
        )
        self.assertTrue(r.get('status'))
        self.assertTrue(r.get('status'))
        
        # Check if the new method was inserted correctly
        with open(os.path.join(sts.project_dir, module_dir, module_name), 'r') as f:
            content = f.read()
        self.assertIn(new_method_content.split('\n')[0].strip(), content)
        
        # Test replacing the existing method
        r = system.add_python_method(
            content=replace_method_content,
            below_method=None,
            replace_method='existing_method',
            module_path=os.path.join(module_dir, module_name)
        )
        self.assertTrue(r.get('status'))
        
        # Check if the method was replaced correctly
        with open(os.path.join(sts.project_dir, module_dir, module_name), 'r') as f:
            content = f.read()
        self.assertIn(replace_method_content.strip(), content)
        
        # Print the final content of the module for verification
        self.assertNotIn("return 'Existing method!'", content)
        code = '\n'.join([f"{i:<3}:{l}" for i, l in enumerate(content.split('\n'), 1)])


    # @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    # def test__modify_python_module(self):
    #     """
    #     This is an example on how to use modify_python_module.
    #     """
    #     system = CodeFile()
    #     module_name = 'test__modify_python_module.py'
    #     module_dir = os.path.relpath(self.test_create_python_module_dir, sts.project_dir)
        
    #     # Initial content for the module
    #     initial_code = """
    # def single_method():
    #     return 'Single method!'
    # """
        
    #     # Content to insert
    #     insert_content = """
    # """
        
    #     # Create the initial python module
    #     r = system.create_python_module(
    #         module_name=module_name,
    #         module_dir=module_dir,
    #         content=initial_code
    #     )
    #     self.assertTrue(r.get('status'))
        
    #     # Test cases for different indices
    #     test_cases = [
    #         (2, ),
    #         (2, None),
    #         (2, 2),
    #         (2, 3),
    #         (2, 4)
    #     ]
        
    #     for indexs in test_cases:
    #         with self.subTest(indexs=indexs):
    #             success = system._modify_python_module(
    #                                         content=insert_content,
    #                                         indexs=indexs,
    #                                         module_path=os.path.join(module_dir, module_name)
    #             )
    #             self.assertTrue(success)
                
    #             # Check if the content was inserted correctly
    #             with open(os.path.join(sts.project_dir, module_dir, module_name), 'r') as f:
    #                 content = f.read()
    #             self.assertIn(insert_content.strip(), content)
                
    #             # Print the final content of the module for verification
    #             code = '\n'.join([f"{i:<3}:{l}" for i, l in enumerate(content.split('\n'), 1)])


    def test__get_indexs_from_text(self):
        # Initial content for the module
        initial_code = """
    def existing_method():
        return 'Existing method!'

    def another_method():
        return 'Another method!'

    @staticmethod
    def new_method():
        return 'New method!'
    """
        
        # Test replacement indices
        indices = self.system._get_indexs_from_text(initial_code, replace_method='another_method')
        self.assertEqual(indices['ref_ix'], (3, 6), "Incorrect indices for replacing 'another_method'")
        # Test insertion after a method
        indices = self.system._get_indexs_from_text(initial_code, below_method='new_method')
        num_lines_in_code = len(initial_code.strip('\n').split('\n'))
        self.assertEqual(indices['ref_ix'], (num_lines_in_code - 1, num_lines_in_code - 1), "Incorrect indices for inserting after 'new_method'")

        # Test replacement indices for a non-existing method
        indices = self.system._get_indexs_from_text(initial_code, replace_method='non_existing_method')
        self.assertEqual(indices['ref_ix'], (None, None), "Expected error message for non-existing method")

        # Test insertion after a non-existing method
        indices = self.system._get_indexs_from_text(initial_code, below_method='non_existing_method')
        self.assertEqual(indices['ref_ix'], (None, None), "Expected error message for non-existing method")
     # self.assertIn("Method non_existing_method not found in the code.", indices, "Expected error message for non-existing method")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
