# test_protopy.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
from protopy.helpers.package_info import dirs_to_tree, tree_to_dirs, mk_dirs_hierarchy
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

    @helpers.test_setup(temp_file=None, temp_chdir='temp_file', temp_pw=None) 
    def test_mk_dirs_hierarchy(self, *args, **kwargs):
        """
        This test runs a full circle from an existing directory hierarchy via a print
        representation then via a path list to a recreated directory hierarchy. 
        The recreated hierarchy is then compared to the original one.
        """
        # convert the original hierarchy to a print representation (tree)
        expected_tree = dirs_to_tree(os.path.join(sts.test_dir), ignores={'data'})
        # print(f"{expected_tree}\n")
        # convert the printable representation (expected_tree) to a list of relative paths
        dirs = tree_to_dirs(expected_tree)
        # re-create the orignal hierarchy using the list of paths
        mk_dirs_hierarchy(dirs, os.getcwd())
        # now convert the resulting hierarchy back to a print representation for comparison
        out_tree = dirs_to_tree(os.path.join(os.getcwd(), 'test'), ignores={'data'})
        # dirs to expected_tree has shortened directories which are represented by |...
        # those shorteners can not be created, therefore have to be removed
        expected_tree = '\n'.join([l for l in expected_tree.split('\n') if not '|...' in l])
        out_tree = '\n'.join([l for l in out_tree.split('\n') if not '|...' in l])
        # print(f"{out_tree}\n")
        # print(f"test_tree_to_dirs: \n{out_tree}\n")
        time.sleep(.1)
        self.assertEqual(expected_tree, out_tree)

if __name__ == "__main__":
    unittest.main()
