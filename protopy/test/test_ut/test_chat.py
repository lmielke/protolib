"""
# test_content.py
tests the Message class
"""

import logging
import os, tempfile, time
import unittest
from unittest.mock import patch
import yaml

from protopy.gp.data.content import Content
from protopy.gp.data.message import Message
from protopy.gp.data.chat import Chat
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()

# this expert mockup class is used to pass an owner object to chat
class Task:
    def __init__(self, *args, **kwargs):
        self.name = 'unittest'
        self.role = 'system'
        self.d_assi = 'l3b'

class Test_Chat(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.color = sts.colors.get(os.getenv('test_color', 'green').upper(), None)
        cls.test_dir = sts.test_data_dir
        if not os.path.exists(cls.test_dir):
            os.makedirs(cls.test_dir)  # Ensure the test directory exists
        cls.file_path = os.path.join(cls.test_dir, "test_save_chat.pickle")  # Define a class variable for file path
        cls.owner = Task()

    @classmethod
    def tearDownClass(cls):
        # Clean up the file after all tests in the class have run
         chats = [c for c in os.listdir(sts.test_data_dir) if c.endswith('.pickle')][:-1]
         for chat in chats:
                os.remove(os.path.join(sts.test_data_dir, chat))

    def test_to_table(self):
        text = """
        This is a long text that needs to be formatted. It is so long that it needs to be 
        split into multiple lines. 
        - So we will split it into multiple lines. 
        - Even if a bullet point is far to long to be displayed in one single line, it must
        be handled correctly and be displayed approprately.
        - Also code blocks must be colorized.
        
        So here is a code block:
        ```shell
        cd /path/to/directory
        ```
        And the text continues. Here is another code block.
        ```shell
        ls -l
        ```
        Text can contain instructions, which are indicated by using the instruction tags.
        1. Those instructions must be wraped to.
        2. multiple lines if they are too long.
        Instructions however, might not always be shown in the output print.
        """.strip()
        # self.name = 'unittest'
        # self.role = 'system'
        chat = Chat(owner=self.owner, use_tags=False, use_names=False)

        # Alice sends a greeting to Bob
        content_alice_1 = Content(text="Hello, Bob!", instructs="Be polite.", tag="expert")
        message_alice_1 = Message(name="Alice", content=content_alice_1)
        chat.append(message_alice_1)

        # Bob responds to Alice
        content_bob_1 = Content(text="Hi, Alice! How are you?", instructs=None)
        message_bob_1 = Message(name="Bob", content=content_bob_1)
        chat.append(message_bob_1)

        # Alice replies to Bob
        content_alice_2 = Content(text="I'm good, thanks! What about you?", instructs=None)
        message_alice_2 = Message(name="Alice", content=content_alice_2)
        chat.append(message_alice_2)

        # Bob shares his status
        content_bob_2 = Content(text="Doing well, just working on some code.", instructs=None)
        message_bob_2 = Message(name="Bob", content=content_bob_2)
        chat.append(message_bob_2)

        # Alice asks about Bob's code
        content_alice_3 = Content(text="What are you coding?", instructs=None)
        message_alice_3 = Message(name="Alice", content=content_alice_3)
        chat.append(message_alice_3)

        # Bob explains his project
        content_bob_3 = Content(text=f"I'm working on a small shell project.\n{text}", instructs='Read the code carefully.')
        message_bob_3 = Message(name="Bob", content=content_bob_3)
        chat.append(message_bob_3)

        # Alice shows interest
        content_alice_4 = Content(text="Sounds interesting!", instructs=None)
        message_alice_4 = Message(name="Alice", content=content_alice_4)
        chat.append(message_alice_4)

        # Test the to_table method
        # print(f"{chat.messages = }")
        # print(str(chat))
        if self.verbose:
            chat.use_tags = False
            tbl = chat.to_table(verbose=2, 
                                fm='pretty', 
                                tablefmt='grid', 
                                )
            print(f"\ntest_to_table:\n{tbl}")

    def test_save_chat(self):
        """Test saving a Chat object to a specific file using pickle."""
        chat = Chat(owner=self.owner, use_tags=False, use_names=False)
        chat.initialize()
        message = Message(name="Tester", content=Content(text="Testing save."))
        chat.append(message)
        if self.verbose: print(str(chat))
        expected = os.path.join(sts.test_data_dir, f"{sts.session_id}_{'test_load_chat.pickle'}")
        
        try:
            chat.save_chat(sts.test_data_dir, 'test_load_chat.pickle')
            # Ensure the file is written
            self.assertTrue(expected)
            # Check if the file is not empty
            self.assertGreater(os.path.getsize(expected), 0)
        except Exception as e:
            # If there's an error in saving, ensure the test is marked as failed
            self.fail(f"Saving chat failed with error: {e}")

    def test_load_chat(self):
        """Test loading a Chat object from a file and verifying its content."""
        # Assuming the 'test_save_chat' has already run and the file exists
        expected = os.path.join(sts.test_data_dir, f"{sts.session_id}_{'test_load_chat.pickle'}")
        chat = Chat(owner=self.owner, use_tags=False, use_names=False)
        ch = chat.load_chat(sts.test_data_dir, 'test_load_chat.pickle')
        # time.sleep(1)
        # Check that the chat is loaded correctly
        self.assertIsNotNone(ch)
        self.assertEqual(len(ch.messages), 3)
        self.assertEqual(ch.messages[-1].content.text, 'Testing save.')


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
