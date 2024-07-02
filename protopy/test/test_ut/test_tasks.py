# test_n_tasks.py

import logging
import os
import unittest
import yaml

from protopy.gp.experts.tasks import Task
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_Task(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def mk_test_data(cls):
        file_name = os.path.basename(__file__).split(".")[0]
        with open(os.path.join(sts.test_data_dir, f"{file_name}.yml"), "r") as f:
            return yaml.safe_load(f)

    # @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)

    def test___init__(self):
        # a software solution is a composition of Features to be implemented
        # every Feature is a composition of Tasks to be completed
        expected = {'task_name', sts.sudo,'programmer', 'architect', 'task_instructions', 'assembly_ix'}
        task = Task(name="file_finder", verbose=0, expert_names=[sts.sudo, 'programmer', 'architect'])
        # print(task.instructs)
        self.assertIn('file_finder', task.instructs)



    # def test_get_instructions(self,):
    #     # instructions are already set during initialization
    #     expected = "#Feature:  __'file_finder'__, Assembly Index: medium"
    #     task = Task(task_name="file_finder", instructs=None)
    #     self.assertIn(expected, task.task_instructions)
    #     # instructions can be provided using the get_instructions method
    #     expected = "# PROJECT info #"
    #     out = task.get_instructions(template_type='state', info='project')
    #     self.assertIn(expected, out)

    # def test_add_experts(self):
    #     # experts are added to the task
    #     sts.experts = {}
    #     task = Task(task_name="file_finder", instructs=None)
    #     experts = task.add_experts(expert_names=[sts.sudo,])
    #     self.assertEqual(sts.experts.get(sts.sudo), experts.get(sts.sudo))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
