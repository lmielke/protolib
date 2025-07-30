# test_protopy.py
# C:\Users\lars\python_venvs\packages\protolib\protopy\test\test_ut\test_protopy.py

import logging
import os
import unittest
import yaml

from protopy.protopy import ExampleClass
from protopy.helpers.function_to_json import FunctionToJson
import protopy.settings as sts

class Test_ExampleClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0

    @classmethod
    def tearDownClass(cls):
        pass

    @FunctionToJson(schemas={"openai"}, write=True)
    def test___str__(self):
        pc = ExampleClass(pr_name="protolib", pg_name="protopy", py_version="3.7")
        expected = "ExampleClass: protopy"
        self.assertEqual(str(pc), expected)
        logging.info("Info level log from the test")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
