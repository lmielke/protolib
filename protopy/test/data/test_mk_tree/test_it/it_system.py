# test_protopy.py

import logging
import os
import unittest
import yaml

from protopy.models.system import System
import protopy.settings as sts

class Test_System(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        pass

    @classmethod
    def mk_test_data(cls):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            return yaml.safe_load(f)




    def test___call__(self):
        pass
        # commands = System()(self.content)
        # print(f"\n{Fore.YELLOW}Code blocks: {commands}{Fore.RESET}")

    # def test_get_code_blocks(self):
    #     system = System()
    #     system.get_code_blocks(self.content)
    #     out = system.confirm_and_run()
    #     print(out)

    def test_execute(self):
        system = System()
        codes = [f"pipenv run proto info", f"dir", 'dir /AD', 'ls -la']
        system.commands = [{
                'indicator': '```', 'language': 'shell', 
                'code': (codes[1]), 
                'user_confirmed_execution': True}]
        # out = system.confirm_and_run()
        out = system.execute(system.commands[0].get('code'))
        print(system.comunicate(verbose=1))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
