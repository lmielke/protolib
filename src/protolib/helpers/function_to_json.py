"""
script_path: src/protolib/helpers/function_to_json.py
purpose: >-
  Introspect Python callables and emit JSON-Schema-style descriptors for use by the
  protolib registry and client packages.
description: |-
  Parses signatures, docstrings, and
  type annotations to produce machine-readable API contracts. Used by expose_api
  and the registry introspector. Do not modify in clones — synced from upstream.
"""
import inspect, json, os, re, sys, textwrap, types
from copy import deepcopy
from functools import wraps
from typing import Any, Callable, Dict

import protolib.app.settings as sts
from dataclasses import dataclass, asdict

PY2JSON: dict[type, str] = {
    str: "string", int: "integer", float: "number",
    bool: "boolean", list: "array", dict: "object", type(None): "null",
}
_ARG_RE = re.compile(r'(\w+) \((.+?)\): (.+)')


@dataclass
class BaseSchema:
    name: str = ""
    description: str = ""
    import_path: str = ""
    module_path: str = ""
    parameters: dict[str, Any] = None
    body: str = ""
    returns: str = ""
    example: str = ""

    @classmethod
    def set_fields(cls, main_meth, test_meth, parsed_props, *args, **kwargs):
        return cls(name=main_meth.__qualname__, description=main_meth.__doc__,
                   import_path=main_meth.__module__,
                   module_path=inspect.getmodule(main_meth).__file__,
                   parameters={"type": "object", "properties": parsed_props},
                   body=cls.get_function_code(main_meth),
                   returns=cls.handle_returns_inspect(main_meth),
                   example=cls.get_function_code(test_meth))

    @staticmethod
    def get_function_code(func: Callable, *args, **kwargs) -> str:
        lines, _ = inspect.getsourcelines(func)
        src = ''.join(lines)
        ixs = sorted(m.start() for m in re.finditer("'''|\"\"\"", src))
        if len(ixs) >= 2:
            lines = [l for i, l in enumerate(lines) if i < ixs[0] or i > ixs[1]]
        return ''.join(lines).strip()

    @staticmethod
    def handle_returns_inspect(func: Callable, *args, **kwargs) -> str:
        ann = inspect.signature(func).return_annotation
        if ann is inspect._empty:
            return "object"
        return PY2JSON.get(ann, str(ann))

    def to_dict(self, *args, **kwargs) -> dict:
        return self.__dict__


@dataclass
class OpenaiSchema:
    """
    purpose: Minimal schema for OpenAI tool-calling.
    """
    name: str = ""
    description: str = ""
    parameters: dict[str, Any] | None = None
    returns: str = ""

    @staticmethod
    def _required(props, *args, **kwargs):
        return [n for n, m in props.items()
                if m.get("required") and m.get("type") != "object"]

    @staticmethod
    def _clean(props, *args, **kwargs):
        return {n: {k: v for k, v in m.items() if k != "required"} for n, m in props.items()}

    @classmethod
    def set_fields(cls, main_meth, test_meth, parsed_props, *args, **kwargs):
        required = cls._required(parsed_props)
        _apply_enum_options(main_meth, parsed_props)
        clean = cls._clean(parsed_props)
        src = textwrap.dedent(inspect.getsource(main_meth).strip())
        return cls(name=main_meth.__qualname__, description=src,
                   parameters={"type": "object", "properties": clean, "required": required},
                   returns=BaseSchema.handle_returns_inspect(main_meth))

    def to_dict(self, *args, **kwargs) -> dict:
        return {
            "name": self.name, "description": self.description,
            "parameters": self.parameters, "returns": self.returns,
        }


@dataclass
class ExecutionInfo:
    import_path: str
    module_path: str

    @classmethod
    def set_fields(cls, main_meth: Callable, *args, **kwargs) -> "ExecutionInfo":
        return cls(
            import_path=main_meth.__module__,
            module_path=inspect.getmodule(main_meth).__file__,
        )

    def to_dict(self, *args, **kwargs) -> dict:
        return asdict(self)


@dataclass
class JoSchema:
    api: str
    response: str
    path: str

    @classmethod
    def set_fields(cls, main_meth: Callable, *args, **kwargs) -> "JoSchema":
        return cls(
            api=main_meth.__name__,
            response=BaseSchema.handle_returns_inspect(main_meth),
            path=inspect.getmodule(main_meth).__file__,
        )

    def to_dict(self, *args, **kwargs) -> dict:
        return asdict(self)


class FunctionToJson:

    def __init__(self, *args, schemas=None, file_name=None, write=True, verbose=0, **kwargs):
        self.schemas = schemas or set()
        self.file_name = file_name
        self.asts = {}

    def __call__(self, test_meth: Callable, *args, **kwargs) -> Callable:
        @wraps(test_meth)
        def wrapper(*args, **kwargs):
            main_meth = self._find_method(*self._get_object_names(test_meth))
            self.get_asts(main_meth, test_meth)
            self.dump_to_json(main_meth.__module__, main_meth.__name__, *args)
            return test_meth(*args, **kwargs)
        return wrapper

    def _get_object_names(self, test_meth: Callable, *args, **kwargs) -> tuple:
        try:
            cl_name, mth_name = test_meth.__qualname__.split('.')
            if cl_name and mth_name:
                return cl_name, mth_name, inspect.getmodule(test_meth)
        except Exception:
            raise ValueError(f"Invalid method name '{test_meth.__qualname__}'.")

    def _find_method(self, cl_name, mth_name, module, *args, **kwargs):
        found_class = getattr(module, cl_name.replace('Test_', ''), None)
        if not found_class:
            raise AttributeError(f"Class '{cl_name}' not found in '{module.__name__}'.")
        return getattr(found_class, mth_name.replace('test_', ''), None)

    def get_asts(self, *args, **kwargs) -> dict[str, dict]:
        meth_props = self.read_signature(*args)
        self.asts['base'] = BaseSchema.set_fields(*args, meth_props).to_dict()
        self.asts['execution'] = ExecutionInfo.set_fields(*args).to_dict()
        self._resolve_schemas(*args, meth_props=meth_props, **kwargs)

    def _resolve_schemas(self, *args, meth_props=None, **kwargs):
        for schema in self.schemas:
            sch = getattr(sys.modules[__name__], f"{schema.capitalize()}Schema", None)
            if not sch:
                raise AttributeError(f"Schema class '{schema}' not found.")
            self.asts[schema] = sch.set_fields(*args, deepcopy(meth_props)).to_dict()

    @staticmethod
    def read_signature(func: Callable, *args, **kwargs) -> dict[str, dict[str, object]]:
        props = {}
        for name, p in inspect.signature(func).parameters.items():
            if name in {"self", "cls"} or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                continue
            props[name] = _param_schema(p)
        return props

    def dump_to_json(self, dot_import: str, m_name: str, write: bool, *args, **kwargs) -> None:
        if not write:
            return
        file_name = self._resolve_filename(dot_import, m_name)
        path = os.path.join(sts.apis_json_dir, file_name)
        with open(path, "w") as f:
            f.write(json.dumps(self.asts, indent=4, default=_default_serializer))

    def _resolve_filename(self, dot_import, m_name, *args, **kwargs):
        name = f"{dot_import}.{m_name}" if self.file_name is None else self.file_name
        return name if name.endswith(".json") else name + ".json"

    @staticmethod
    def parse_docstring(docstring, *args, **kwargs):
        args_section = re.search(r'Args:\n\s+(.*?)(\n\n|\Z)', docstring or '', re.DOTALL)
        if not args_section:
            return {}
        return _parse_arg_lines(args_section.group(1))


# ---------- module-level helpers ----------

def _apply_enum_options(main_meth, props, *args, **kwargs):
    for p, d in FunctionToJson.parse_docstring(main_meth.__doc__).items():
        if "options" in d and p in props:
            props[p]["enum"] = d["options"] or []

def _param_schema(p, *args, **kwargs):
    ann = p.annotation if p.annotation is not inspect._empty else object
    return {
        "type": PY2JSON.get(ann, "object"),
        "default": None if p.default is inspect._empty else p.default,
        "required": p.default is inspect._empty,
    }

def _default_serializer(obj, *args, **kwargs):
    if isinstance(obj, (type, types.ModuleType)):
        return f"<{obj.__name__}>"
    return str(obj)

def _parse_arg_lines(args_text, *args, **kwargs):
    result, current, opts_found = {}, None, False
    for line in args_text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            current, opts_found = _handle_option(result, current, line)
        else:
            current, opts_found = _handle_arg(result, current, opts_found, line)
    return result

def _handle_option(result, current, line, *args, **kwargs):
    if current:
        result[current].setdefault('options', []).append(line[2:])
    return current, True

def _handle_arg(result, current, opts_found, line, *args, **kwargs):
    match = _ARG_RE.match(line)
    if not match:
        if current and line: result[current]['description'] += ' ' + line
        return current, opts_found
    if current and not opts_found: result[current]['options'] = None
    current = match.group(1)
    result[current] = {'type': match.group(2), 'description': match.group(3)}
    return current, False
