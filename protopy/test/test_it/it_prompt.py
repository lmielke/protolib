# test_protopy.py

import logging
import os, subprocess
import unittest
import yaml
import Levenshtein

import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()

from protopy.gp.experts.experts import Expert
from protopy.gp.models.openai.prompt import Prompt
from protopy.apis.ask import main as ask_main


class Test_Prompt(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.model = 'gpt-3.5-turbo-0125'

    @classmethod
    def tearDownClass(cls):
        pass

    # helper functions
    def assertSimilar(self, str1: str, str2: str, max_distance: int = 2) -> None:
        """Asserts that two strings are similar within a certain Levenshtein distance.
        
        Args:
            str1: (str) The first string.
            str2: (str) The second string.
            max_distance: (int) The maximum allowed Levenshtein distance for strings to be considered equal.
        """
        distance = Levenshtein.distance(str1, str2)
        self.assertLessEqual(distance, max_distance, 
                             f'Strings "{str1}" and "{str2}" are not similar enough (distance={distance}).')


    ## TEST STARTS HERE ##
    def test_info_visible(self):
        q = lambda info: f"""
        This prompt is to test the readability of instructions provided in the prompt.
        At specific positions within the text, you will find a '{sts.check_quest}' 
        together with a {sts.check_answ}. 
        Note: The {sts.check_answ} purposefully is a very specific but cryptic answer.
        Be precise when citing the {sts.check_answ} in your response. 
        Example:
        {sts.check_vals['USER_INFO'][0]}: {sts.check_vals['USER_INFO'][1]}
        Lets start! 
        What is the {sts.check_answ} for {sts.check_quest} {info}? Give me only the answer. Do not explain your reasoning.
        """
        # print(f"Prompt: {q}")
        infos = ['OS', 'USER_INFO']
        for info in infos:
            answer = ask_main(question=q(info), regex=1, infos=[info])
            expected = sts.check_vals[info][1]
            # NOTE: expected might not be an exact match, so we allow for some tolerance
            self.assertSimilar(expected, answer.strip(), 2)
        # ask_main(question=q, regex=1, infos=['os'])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
