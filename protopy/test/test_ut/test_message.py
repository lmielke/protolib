"""
# test_message.py
tests the Message class
"""

import logging
import os
import unittest
from unittest.mock import patch
import yaml

from protopy.gp.data.content import Content
from protopy.gp.data.message import Message
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_Message(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.color = sts.colors.get(os.getenv('test_color', 'green').upper(), None)

    @classmethod
    def tearDownClass(cls):
        pass

    def test___str__(self):
        # Create a Content instance
        content = Content(text="Hello, World!", instructs="Be polite.")
        message = Message(content=content, name="alice")
        self.assertEqual(
            str(message), 
            f'\x1b[31malice:\x1b[0m  \x1b[36m<INST>\x1b[39m\x1b[0m\n        Be polite.\n        \x1b[36m</INST>\x1b[39m\x1b[0m\n        Hello, World!'
            )
        # Test with a function
        message = Message(content=content, name="bob",)
        self.assertEqual(
            str(message), 
            f'\x1b[31mbob:\x1b[0m  \x1b[36m<INST>\x1b[39m\x1b[0m\n      Be polite.\n      \x1b[36m</INST>\x1b[39m\x1b[0m\n      Hello, World!'
                            )

    def test_dict(self):
        # Prepare a Content instance
        content = Content(text="Hello, World!", instructs="Be polite.")
        
        # Prepare a Message instance using the Content instance
        message = Message(content=content, name="alice",)
        # Convert the Message to a dictionary
        message_dict = message.to_dict()
        # content is tested inside content dataclass
        # del message_dict['content']
        # Verify the structure and content of the dictionary
        self.assertTrue(set(message_dict.keys()).issubset({'name',
                                                            'content',
                                                            'watermark',
                                                            'role',
                                                            'mType',
                                                            'mId'}
                                                ))

    def test_to_table(self):
        # Prepare a Content instance
        content = Content(text="Hello, World!", instructs="Be polite.")
        # Prepare a Message instance using the Content instance
        message = Message(content=content, name="alice",)
        # Convert the Message to a table
        table = message.to_table(use_names=True,)
        # Verify the structure and content of the table
        # print(table)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
