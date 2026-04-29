"""
script_path: src/protolib/test/helpers/test_docstrings.py
purpose: "Integration tests for helpers/docstrings.py — Docstring and Docstrings."
update_rules: "Append scenarios. Never remove existing tests."
"""
import ast, unittest
from protolib.helpers.docstrings import Docstring, Docstrings


VALID = (
    'script_path: src/foo.py\n'
    'purpose: "demo"\n'
    '\n'
    'Free-form body text here.'
)

MALFORMED = 'key: [unclosed\n\nbody'


class TestDocstring(unittest.TestCase):
    """Docstring(raw) → .meta, .body, .get()."""

    def test_valid_meta_parsed(self):
        self.assertEqual(Docstring(VALID).meta['script_path'], 'src/foo.py')

    def test_valid_purpose(self):
        self.assertEqual(Docstring(VALID).meta['purpose'], 'demo')

    def test_valid_body(self):
        self.assertEqual(Docstring(VALID).body.strip(), 'Free-form body text here.')

    def test_empty_meta_is_none(self):
        self.assertIsNone(Docstring('').meta)

    def test_empty_body_is_empty_string(self):
        self.assertEqual(Docstring('').body, '')

    def test_none_meta_is_none(self):
        self.assertIsNone(Docstring(None).meta)

    def test_malformed_meta_is_none(self):
        self.assertIsNone(Docstring(MALFORMED).meta)

    def test_malformed_body_is_empty(self):
        self.assertEqual(Docstring(MALFORMED).body, '')

    def test_get_returns_value(self):
        self.assertEqual(Docstring(VALID).get(key='purpose'), 'demo')

    def test_get_returns_default(self):
        self.assertEqual(Docstring(VALID).get(key='missing', default='fb'), 'fb')

    def test_get_default_none_when_meta_none(self):
        self.assertIsNone(Docstring('').get(key='purpose'))

    def test_head_only_no_body(self):
        d = Docstring('purpose: "x"')
        self.assertEqual(d.meta['purpose'], 'x')
        self.assertEqual(d.body, '')


CLS_SRC = '''
class Sample:
    def alpha(self, *args, **kwargs):
        """purpose: A method"""
        pass

    def beta(self, *args, **kwargs):
        """purpose: B method"""
        pass
'''


class TestDocstringsFactories(unittest.TestCase):
    """Docstrings.from_node / Docstrings.from_class."""

    def test_from_node_returns_docstring(self):
        tree = ast.parse(CLS_SRC)
        func = tree.body[0].body[0]
        self.assertEqual(Docstrings.from_node(func).meta['purpose'], 'A method')


    def test_from_class_keys_are_method_names(self):
        tree = ast.parse(CLS_SRC)
        result = Docstrings.from_class(tree, class_name='Sample')
        self.assertEqual(set(result.keys()), {'alpha', 'beta'})

    def test_from_class_method_meta_parsed(self):
        tree = ast.parse(CLS_SRC)
        result = Docstrings.from_class(tree, class_name='Sample')
        self.assertEqual(result['beta'].meta['purpose'], 'B method')

    def test_from_class_unknown_returns_empty(self):
        tree = ast.parse(CLS_SRC)
        self.assertEqual(Docstrings.from_class(tree, class_name='Nope'), {})

    def test_from_node_on_classdef(self):
        tree = ast.parse('class C:\n    """purpose: top"""\n    pass\n')
        d = Docstrings.from_node(tree.body[0])
        self.assertEqual(d.meta['purpose'], 'top')


if __name__ == '__main__':
    unittest.main()
