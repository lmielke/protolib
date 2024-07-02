# tool_choice.py

import ast, inspect, json, os, re, sys
from copy import deepcopy
from datetime import datetime as dt
from tabulate import tabulate as tb

import protopy.settings as sts
import protopy.helpers.pretty_printer as ppt

from functools import wraps
from typing import Callable, Dict
import types
from typing import Any

import textwrap

class FunctionToJson:
    """
    Decorator to generate a .json file for any given method by passing in the test_method from
    use:

    from protopy.gp.data.tool_choice import FunctionToJson

    @f_json.open_ai_function(apis={"open_ai_api_",}, write=False,)
    def test_method(self, *args, **kwargs):
        pass
    """
    def __init__(self, *args, **kwargs):
        self.verbose = 0
        self.test_func = None
        self.main_func = None

    def open_ai_function(self, *dec_args, 
                                apis:set=set(), 
                                file_name:str=None, 
                                write:bool=True, 
                                verbose:int=0,
                                **dec_kwargs):
        """
        Produces a .json file for any given method by passing in the test_method from
        a decorator applied to the test_method.
        Example:    @f_json.open_ai_function(apis={"open_ai_api_",}, write=False,)
                    def test_method(self, *args, **kwargs):
                        pass
        Args:
            apis (set): names of apis to include in output file.
                Options:
                    - open_ai_api_
                    - jo_api
            write (bool): write .json file to disk.
                Options:
                    - True
                    - False
        Returns:
            str: The JSON string representation of the method definition parameters.
        """
        self.write = write
        self.verbose = verbose
        self.file_name = file_name

        def decorator(test_func: Callable):
            self.test_func = test_func
            test_class_name, test_method_name = self._get_object_names(test_func)

            @wraps(test_func)
            def wrapper(*args, **kwargs):
                module = inspect.getmodule(test_func)
                self.main_func = self._find_method(test_class_name, test_method_name, module)
                main_module =  inspect.getmodule(self.main_func)
                # class_name = self.get_class_name(self.main_func)
                if self.main_func is None:
                    raise AttributeError((
                                        f"Main func '{test_class_name}.{test_method_name}'"
                                        f" could not be found."
                                        ))
                package_apis = {
                        "base": {
                            "name": self.main_func.__qualname__,
                            "description": self.main_func.__doc__,
                            "import": self.main_func.__module__,
                            "module_path": main_module.__file__,
                            "parameters": {
                                    "type": "object",
                                    "properties": self.func_to_json(self.main_func)},
                            "body": self.get_function_code(self.main_func),
                            "returns": self.handle_returns_inspect(self.main_func),
                            "example": self.get_function_code(test_func)
                        },
                }
                if "jo_api" in apis:
                    package_apis["jo_api"] = {
                        "import": self.main_func.__module__,
                        "api": self.main_func.__name__,
                        "response": self.handle_returns_inspect(self.main_func),
                        "path": main_module.__file__,
                        }
                if "open_ai_api_" in apis:
                    package_apis["open_ai_api_"] = self.map_to_open_ai_function(
                                                                        package_apis["base"]
                                                                        )
                # Parse docstring for additional details
                parsed_docstring = self.parse_docstring(self.main_func.__doc__)
                # Update package_apis to add enum details
                for param, details in parsed_docstring.items():
                    if 'options' in details:
                        if param in package_apis["open_ai_api_"]["parameters"]["properties"]:
                            pars = package_apis["open_ai_api_"]["parameters"]["properties"]
                            options = details['options']
                            pars[param]["enum"] = options if options else []

                json_string = self.dump_to_json(
                                                package_apis,
                                                self.main_func.__module__,
                                                self.main_func.__name__,
                                                write,
                                                verbose,
                                                )
                return test_func(*args, **kwargs)
            return wrapper
        return decorator

    def handle_returns_inspect(self, func, *args, **kwargs) -> str:
        ret = str(inspect.signature(self.main_func).return_annotation)
        # if ret == "<class 'inspect._empty'>":
        #     ret = None
        return ret

    def map_to_open_ai_function(self, open_ai_function: dict) -> dict:
        """
        Maps the given 'open_ai_function' structure to the format expected by OpenAI.

        Args:
            open_ai_function (dict): The original 'open_ai_function' JSON structure.

        Returns:
            dict: The mapped 'open_ai_function' structure.
        """
        type_mappings = {
            "<class 'str'>": "string",
            "<class 'float'>": "number",
            "<class 'int'>": "integer",
            "<class 'dict'>": "object",
            "<class 'list'>": "array",
            "<class 'set'>": "array",
            "<class 'bool'>": "boolean",
            "<class 'inspect._empty'>": "none",
            # Add other mappings as needed
        }
        type_ignoreds = {"object"}

        modified_function = deepcopy(open_ai_function)
        properties = modified_function.get("parameters", {}).get("properties", {})
        required = []

        for param, details in properties.items():
            original_type = details.get("type")
            # Map types
            details["type"] = type_mappings.get(original_type, original_type)
            is_ignored = any([o in details["type"] for o in type_ignoreds])
            # Check if type is not ignored before adding to required
            if details.pop("required", False) and not is_ignored:
                required.append(param)

        # Remove properties with ignored types
        for param, details in deepcopy(properties).items():
            # Remove default values for required parameters
            if any([o in details["type"] for o in type_ignoreds]):
                del properties[param]        # Remove properties with ignored types

        if properties:
            modified_function["parameters"] = {
                "type": "object",
                "properties": properties,
                "required": required
            }
        return modified_function


    def dump_to_json(self, data: Any, dot_import: str, meth_name:str, write:bool, verbose:str=0) -> str:
        """
        Converts a data structure to a JSON string, handling non-serializable objects.

        Args:
            data (Any): The data to be serialized to JSON.

        Returns:
            str: The JSON string representation of the data.
        """
        # print(f"{sts.YELLOW}data: {data}{sts.ST_RESET}")
        def default_serializer(obj):
            """Fallback serializer for objects that JSON can't serialize natively."""
            if isinstance(obj, (type, types.ModuleType)):
                return f"<{obj.__name__}>"
            return str(obj)
        if verbose:
            p = ppt.PrettyPrinter()
            p.pretty_tables(data)
        json_string = json.dumps(data, indent=4, default=default_serializer)
        # safe data as .json file
        def write_to_file(write):
            # if no file_name is provided, save file using the dotted import path
            if write:
                file_name =  f"{dot_import}.{meth_name}" \
                                    if self.file_name is None else self.file_name
                if not file_name.endswith(".json"):
                    file_name += ".json"
                with open(os.path.join(sts.apis_json_dir, file_name), "w") as f:
                    f.write(json_string)
        write_to_file(write)
        return json_string

    def _get_object_names(self, test_func: Callable) -> tuple:
        qualname = test_func.__qualname__
        parts = qualname.split('.')
        if len(parts) > 1:
            cl_name = parts[-2]
            mth_name = parts[-1]
            return cl_name, mth_name
        else:
            raise ValueError("Test function does not appear to be a class method.")

    def _find_method(self, cl_name: str, mth_name: str, module: object) -> Callable:
        """
        Finds a method in a given class within a module, adjusting for test naming 
        conventions.
    
            Args:
                cl_name (str): The name of the class, 'Test_' prefix removed.
                    Options:
                        - FunctionToJson
                        - Test_FunctionToJson
                mth_name (str): The name of the method, 'test_' prefix removed.
                module: The module where the class and method are expected to be found.
    
            Returns:
                Callable: The found method or None if not found.
        """
        cl_name = cl_name.replace('Test_', '')
        mth_name = mth_name.replace('test_', '')
        found_class = getattr(module, cl_name, None)
        if found_class is not None:
            return getattr(found_class, mth_name, None)
        return None

    def get_function_code(self, func: Callable) -> str:
        """
        Extracts the source code of a function, excluding its docstring using re.

        Args:
            func (Callable): The function whose code is to be extracted.

        Returns:
            str: The source code of the function, excluding the docstring.
        """
        lines, _ = inspect.getsourcelines(func)
        # print(f"\n{sts.YELLOW}lines: {lines}{sts.ST_RESET}")

        docStrRegex = "'''|\"\"\""
        ixs = sorted([ix.start() for ix in re.finditer(docStrRegex, ''.join(lines))])

        # Ensure that ixs has two elements, indicating start and end of the docstring
        if len(ixs) >= 2:
            body_lines = [line for ix, line in enumerate(lines) if ix < ixs[0] or ix > ixs[1]]
        else:
            # No docstring found, or docstring format is unexpected
            body_lines = lines

        return ''.join(body_lines).strip()

    def func_to_json(self, func: Callable) -> Dict[str, Dict[str, object]]:
        """
        Extracts function parameters and generates a JSON structure, 
        including a 'required' flag.

        Args:
            func (Callable): The function whose parameters are to be extracted.

        Returns:
            Dict[str, Dict[str, object]]: A dictionary representing the parameters and 
            their attributes.
        """

        params = {}
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            # Handle *args and **kwargs differently
            if param.kind in [param.VAR_POSITIONAL, param.VAR_KEYWORD]:
                continue
            param_type = str(param.annotation) if param.annotation is not inspect._empty \
                                                                                else "object"
            default = param.default if param.default is not inspect._empty else None
            required = param.default is inspect._empty
            params[name] = {
                "type": str(param_type),
                "default": default,
                "required": required
            }
        return params


    def parse_docstring(self, docstring):
        args_section = re.search(r'Args:\n\s+(.*?)(\n\n|\Z)', docstring, re.DOTALL)
        if not args_section:
            return {}

        args_text = args_section.group(1)
        args = {}
        current_arg = None
        options_found = False

        for line in args_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):  # Option for the current argument
                options_found = True
                if current_arg:
                    args[current_arg].setdefault('options', []).append(line[2:])
            else:
                arg_match = re.match(r'(\w+) \((.+?)\): (.+)', line)
                if arg_match:
                    if current_arg and not options_found:
                        args[current_arg]['options'] = None
                    current_arg = arg_match.group(1)
                    options_found = False
                    args[current_arg] = {
                        'type': arg_match.group(2),
                        'description': arg_match.group(3),
                    }
                elif current_arg:  # Handle continuation of the description
                    args[current_arg]['description'] += ' ' + line

        if current_arg and not options_found:
            # args[current_arg]['options'] = None
            pass

        return args
