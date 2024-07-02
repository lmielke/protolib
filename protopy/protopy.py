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
