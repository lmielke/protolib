"""
funcs.py
##################### protopy Tools/Functions #####################
creates chat structure


"""


import json, os, re
from typing import List
import importlib

import protopy.settings as sts
import protopy.helpers.collections as hlp


class Function:
    """
    Manages tools list for OpenAi´s chat prompt. Function list is derrived using 
    OpenAIFunctionGenerator. Decorated Text_methods will be stored as .json
    schema in sts.apis_dir and loaded from there.
    """

    def __init__(self, *args, f_type:str = "function", **kwargs):
        self.name = None # NOTE: only determined after agent responded and get_func_call()
        self.arguments = {}
        self.resulsts = None
        self.type = f_type
        self.tools, self.names = [], []
        self.executables = {}
        self.func_response, self.executable, self.is_safe = None, None, False
        self.exe_out = {'status': None, 'body': None}

    def get_function_data(self, *args, **kwargs) -> List[dict]:
        """
        Collects all functions/json schemas from sts.apis_dir and appends them to
        be used as tools (list) in OpenAi´s chat prompt
        Example: tools [{function1}, {function2}, ...]
        """
        for json_obj in self.load_apis_json(*args, **kwargs):
            function = json_obj.get(sts.open_ai_func_prefix)
            if function is not None:
                self.append_executables(function)
                del function['body']
                self.names.append(function['name'])
                function['name'] = function['name'].split('.')[-1]
                self.tools.append( {"type": self.type, "function": function,} )
        return self.tools

    def append_executables(self, function:dict, *args, **kwargs):
        """
        When the assistant returns a response, it contains a function name and its
        calling parameters. The executables are needed then to import and run the funciton.
        """
        
        self.executables[function.get('name').split('.')[-1]] = {
                                        'name': function.get('name'),
                                        'class_name': function.get('name').split('.')[0],
                                        'import': function.get('import'),
                                                    }

    def load_apis_json(self, *args, **kwargs):
        """
        Loads all .json files from sts.apis_dir and returns them as a list of dicts
        """
        contents = []
        for filename in os.listdir(sts.apis_json_dir):
            if filename.endswith(sts.json_ext) and not filename.startswith('#'):
                with open(os.path.join(sts.apis_json_dir, filename), 'r') as file:
                    contents.append(json.load(file))
        return contents

    def get_func_call(self, tool_calls:list=None, *args, **kwargs):
        """
        Function call arguments are converted to Function properties here for each prompt.
        Expected properties:
            'name': str, name of function that was called by the model
            'arguments': list[str], arguments of the function that was called
            'type': str tbd'
        """ 
        if tool_calls is None:
            return None
        for k, vs in json.loads(tool_calls[0].function.arguments).items():
            # print(f"{k = }, {vs = }, {type(vs) = }")
            if type(vs) == str:
                self.arguments[k] = vs.replace("'", "").strip()
            else:
                self.arguments[k] = vs
        self.name = tool_calls[0].function.name
        self.executable = self.executables[self.name]
        self.is_safe = self.inspect_function(*args, **kwargs)
        return True

    def inspect_function(self, *args, **kwargs):
        """
        Add some checks here
        """
        return True

    def execute(self, *args, **kwargs):
        if not self.executable: return None
        out = {}
        out.update(getattr(
                            (
                            importlib.import_module(self.executable.get('import'))
                            .__dict__.get(self.executable.get('class_name'))
                            )(),
                            self.name
                    )(**self.arguments))
        out['msg'] = (
                    f"{sts.GREEN if out['status'] == True else sts.RED}"
                    f"Function executed{sts.RESET}: {self.name}! "
                    )
        return out
