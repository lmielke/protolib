"""
# test_retrievals.py
tests the Instructions class
"""

import logging
import os
import re
import unittest
from unittest.mock import patch
import yaml

from protopy.gp.data.retrievals import Template
import protopy.settings as sts
import protopy.helpers.collections as hlp


class Task:
    def __init__(self, *args, **kwargs):
        self.name = 'unittest'
        self.role = 'system'
        self.d_assi = 'l3b'

class Test_Template(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary template file for testing
        cls.expert_name, cls.expert_domain = sts.sudo, 'python_programmer'
        cls.task_name = 'file_finder'
        context = {
            'expert_name': cls.expert_name,
            'task_name': cls.task_name,
            'task_description': None,
            'expert_instructions': None,
        }
        cls.owner = Task()

    @classmethod
    def tearDownClass(cls):
        # Clean up: Remove the temporary files created for testing
        pass

    def test_get_template_path(self, *args, **kwargs):
        template = Template(owner=self.owner, t_name=self.owner.name, t_domain=sts.sudo)
        template_path = template.get_template_path(self.owner, )
        self.assertIn(f'{self.owner.name}.md', template_path)

    def test_load_instructs(self):
        template = Template(owner=self.owner, t_name=self.owner.name, t_domain=self.task_name)
        template_path = os.path.join(sts.readme_dir, 'task', 'templates', f"{self.task_name}.md")
        instructs = template.load_instructs(template_path)
        self.assertIn(self.task_name, instructs)

    def test_add_context(self):
        template = Template(owner=self.owner, t_name=self.owner.name, name=self.expert_name, t_domain=self.task_name)
        # template_path = os.path.join(sts.readme_dir, 'expert', 'templates', f"{self.expert_name}.md")
        context = template.add_context(context=self.owner.__dict__)
        self.assertIn(self.owner.name, context['name'])

    def test_render_template(self):
        template = Template(owner=self.owner, t_name=self.owner.name, t_domain=self.expert_domain)
        rendered = template.render_template(context=self.owner.__dict__)
        self.assertIn(f'{self.owner.name}', rendered)

    def test_get_sys_infos(self):
        template = Template(owner=self.owner, t_name=self.owner.name, t_domain=self.expert_domain)
        out = template.get_sys_infos(infos=['package', 'os'])
        self.assertIn('# START info -i PACKAGE #', out)


    def test_get_all_infos(self):
        template = Template(owner=self.owner, t_name=self.owner.name, t_domain=self.expert_domain)
        all_infos = template.get_all_infos()
        expecteds = {'package', 'git_diff', 'project', 'ps_history', 'user_info', 'os_activity', 
                    'network', 'docker', 'python', 'os'}
        matches = re.findall(r'(## START info -i )(\w{2,20})( ##)', all_infos)
        self.assertEqual(expecteds, set([m[1].lower() for m in matches]))

    def test_render_and_save(self):
        # Initialize the Template object

        # Instructions depend on one expert, the task at hand and the description of the task.
        # self.context summarizes the above information.
        template = Template(owner=self.owner, t_name=self.owner.name, name=self.expert_name, t_domain=self.task_name)
        # Render and save the template
        template.render_and_save({}, t_type='state', infos='project')
        # template = Template(owner=self.owner, t_name=self.owner.name, name='programmer', t_domain=self.task_name)
        # # Render and save the template
        # template.render_and_save()

if __name__ == "__main__":
    unittest.main()
