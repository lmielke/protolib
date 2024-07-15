"""
NOTE: Most of table tabulate printing is still done from collections.py 
Move to here!
"""

from typing import Any, Dict
import re, textwrap
from tabulate import tabulate as tb


class PrettyPrinter:

    def __init__(self, width: int = 90):
        self.width = width

    def __call__(self, *args, **kwargs):
        data, headers = self.prep_data(*args, **kwargs)
        self.print_table(data, headers=headers)

    def wrap_text(self, text: str) -> str:
        """
        Wrap text to the specified width.

        Args:
            text: The text to be wrapped.

        Returns:
            A string with wrapped text.
        """
        wrapper = textwrap.TextWrapper(width=self.width)
        wrapped_lines = wrapper.wrap(text)
        return '\n'.join(wrapped_lines)

    def prep_data(self, data: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Prepare the data for pretty printing.

        Args:
            data: The data to be prepared.

        Returns:
            The prepared data.
        """
        if 'messages' in data:
            headers = list(data['messages'][0].keys())
            values = [
                        [
                            re.sub( r'(<\|\w+\|>)(\w+)(<\|\w+\|>)', 
                                    r'\1\n\2\n\3', 
                                    d
                            ) for d in msg.values()] for msg in data['messages']]
            return values, headers

    def pretty_tables(self, data: Dict[str, Any], level: int = 0) -> str:
        """
        Create a tabulated representation of a dictionary, including nested dictionaries.

        Args:
            data: The dictionary to convert to a table.
            level: The current level of nesting (used for indentation).

        Returns:
            A string representing the dictionary in tabulated form.
        """
        table = []
        for k, vs in data.items():
            if isinstance(vs, dict):
                # Recursively process nested dictionaries
                table.append([k, self.pretty_tables(vs, level + 1)])
            elif isinstance(vs, str):
                # Wrap long string values
                table.append([k, self.wrap_text(vs)])
            else:
                table.append([k, repr(vs)])
        return self.print_table(table, level)


    def print_table(self, table: str, level: int = 0, headers:list = None) -> str:
        headers = ["Key", "Value"] if headers is None else headers
        tablefmt = "grid" if level == 0 else "simple" if level == 1 else "plain"
        formatted_table = tb(table, headers=headers, tablefmt=tablefmt)

        if level == 0:
            print(f"\n{formatted_table}")
        return formatted_table
