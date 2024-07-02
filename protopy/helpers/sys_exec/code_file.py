"""
codefile.py
sts.project_dir/protopy/helpers/sys_exec/codefile.py
This module provides the CodeFile class for executing shell and PowerShell commands.
The module also provides functionality for writing and modifying Python modules.
"""
import os, re, subprocess, time
from datetime import datetime as dt
from typing import List, Tuple, Union

from dataclasses import dataclass, field
import protopy.settings as sts

time_stamp = re.sub(r"([: .])", r"-" , f"{dt.now()}")

class CodeFile:

    def __init__(self, *args, **kwargs ) -> None:
        # assistant message fields like self.fields
        self.commands = None

    def __call__(self, msg:dict, *args, **kwargs):
        pass          

    def create_python_module(self, *args, 
                                        content:str, 
                                        module_name:str=f"{time_stamp}_un_named.py",
                                        module_dir:str='protopy/resources',
                                        **kwargs,
        ) -> dict:
        """
        Writes/Overwrites an entire Python module file with content:str (valid python code) 
        in a subdirectory of `sts.project_dir`. PEP8 must be followed.
        Args:
            content (str): The Python code to be written to the file.
                Example: see modified PEP8 info section.
            module_name (str): The name of the Python file to be created.
                Examples:
                - 'settings.py'
                - 'chat.py'
            module_dir (str, optional): The relative directory path from `sts.project_dir` 
                                        where the file will be created.
                                        Defaults to `sts.project_dir/resources` if not provided.

        Returns:
            dict: status = {'status': True/False, 'body': message}
        """
        # module_dir must be a directory inside the package
        module_dir = os.path.join(sts.project_dir, module_dir)
        # we assert that module_dir is a valid directory
        if not os.path.isdir(module_dir):
            return {'status': False, 'body': f'Invalid path: {module_dir}'}
        # we assert that module_name ends with '.py'
        if not module_name.endswith('.py'):
            module_name += '.py'
        # we validate that the content adheres to our modified PEP8
        # black.format_file_in_place(module_name, write_back=black.WriteBack.CHECK)
        with open(os.path.join(module_dir, module_name), 'w') as f:
            f.write(content)
        return {'status': True, 'body': f'File {module_name} created in {module_dir}'}

    def add_python_method(self, *args,
                          content: str,
                          below_method: str = None,
                          replace_method: str = None,
                          module_path: str = 'protopy/resources/unassigned.py',
                          **kwargs
        ) -> dict:
        """
        Inserts or overwrites a python class method in a given python module. Use to extend
        or modify existing classes in the python module.
        Args:
            content (str):  The Python code for the new method to be inserted
                            or used as a replacement.
            below_method (str, optional):   Method name to insert the new content after. 
                                            The content will be added below this method.
            replace_method (str, optional): Method name an existing method to be replaced. 
                                            For new methods, set to None.
            module_path (str):  Path to the Python module file. Always try to provide this!
                                If not provided, content will be added to a unassigned bucket.
        Returns:
            dict: status = {'status': True/False, 'body': message}
        """
        # derive a location in the target class to insert the new method
        if not below_method and not replace_method:
            return {'status': False, 'body': 'Provide below_method or replace_method!'}
        # module_path must be a valid file
        if not os.path.isfile(module_path):
            return {'status': False, 'body': f"File not in {module_path}"}
        # read the original code to be modified
        with open(module_path, 'r') as file:
            code = file.read()
        # either below_method or replace_method must be provided
        # verify that the below_method method exists
        if below_method and ( below_method not in code ):
            return {'status': False, 'body': f"Method {below_method} not in {module_path}"}
        # verify that the replace_method method exists
        if replace_method and ( replace_method not in code ):
            return {'status': False, 'body': f"Method {replace_method} not in {module_path}"}
        # get the indices for modification
        indexs = self._get_indexs_from_text(code, below_method, replace_method)
        # modify the module
        # The content has to adhere to our modified PEP8
        # black.format_file_in_place(module_name, write_back=black.WriteBack.CHECK)
        status_msg = self._modify_python_module( *args,
                                                content=content,
                                                content_meta=indexs,
                                                module_path=module_path,
                                                **kwargs
        )
        return {'status': True, 'body': status_msg}

    def _modify_python_module(self, *args,  content:str,
                                            content_meta:dict, 
                                            module_path:str, **kwargs
        ) -> bool:
        """
        Modifies a existing python codebase by inserting/replacing coding at specified indices
        within the target module.

        Args:
            content (str): The Python code to be inserted.
            content_meta (dict): The start and end indices for the modification.
            module_path (str): The path to the Python module to be modified.

        Returns:
            bool: True if the modification is successful, False otherwise.
        """
        # get idx
        indexs = content_meta.get('ref_ix')
        # Check if module_path is a valid file
        if not os.path.isfile(module_path):
            return f"Invalid path: {module_path}"
        # Read the source code
        with open(module_path, 'r') as f:
            module_code = f.read().split('\n')
        # Adjust conditional index start and end points
        indexs = self._veryfy_indexs(indexs, *args, **kwargs)
        # Split the code into blocks and properly indent content
        # The content has to adhere to our modified PEP8
        # black.format_file_in_place(module_name, write_back=black.WriteBack.CHECK)
        content_blocks = self.prepare_content(content, module_code, indexs, content_meta)
        with open(module_path, 'w') as f:
            f.write('\n\n'.join(['\n'.join(block).strip('\n') for block in content_blocks]))
        return True

    def prepare_content(self, new_code:str, code:list, indexs:list, *args, **kwargs):
        indent, ref_indent = self._get_indent_level(new_code, *args, **kwargs)
        new_code = '\n'.join([l.replace(' '*indent, ' '*ref_indent, 1) for l in new_code.split('\n')])
        new_code = new_code.strip('\n')
        blocks = [code[ :indexs[0]], [f"{new_code}"], code[indexs[1]: ], '\n']
        return blocks

    def _get_indent_level(self, content, content_meta:dict, *args, **kwargs):
        """
        Get the indentation level of the content.
        Args:
            content (str): The content to be analyzed.
        Returns:
            int: The number of spaces used for indentation.
        """
        ref_indent = content_meta[content_meta['ref_method']]['indent']
        for i, line in enumerate(content.split('\n')):
            if len(line) == 0:
                continue
            elif line.strip().startswith('@'):
                continue
            elif re.search(r'^(\s*)(def\s+\w+)', line):
                return re.search(r'^(\s*)(def\s+\w+)', line).group(1).count(' '), ref_indent


    def _get_indexs_from_text(self, 
                                    original_code: str, 
                                    below_method: str = None, 
                                    replace_method: str = None
        ) -> Tuple[Union[int, None], Union[int, None]]:
        """
        Get the start and end indices for inserting or replacing content in the original code.

        Args:
            original_code (str): The original code as a single string.
            below_method (str, optional): Method to insert the new content after.
            replace_method (str, optional): Method to replace with the new content.

        Returns:
            Tuple[Union[int, None], Union[int, None]]: A tuple with start and end indices or None.
        """
        original_code = original_code.strip('\n')
        lines = original_code.split('\n')
        prev_end = 0
        # Create a dictionary with function names and their start and end line numbers
        def _find_end_line(start_line, lines, indents):
            for i, line in enumerate(lines[start_line+1:], 1):
                ind = len(re.search(r'^\s*', line).group())
                if len(line) == 0:
                    last_empty = i
                    continue
                if len(re.search(r'^\s*', line).group()) > indents:
                    continue
                if len(re.search(r'^\s*', line).group()) <= indents:
                    return start_line + i
            return start_line + i + 1

        def _adj_start(start_line, lines):
            for i, line in enumerate(reversed(lines[:start_line])):
                if len(line) == 0:
                    return start_line - i

        def _find_lines(line, lines, *args, **kwargs):
            indention, definition, func_name = line.partition('def')
            start_line = original_code[:match.start()].count('\n') + indention.count('\n')
            indent = len(indention.strip('\n'))
            end_line = _find_end_line(start_line, lines, indent)
            return func_name.strip(), start_line, end_line, indent

        indices, prev_func_name, ref_ix, ref_method = [], None, (None, None), None
        content_meta = {}
        for i, match in enumerate(re.finditer(r'^\s*def\s+\w+', original_code, re.MULTILINE)):
            func_name, start_line, end_line, indent = _find_lines(match.group(), lines)
            if i != 0 and ( start_line != prev_end ):
                start_line = _adj_start(start_line, lines)
            if replace_method and func_name == replace_method:
                ref_ix = (start_line, end_line)
                ref_method = func_name
            elif below_method and prev_func_name == below_method:
                ref_ix = (start_line, start_line)
                ref_method = func_name
            content_meta[func_name] = {
                                            'start': start_line, 
                                            'end': end_line, 
                                            'indent': indent
                                            }
            prev_end, prev_func_name = end_line, func_name
        if below_method and prev_func_name == below_method:
            ref_ix = (content_meta[func_name]['end'], content_meta[func_name]['end'])
            ref_method = func_name
        content_meta['ref_ix'] = ref_ix
        content_meta['ref_method'] = func_name
        return content_meta


    def _veryfy_indexs(self, indexs: tuple, *args, **kwargs) -> tuple:
        """
        Adjusts the start and end points based on the provided indices.

        Args:
            indexs (tuple): A tuple with start and end indices.

        Returns:
            tuple: A tuple with adjusted start and end indices.
        """
        if len(indexs) == 1:
            indexs = (indexs[0], None)
        elif not indexs[1]:
            indexs = (indexs[0], None)
        # we use a text file line index which is 1 based, so we adjust for that
        to_index = indexs[1] if indexs[1] is not None else indexs[0]
        return indexs[0], to_index
