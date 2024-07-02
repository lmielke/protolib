# test_protopy.py

import logging
import os, subprocess
import unittest
import yaml

import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()

from protopy.gp.experts.experts import Expert
from protopy.gp.models.openai.prompt import Prompt


class Test_Prompt(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.model = 'gpt-3.5-turbo-0125'

    @classmethod
    def tearDownClass(cls):
        pass

    # @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)
    def test___init__(self):
        # prompts require a chat to be created
        expected = "Instructions for unittest Protolib python template"
        instructs = "This is a unittst. You are Ut_blue! Continue the conversation!"
        ut = Expert(name='unittest', color='green')
        ut_blue = Expert(name='ut_blue', color='blue', instructs=instructs)
        ut.speak("<instructions> You are ut_blue! Continue the conversation! </instructions> /nPing!, Say Pong!'")
        # instantiate a prompt object to be called
        ut_blue.to_dict = lambda **kwargs: ut_blue.chats['master'].to_dict()
        prompt = Prompt(ut_blue)
        r = prompt(
                        chat=ut_blue.chats['master'],
                        function='auto',
                        temperature=0.0,
                        model=self.model
                    )
        if self.verbose: print(f"\n{r.get('content') = }")
        ut_blue._think(prompt.response.content)
        # prompt can take a temperature and model, if not proviced defaults apply
        if self.verbose: print(f"\nTest_Prompt.___init__\n{str(ut_blue.chats['master'])}")
        # self.assertIn('conversation', prompt.response.content)
        if self.verbose: print(f"\nTest_Prompt.___init__\n{prompt.response.__dict__}")
        ut.speak("List all my files for the current directory!")
        ut_blue.to_dict = lambda **kwargs: ut_blue.chats['master'].to_dict()
        r = prompt(
                        chat=ut_blue.chats['master'],
                        function='auto',
                        temperature=0.0,
                        model=self.model
                    )
        # if model responds it should have a 'done' parameter set to True inside response
        self.assertTrue(prompt.response.done)
        ut_blue._think(prompt.response.content)
        if self.verbose: print(f"\nTest_Prompt.___init__\n{prompt.response.__dict__}")
        if self.verbose: print(f"\nTest_Prompt.___init__\n{str(ut_blue.chats['master'])}")
        if self.verbose: print(f"\nTest_Prompt.function:\n{prompt.function.name}")
        if self.verbose: print(f"\nTest_Prompt.function.arguments:\n{prompt.function.arguments}")
        if self.verbose: print(prompt.response.function.arguments)
        if prompt.response.function.arguments:
            shell_out = subprocess.run(
                                    f"powershell -Command {prompt.response.function.arguments['cmd']}",
                                    text=True, 
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                    )
            if shell_out.stdout:
                if self.verbose: print(f"OK: {shell_out.stdout = }")
            elif shell_out.stderr:
                if self.verbose: print(f"ERR: {shell_out.stderr}")
            else:
                if self.verbose: print('no os response')
        


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
