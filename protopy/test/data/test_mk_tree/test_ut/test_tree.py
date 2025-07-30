# test_protopy.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
from protopy.helpers.tree import Tree
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers
import logging


class Test_Tree(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        cls.testData = cls.mk_test_data(*args, **kwargs)
        cls.tree = '''
                        <hierarchy>
                        |--▼ test
                            |-testhelper.py
                            |- __init__.py
                            |--▼ data
                                |-empty.txt
                                |-protopy.yml
                            |... ▼ __pycache__
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

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        pass

    @classmethod
    def mk_test_data(cls, *args, **kwargs):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            out = yaml.safe_load(f)
        return out

    def test__normalize_tree(self, *args, **kwargs):
        """
        test the _normalize_tree function
        """
        expected = '''
<hierarchy>
|--▼ test
    |-testhelper.py
    |- __init__.py
    |--▼ data
        |-empty.txt
        |-protopy.yml
    |... ▼ __pycache__
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

        tree = Tree()
        normalized = tree._normalize_tree(self.tree)
        print(f"test__normalize_tree: \n{normalized}\n")
        self.assertEqual(normalized, expected.strip())

    def test_mk_tree(self, *args, **kwargs):
        """
        test the mk_tree function
        """
        time.sleep(.3)
        tree = Tree(dir_conn="|--", file_conn="|-", dir_symbol="▼")
        project_tree = tree.mk_tree(sts.test_data_dir, 'test_mk_dirs_hierarchiy')
        print(f"test_mk_tree: \n{project_tree}\n")
        self.assertEqual(
                            tree._normalize_tree(project_tree).strip(), 
                            tree._normalize_tree(self.tree).strip()
                            )
        # self.assertEqual(test_tree, self.testData["testDirsToTree"])

    def test_parse_tree(self, *args, **kwargs):
        """
        test the parse_tree function
        """
        expected = [
                    ('test', True),
                    ('test\\testhelper.py', False),
                    ('test\\__init__.py', False),
                    ('test\\data', True),
                    ('test\\data\\empty.txt', False),
                    ]
        tree = Tree()
        dirs = tree._parse_tree(self.tree)
        print(f"dirs:\n{dirs}\n")
        print(f"{expected}\n")
        self.assertEqual(dirs[:5], expected)



    # def test__decolorize_tree(self, *args, **kwargs):
    #     """
    #     test the dirs_to_tree function
    #     """
    #     test_dir = os.path.join(sts.test_dir)
    #     test_tree = dirs_to_tree(test_dir)
    #     decolorized = _decolorize_tree(test_tree)
    #     print(f"test_dirs_to_tree: \n{decolorized}\n")
    #     # self.assertEqual(test_tree, self.testData["testDirsToTree"])

    @helpers.test_setup(temp_file=None, temp_chdir='temp_file', temp_pw=None)
    def test_mk_dirs_hierarchiy(self, *args, **kwargs):
        """
        test the mk_dirs_hierarchy function
        """
        tree = Tree()
        dirs = [
                    ['test', True],
                    ['test\\testhelper.py', False],
                    ['test\\__init__.py', False],
                    ['test\\data', True],
                    ['test\\data\\empty.txt', False],
                    ]
        start_dir = tree.mk_dirs_hierarchy(dirs, os.getcwd())
        print(f"start_dir: {start_dir}")
        time.sleep(time.sleep(.5))
        self.assertTrue(os.path.isfile(dirs[-1][0]))
        

if __name__ == "__main__":
    unittest.main()
