"""
script_path: src/protolib/test/helpers/test_docstrings.py
description: >-
  Runs integration tests for the Docstring and Docstrings helper classes. Validates metadata
  parsing, body extraction, and AST-based factory methods. Ensures malformed inputs return
  safe defaults. Consumed by the protolib test suite to verify docstring handling logic.
tags:
- parsing
- testing
update_rules: Append scenarios. Never remove existing tests.
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

# Block scalar with an internal blank line (the defect case)
BLOCK_SCALAR = (
    'script_path: src/foo.py\n'
    'description: |\n'
    '  First paragraph of the description.\n'
    '\n'
    '  Second paragraph — still part of description.\n'
    '\n'
    'Body text that must NOT be absorbed into meta.'
)

# Body that looks like YAML key: value — must not be absorbed into meta
PROSE_BODY = (
    'script_path: src/foo.py\n'
    'purpose: "demo"\n'
    '\n'
    'key: value prose line\n'
    'another: line'
)


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

    def test_block_scalar_internal_blank_retained_in_meta(self):
        """purpose: 'Block scalar with internal blank line: description fully parsed into meta.'"""
        d = Docstring(BLOCK_SCALAR)
        self.assertIsNotNone(d.meta)
        desc = d.meta.get('description', '')
        self.assertIn('First paragraph', desc)
        self.assertIn('Second paragraph', desc)

    def test_block_scalar_body_not_absorbed(self):
        """purpose: 'Body text after a block-scalar head must appear in body, not meta.'"""
        d = Docstring(BLOCK_SCALAR)
        self.assertIn('Body text', d.body)

    def test_prose_body_not_absorbed_as_meta(self):
        """purpose: 'key: value prose lines in the body must not be parsed as meta fields.'"""
        d = Docstring(PROSE_BODY)
        self.assertIsNotNone(d.meta)
        self.assertNotIn('key', d.meta)
        self.assertIn('key: value prose line', d.body)


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
