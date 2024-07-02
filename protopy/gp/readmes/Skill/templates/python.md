# Our Modified PEP8 Style Guide

This section outlines modifications to the traditional PEP8 style guidelines specifically tailored to our project's needs.

{{ context['description'] }}

# Standards Examples

Below are examples that illustrate how our modified standards should be applied in practice.

{{ context['standards'] }}

# Sample Python

## Standard Module
The following example shows a Python module that adheres to our modified PEP8 standards.

```python
"""
protopy.py
This is an example module for a properly formatted Python prototype project.
It contains the Protopy used for prototyping Python projects.
"""

# Standard library imports in alphabetical order
import os
import re
import time
from datetime import datetime as dt

# Third-party library imports in alphabetical order
import yaml

# Local application imports in alphabetical order
import protopy.settings as sts


class Protopy:
    """
    Protopy is a class for prototyping Python projects.
    NOTE: *args, **kwargs are critical in this class to allow for the passing of arguments
    """

    def __init__(self, *args, pr_name: str, py_version:str, verbose: int = 0, **kwargs) -> None:
        """
        This is a Google style python docstring. 
        Here gpes a description, what the class does.
        Describe the Object and its purpose. 
        Why do we need it?

        Args:
            pr_name (str): Name of the project.
            verbose (int): Verbosity level.
                Options:
                    - 0: no output
                    - 1: some output
                    - 2: more output
                    - 3: full output
        """
        self.verbose = verbose
        self.pr_name = pr_name

    def __str__(self, *args, **kwargs) -> str:
        """
        String representation of the Protopy instance.

        Returns:
            str: The string representation of the class instance.
        """
        return f"Protopy: {self.pr_name}"

```

## Standard Test_Module
The following example shows a Python test_module that adheres to our modified PEP8 standards.

```python
# test_protopy.py

import logging
import os
import unittest
import yaml

from protopy.protopy import Protopy
import protopy.settings as sts

class Test_Protopy(unittest.TestCase):
    """
    Note how the Test module is named. It should start with Test_ and the name of the module being tested.
    """
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        cls.testData = cls.mk_test_data()# if needed

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def mk_test_data(cls):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            return yaml.safe_load(f)

    def test___str__(self):
        """
        Test the __str__ method returns the correct string format.
        """
        pc = Protopy(pr_name="protopy", py_version="3.7")
        expected = "Protopy: protopy"
        self.assertEqual(str(pc), expected)
        logging.info("Info level log from the test")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
```

NOTE: Adherence to these guidelines is critical and therefore enforced using:
```python
    black.format_file_in_place('protopy.py', write_back=black.WriteBack.CHECK)
```
