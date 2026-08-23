"""
script_path: src/protolib/test/helpers/test_function_to_json.py
description: >-
  Runs integration tests for the function_to_json helper module, verifying schema generation
  from Python signatures and docstrings. Validates type mapping, parameter extraction, and
  JSON serialization logic. Consumes the BaseSchema and FunctionToJson classes to ensure correct
  output structures.
tags:
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
"""
import inspect, json, os, tempfile, shutil, unittest
from protolib.helpers.function_to_json import (
    BaseSchema, OpenaiSchema, ExecutionInfo, JoSchema, FunctionToJson,
)
import protolib.app.settings as sts


# --- sample functions used as test targets ---

def sample_func(name: str, count: int = 5, *args, **kwargs) -> str:
    """A sample function.

    Args:
        name (str): The user name
        count (int): How many times
            - once
            - twice
            - thrice
    """
    return name * count


def sample_no_return(x, *args, **kwargs):
    pass


def sample_with_docstring(*args, **kwargs):
    """This is the docstring."""
    return 42


class TestHandleReturnsInspect(unittest.TestCase):
    """handle_returns_inspect: map Python annotations to JSON Schema types."""

    def test_str_returns_string(self):
        result = BaseSchema.handle_returns_inspect(sample_func)
        assert result == "string"

    def test_no_annotation_returns_object(self):
        result = BaseSchema.handle_returns_inspect(sample_no_return)
        assert result == "object"

    def test_int_annotation(self):
        def int_func(*args, **kwargs) -> int:
            return 1
        result = BaseSchema.handle_returns_inspect(int_func)
        assert result == "integer"

    def test_list_annotation(self):
        def list_func(*args, **kwargs) -> list:
            return []
        result = BaseSchema.handle_returns_inspect(list_func)
        assert result == "array"

    def test_dict_annotation(self):
        def dict_func(*args, **kwargs) -> dict:
            return {}
        result = BaseSchema.handle_returns_inspect(dict_func)
        assert result == "object"

    def test_bool_annotation(self):
        def bool_func(*args, **kwargs) -> bool:
            return True
        result = BaseSchema.handle_returns_inspect(bool_func)
        assert result == "boolean"


class TestReadSignature(unittest.TestCase):
    """read_signature: extract function parameters into JSON Schema properties."""

    def test_typed_params(self):
        props = FunctionToJson.read_signature(sample_func)
        assert "name" in props
        assert props["name"]["type"] == "string"
        assert props["name"]["required"] is True

    def test_default_value(self):
        props = FunctionToJson.read_signature(sample_func)
        assert props["count"]["default"] == 5
        assert props["count"]["required"] is False

    def test_skips_self_and_varargs(self):
        props = FunctionToJson.read_signature(sample_func)
        assert "args" not in props
        assert "kwargs" not in props

    def test_untyped_param(self):
        props = FunctionToJson.read_signature(sample_no_return)
        assert props["x"]["type"] == "object"


class TestParseDocstring(unittest.TestCase):
    """parse_docstring: extract args and options from Google-style docstring."""

    def test_parses_args(self):
        result = FunctionToJson.parse_docstring(sample_func.__doc__)
        assert "name" in result
        assert result["name"]["type"] == "str"
        assert "The user name" in result["name"]["description"]

    def test_parses_options(self):
        result = FunctionToJson.parse_docstring(sample_func.__doc__)
        assert "count" in result
        assert "options" in result["count"]
        assert "once" in result["count"]["options"]
        assert len(result["count"]["options"]) == 3

    def test_no_args_returns_empty(self):
        result = FunctionToJson.parse_docstring("No args section here.")
        assert result == {}

    def test_none_docstring(self):
        result = FunctionToJson.parse_docstring(None)
        assert result == {}


class TestGetFunctionCode(unittest.TestCase):
    """get_function_code: extract source stripping docstrings."""

    def test_returns_source(self):
        code = BaseSchema.get_function_code(sample_func)
        assert "def sample_func" in code
        assert "return name * count" in code

    def test_includes_body(self):
        code = BaseSchema.get_function_code(sample_with_docstring)
        assert "return 42" in code
        assert "def sample_with_docstring" in code


class TestBaseSchemaSetFields(unittest.TestCase):
    """BaseSchema.set_fields: build schema from callables."""

    def test_fields_populated(self):
        props = FunctionToJson.read_signature(sample_func)
        schema = BaseSchema.set_fields(sample_func, props, test_meth=sample_no_return)
        assert schema.name == "sample_func"
        assert schema.returns == "string"
        assert "properties" in schema.parameters

    def test_to_dict(self):
        props = FunctionToJson.read_signature(sample_func)
        schema = BaseSchema.set_fields(sample_func, props, test_meth=sample_no_return)
        d = schema.to_dict()
        assert isinstance(d, dict)
        assert d["name"] == "sample_func"


class TestExecutionInfo(unittest.TestCase):
    """ExecutionInfo: minimal import/module path schema."""

    def test_set_fields(self):
        info = ExecutionInfo.set_fields(sample_func)
        assert "test_function_to_json" in info.import_path
        d = info.to_dict()
        assert "import_path" in d
        assert "module_path" in d


class TestJoSchema(unittest.TestCase):
    """JoSchema: api/response/path schema."""

    def test_set_fields(self):
        schema = JoSchema.set_fields(sample_func)
        assert schema.api == "sample_func"
        assert schema.response == "string"
        assert schema.path.endswith(".py")


class TestOpenaiSchemaSetFields(unittest.TestCase):
    """OpenaiSchema.set_fields: build OpenAI tool schema."""

    def test_required_collected(self):
        props = FunctionToJson.read_signature(sample_func)
        schema = OpenaiSchema.set_fields(sample_func, props)
        assert "name" in schema.parameters["required"]

    def test_required_flag_stripped_from_props(self):
        props = FunctionToJson.read_signature(sample_func)
        schema = OpenaiSchema.set_fields(sample_func, props)
        for prop_meta in schema.parameters["properties"].values():
            assert "required" not in prop_meta

    def test_to_dict_keys(self):
        props = FunctionToJson.read_signature(sample_func)
        schema = OpenaiSchema.set_fields(sample_func, props)
        d = schema.to_dict()
        assert set(d.keys()) == {"name", "description", "parameters", "returns"}


class TestDumpToJson(unittest.TestCase):
    """dump_to_json: write schema dict to JSON file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig = sts.apis_json_dir
        sts.apis_json_dir = self.tmpdir

    def tearDown(self):
        sts.apis_json_dir = self._orig
        shutil.rmtree(self.tmpdir)

    def test_writes_json_file(self):
        ftj = FunctionToJson(schemas=set())
        ftj.asts = {"base": {"name": "test"}}
        ftj.dump_to_json("my.module", "my_func", True)
        path = os.path.join(self.tmpdir, "my.module.my_func.json")
        assert os.path.exists(path)
        with open(path) as f:
            data = json.load(f)
        assert data["base"]["name"] == "test"

    def test_skip_when_write_false(self):
        ftj = FunctionToJson(schemas=set())
        ftj.asts = {"base": {"name": "test"}}
        ftj.dump_to_json("my.module", "my_func", False)
        path = os.path.join(self.tmpdir, "my.module.my_func.json")
        assert not os.path.exists(path)


class _StubTest:
    def test_stub(self):
        pass


class TestGetObjectNames(unittest.TestCase):
    """_get_object_names: extract class/method names from test method."""

    def test_valid_method(self):
        ftj = FunctionToJson(schemas=set())
        result = ftj._get_object_names(_StubTest.test_stub)
        assert result[0] == "_StubTest"
        assert result[1] == "test_stub"

    def test_invalid_qualname_raises(self):
        ftj = FunctionToJson(schemas=set())
        with self.assertRaises(ValueError):
            ftj._get_object_names(sample_func)


if __name__ == '__main__':
    unittest.main()
