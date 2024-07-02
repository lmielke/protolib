# test_skill.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers

from protopy.gp.data.skill import Skill


class Test_Skill(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        # cls.testData = cls.mk_test_data(*args, **kwargs)
        # cls.msg = f' >>>> NOT IMPLEMENTED <<<< '

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        pass

    @classmethod
    def mk_test_data(cls, *args, **kwargs):
        out = None
        # with open(os.path.join(sts.test_data_dir, "someFile.yml"), "r") as f:
        #     out = yaml.safe_load(f)
        return out

    def test_to_dict(self):
        """Test the to_dict method returns the correct dictionary format."""
        expected_dict = {
                'name': "python",
                'description': "Learn Python basics",
                'standards': "PEP8 Compliance",
            }
        skill = Skill(
                        name="python", 
                        description="Learn Python basics", 
                        standards="PEP8 Compliance"
                )
        result_dict = skill.to_dict()
        self.assertEqual(result_dict, expected_dict, 
            "to_dict should return a dictionary with the correct structure and content.")

    def test_load_instructions(self):
        """Test that load_instructions correctly concatenates loaded instructions."""
        skill = Skill(
                name="python", 
                description="Learn Python basics", 
                standards="PEP8 Compliance"
        )
        expected_instructions = "\nLearn Python basics"  # Replace with the expected result from Template.load
        result_instructions = skill.load_instructions()
        self.assertIn(
                        expected_instructions, result_instructions, 
                        "load_instructions should include the loaded template content.")


if __name__ == "__main__":
    unittest.main()
