"""
# test_content.py
Tests the Content class
"""

import logging
import os
import unittest
from unittest.mock import patch
import yaml

from protopy.gp.data.content import Content
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.texts import Text  # Import the Text class
from protopy.gp.data.tool_choice import FunctionToJson

f_json = FunctionToJson()

class Test_Content(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.color = sts.GREEN
        cls.text = """
        This is a long text that needs to be pretty. It is so long that it needs to be 
        split into multiple lines. So we will split it into multiple lines. 
        1. This is a list item that should remain on a separate line.
        2. This is another list item that should remain on a separate line. But its very long,
        so it will be split into multiple lines.
        - even if it is not a number but a regular dash, it should be treated as a bullet point
        Also code blocks must be colorized.
        ```shell
        cd /path/to/directory
        ```
        And the text continues. Here is another code block.
        ```shell
        ls -l
        ```
         To list all the files in the current working directory (CWD), you can use the    |
        `os.listdir()` method in Python. Here's an example script:
        ```python
        import os
        def list_files():
        print("Files in CWD:")
        for file in os.listdir():
        print(file)
        if __name__ == "__main__":
        list_files()
        ```
        Run this script, and it will print out a list of all the files in your current
        working directory.
        Text can contain instructions, which are indicated by using the <instructions> tags.
        Instructions however, might not always be shown in the output print.
        """.strip()

    def test___str__(self):
        content_no_instructs = Content(text='Hello World!', instructs='Be polite')
        # print('with instructs:\n', str(content_no_instructs))
        # self.assertEqual(str(content_no_instructs), content_no_instructs.prettyfy())

    @patch('builtins.input', side_effect=['', '', 'Hello'])
    def test_get_input(self, mock_input):
        ct = Content()
        self.assertEqual(ct.get_input(), 'Hello')

    def test_get_code_blocks(self):
        content = Content(text=self.text)
        expected_code_blocks = {
            '<code_block_0>': ('shell', 'cd /path/to/directory'),
            '<code_block_1>': ('shell', 'ls -l')
        }
        preped = {k: (v[0], v[1]) for k, v in content.code_blocks.items()}
        # self.assertEqual(preped, expected_code_blocks)

    def test_construct(self):
        content = Content(text=self.text)
        pretty = content.construct(fm='pretty', use_tags=True)
        # print(pretty)
        # print(f"{type(pretty) = }")
        self.assertTrue(pretty.strip().startswith(self.text.strip()[:20]))

if __name__ == "__main__":
    unittest.main()