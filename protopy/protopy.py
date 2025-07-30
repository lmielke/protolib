"""
protopy.py
This is an example module for a properly formatted Python prototype project.
It contains the DefaultClass used for prototyping Python projects.
"""

# Standard library imports in alphabetical order
import os
import re
import time
from datetime import datetime as dt

# Third-party imports in alphabetical order
import yaml

# Local application imports in alphabetical order
import protopy.settings as sts

class DefaultClass:
    """
    DefaultClass is a class for prototyping Python projects.
    NOTE: **kwargs are critical in this class to allow for the passing of arguments
    """

    def __init__(self, *args, pg_name: str = None, verbose: int = 0, **kwargs) -> None:
        """
        Initializes DefaultClass with the following attributes.

        Args:
            pg_name (str): Name of the project.
            verbose (int): Verbosity level.
                Options:
                    - 0: no output
                    - 1: some output
                    - 2: more output
                    - 3: full output
        """
        self.verbose = verbose
        self.pg_name = pg_name

    def __str__(self, *args, **kwargs) -> str:
        """
        String representation of the DefaultClass instance.

        Returns:
            str: The string representation of the class instance.
        """
        return f"DefaultClass: {self.pg_name = }"
