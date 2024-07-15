# test_protopy.py

import logging
import os, platform, subprocess
import unittest
import yaml

import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()

from protopy.gp.experts.experts import Expert
from protopy.gp.models.openai.prompt import Prompt


# this task mockup class is used to pass an owner object to chat
class Task:
    def __init__(self, *args, **kwargs):
        self.name = 'unittest'
        self.role = 'system'
        self.d_assi = 'l3b'

class Test_Prompt(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.model = 'gpt-3.5-turbo-0125'
        loc_assi_server_running = Test_Prompt.is_server_running(1)
        if not loc_assi_server_running:
            msg = f"{sts.RED}Assistant server not running{sts.RESET}"
            raise Exception(f"Test_Prompt.setUpClass: {msg}")

    @classmethod
    def tearDownClass(cls):
        pass

    @staticmethod
    def is_server_running(id:int):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', f"{os.environ['NETWORK']}{id}"]
        
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            return True
        except subprocess.CalledProcessError:
            return False

    # @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test___init__(self, *args, **kwargs):
        owner = Task()
        prompt = Prompt(owner, *args, d_assi=owner.d_assi, **kwargs)
        print(f"Test_Prompt.__init__: {prompt.msg = }")

    def test_to_table(self, *args, **kwargs):
        owner = Task()
        prompt = Prompt(owner, *args, d_assi=owner.d_assi, **kwargs)
        context = { 'messages': [
                                {'role': 'user', 'content': 'Hi there!'},
                                {'role': 'user', 'content': 'Hi back!'},
                                {'role': 'unittest', 'content': 'This is unittest!'},
                                ],
                    }
        prompt.to_table(context, verbose=2)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
