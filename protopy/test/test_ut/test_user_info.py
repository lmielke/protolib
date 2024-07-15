# test_text.py
"""
Tests the Text class
"""

import unittest
import os
import re
import random as rd
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.helpers.sys_info.user_info import Userhistory


class TestUserhistory(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # text is loaded from sts.test_data_dir/test_text.txt
        cls.verbose = 0

    @classmethod
    def tearDownClass(cls):
        pass


    ###  Tests start here ###

    def test_get_ps_history(self):
        """
        Test the get_ps_history method
        """
        user_hist = Userhistory()
        user_hist.get_ps_history()
        self.assertTrue(len(user_hist.recently_used_cmds) == 100)

if __name__ == "__main__":
    unittest.main()
