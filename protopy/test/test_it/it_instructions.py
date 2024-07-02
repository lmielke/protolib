"""
# test_instructions.py
tests the Instructions class
"""

import getpass
import logging
import os
import unittest
from unittest.mock import patch
import yaml

from protopy.gp.data.retrievals import Template
from protopy.gp.experts.experts import Expert

import protopy.settings as sts
import protopy.helpers.collections as hlp

class Test_Instructions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary template file for testing
        pass

    @classmethod
    def tearDownClass(cls):
        # Clean up: Remove the temporary files created for testing
        pass


    def test_expert_instructions(self):
        expert = Expert(name='springmeyer_d')
        print(expert.chat.to_table(verbose=3, use_tags=True, use_names=False, fm='pretty' ))


if __name__ == "__main__":
    unittest.main()
