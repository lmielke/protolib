# test_protopy.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
from protopy.helpers.module_structure import Module
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers
import logging


class Test_Module(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        cls.testData = cls.mk_test_data(*args, **kwargs)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        pass

    @classmethod
    def mk_test_data(cls, *args, **kwargs):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            out = yaml.safe_load(f)
        return out

    def test_lint_python_code(self, *args, **kwargs):
        md = Module(module_path=os.path.join(sts.test_dir, 'test_module.py'))
        print(f"{f' Module 0':#^80}")
        md.lint_python_code(coding='')
        for line in md.contents.split('\n'):
            print(line)
        print(f"{f' Module 1':#^80}")
        md.contents = md.contents.replace('test_module', 'test_module2').replace('Default', 'Default2')
        md.lint_python_code(coding=md.contents)
        for line in md.contents.split('\n'):
            print(line)
        print(f"{f' Module 2':#^80}")
        md.contents = md.contents.replace('\n# test_module2', '# test_module3')
        md.lint_python_code(coding=md.contents)
        for line in md.contents.split('\n'):
            print(line)
        print(f"{f' Module 3':#^80}")
        coding = (
                    f'\n\nclass MyClass:\n    '
                    f'"""This is a class doc_string"""\n    print(MyClass)\n'
                )
        contents = f'"""test_module.py\nThis is a module doc string!"""' + coding
        md.lint_python_code(coding=contents)
        for line in md.contents.split('\n'):
            print(line)

if __name__ == "__main__":
    unittest.main()
