# test_protopy.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
from protopy.helpers.package_info import dirs_to_tree, tree_to_dirs, mk_dirs_hierarchy, _decolorize_tree
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers
import logging


class Test_Unittest(unittest.TestCase):
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

    def test_dirs_to_tree(self, *args, **kwargs):
        """
        test the dirs_to_tree function
        """
        test_dir = os.path.join(sts.test_dir)
        test_tree = dirs_to_tree(test_dir)
        print(f"test_dirs_to_tree: \n{test_tree}\n")
        # self.assertEqual(test_tree, self.testData["testDirsToTree"])

    def test__decolorize_tree(self, *args, **kwargs):
        """
        test the dirs_to_tree function
        """
        test_dir = os.path.join(sts.test_dir)
        test_tree = dirs_to_tree(test_dir)
        decolorized = _decolorize_tree(test_tree)
        print(f"test_dirs_to_tree: \n{decolorized}\n")
        # self.assertEqual(test_tree, self.testData["testDirsToTree"])

    def test_tree_to_dirs(self, *args, **kwargs):
        """
        test the tree_to_dirs function
        """
        tree = '''
        <hierarchy>
        |--▼ test
            |-testhelper.py
            |- __init__.py
            |--▼ data
                |-empty.txt
                |-protopy.yml
            |-- ▼ logs
                |...
            |-▼ testopia_logs
                |-2024-01-12-14-26-24-796531_test_protopackage.log
                |...
            |-  ▼ test_it
                |-test_package_info.py
                |-__init__.py
            |--▼ test_ut
                |-test_package_info.py
                |-test_protopy.py
                |-__init__.py
        </hierarchy>
        '''
        expected = [
                    ['test', True],
                    ['test\\testhelper.py', False],
                    ['test\\__init__.py', False],
                    ['test\\data', True],
                    ['test\\data\\empty.txt', False],
                    ]
        dirs = tree_to_dirs(tree)
        self.assertEqual(dirs[:5], expected)

    @helpers.test_setup(temp_file=None, temp_chdir='temp_file', temp_pw=None)
    def test_mk_dirs_hierarchiy(self, *args, **kwargs):
        """
        test the mk_dirs_hierarchy function
        """
        dirs = [
                    ['test', True],
                    ['test\\testhelper.py', False],
                    ['test\\__init__.py', False],
                    ['test\\data', True],
                    ['test\\data\\empty.txt', False],
                    ]
        mk_dirs_hierarchy(dirs, os.getcwd())
        self.assertTrue(os.path.isfile(dirs[-1][0]))
        

if __name__ == "__main__":
    unittest.main()
