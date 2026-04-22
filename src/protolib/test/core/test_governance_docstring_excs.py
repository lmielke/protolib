"""
script_path: src/protolib/test/core/test_governance_docstring_excs.py

IT for Phase 3 — docstring-based governance exceptions. Exercises the
helpers (_parse_docstring_front_matter, _enclosing_scopes,
_docstring_exceptions, _match_exception, _filter_docstring_excs) against
fixture files under test/data/governance_fixtures/.
"""
import ast, os, unittest
import protolib.core.settings as sts
from protolib.test.core.test_governance import (
    CHECKS, _parse_docstring_front_matter, _enclosing_scopes,
    _docstring_exceptions, _match_exception, _filter_docstring_excs,
)

FIX_DIR = os.path.join(sts.test_dir, "data", "governance_fixtures")


def _load(name, *args, **kwargs):
    with open(os.path.join(FIX_DIR, name)) as f: src = f.read()
    return src, ast.parse(src)


class TestFrontMatter(unittest.TestCase):

    def test_empty(self, *args, **kwargs):
        self.assertEqual(_parse_docstring_front_matter(""), ({}, ""))

    def test_none(self, *args, **kwargs):
        self.assertEqual(_parse_docstring_front_matter(None), ({}, ""))

    def test_yaml_head(self, *args, **kwargs):
        meta, body = _parse_docstring_front_matter('purpose: "x"\n\nbody')
        self.assertEqual(meta, {"purpose": "x"})
        self.assertEqual(body, "body")

    def test_no_yaml(self, *args, **kwargs):
        meta, body = _parse_docstring_front_matter("just prose")
        self.assertEqual(meta, {})


class TestMatch(unittest.TestCase):

    def test_module_scope_suppresses(self, *args, **kwargs):
        src, tree = _load("match.py")
        msgs = ["line 9: local import: import json"]
        kept = _filter_docstring_excs(msgs, code="c25", tree=tree, rules=CHECKS)
        self.assertEqual(kept, [])

    def test_no_match_keeps_msg(self, *args, **kwargs):
        src, tree = _load("no_match.py")
        msgs = ["line 8: local import: import json"]
        kept = _filter_docstring_excs(msgs, code="c25", tree=tree, rules=CHECKS)
        self.assertEqual(kept, msgs)

    def test_def_scope_suppresses(self, *args, **kwargs):
        src, tree = _load("def_scope_match.py")
        msgs = ["line 10: local import: import json"]
        kept = _filter_docstring_excs(msgs, code="c25", tree=tree, rules=CHECKS)
        self.assertEqual(kept, [])


class TestMalformed(unittest.TestCase):

    def test_non_list_excs_raises(self, *args, **kwargs):
        src, tree = _load("malformed.py")
        with self.assertRaises(ValueError):
            _docstring_exceptions(tree)


class TestMandatoryGuard(unittest.TestCase):

    def test_suppressing_c1_raises(self, *args, **kwargs):
        src, tree = _load("mandatory_suppress.py")
        with self.assertRaises(AssertionError):
            _filter_docstring_excs(
                ["line 5: some_func() has 9 lines (>8)"],
                code="c1", tree=tree, rules=CHECKS)


if __name__ == "__main__":
    unittest.main()
