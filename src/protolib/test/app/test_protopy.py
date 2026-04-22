# testcorepy.py
# C:\Users\lars\python_venvs\packages\protolib\protopy\test\test_ut\testcorepy.py

import logging
import os
import unittest
import yaml

from protolib.app.protopy import DefaultClass
from protolib.helpers.function_to_json import FunctionToJson
import protolib.app.settings as sts

class Test_DefaultClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0

    @classmethod
    def tearDownClass(cls):
        pass

    @FunctionToJson(schemas={"openai"}, write=True)
    def test___str__(self):
        # Update the pg_name passed in if you want, 
        # but the class itself is now likely defaulting to 'protolib'
        pc = DefaultClass(pr_name="protolib", pg_name="protolib", py_version="3.7")
        
        # Change 'protopy' to 'protolib'
        expected = "DefaultClass: self.pg_name = 'protolib'" 
        self.assertEqual(str(pc), expected)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
