# test_protopy.py
import inspect
import logging
import os, re, time
import unittest
import yaml

from protopy.helpers.sys_exec.system import System
import protopy.settings as sts
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_System(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.system = System()
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

    def test_execute(self):
        system = System()
        codes = [f"pipenv run proto info", f"dir", 'dir /AD', 'ls -la']
        system.commands = [{
                            'indicator': '```', 'language': 'shell', #``` is the language used
                            'code': (codes[1]), 
                            'user_confirmed_execution': False
                            }]
        # out = system.confirm_and_run()
        out = system.execute()

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=False,)
    def test_adhog_assist_shell_action(self):
        """
        This is the test docstring
        """
        
        system = System()
        cmds = [
                "dir", 
                "proto clone -pr 'myhammerlib' -n 'myhammer' -a 'myham' -t 'C:/temp' -p '3.10' --install -y"
                ]
        out = system.adhog_assist_shell_action(cmds[0], exec='shell')

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test_adhog_assist_ps_action(self):
        """
        This is an example on how to use adhog_assist_ps_action.
        """
        
        system = System()
        cmds = [
                "$PSVersionTable.PSVersion", 
                "proto clone -pr 'myhammerlib' -n 'myhammer' -a 'myham' -t 'C:/temp' -p '3.10' --install -y"
                ]
        out = system.adhog_assist_ps_action(cmds[0])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
