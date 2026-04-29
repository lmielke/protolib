"""
script_path: src/protolib/test/core/test_governance_meta_rules.py
purpose: "[TO_DELETE] IT for c_dfmt, c_dscope, c_dorph meta-rules against synthetic fixtures."
"""
import ast, os, unittest
from protolib.test.core.helpers.gov import CHECKS
from protolib.test.core.helpers.gov.meta import (
    _c_dfmt_check, _c_dscope_check, _c_dorph_check, _parse_legacy,
    _docstring_nodes, _docstring_excs_safe, _rec,
)

FIX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "governance_fixtures")


def _parse(name, *args, **kwargs):
    path = os.path.join(FIX_DIR, name)
    with open(path) as f: src = f.read()
    return ast.parse(src), path


def _simulate_records(tree, *args, **kwargs) -> dict:
    """Emulate a prior pass: return fake records for c25 at module scope."""
    records = {code: [] for code in CHECKS}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt in ast.walk(n):
                if isinstance(stmt, ast.Import):
                    for alias in stmt.names:
                        tech = f"local import: import {alias.name}"
                        records['c25'].append(_rec(line=stmt.lineno, scope='module',
                                                   technical=tech, level='warn'))
    return records


class TestMetaRules(unittest.TestCase):

    def test_well_formed_has_no_violations(self, *args, **kwargs):
        tree, _ = _parse("well_formed_module.py")
        _, e = _c_dfmt_check(tree, "test/data/governance_fixtures/well_formed_module.py", rules=CHECKS)
        self.assertEqual(e, [])

    def test_malformed_yaml_flagged(self, *args, **kwargs):
        tree, _ = _parse("malformed_yaml.py")
        _, e = _c_dfmt_check(tree, "fixtures/malformed_yaml.py", rules=CHECKS)
        self.assertTrue(any("no front-matter mapping" in m for m in e), e)

    def test_unknown_key_flagged(self, *args, **kwargs):
        tree, _ = _parse("unknown_key.py")
        _, e = _c_dfmt_check(tree, "fixtures/unknown_key.py", rules=CHECKS)
        self.assertTrue(any("unexpected key 'totally_bogus_key'" in m for m in e), e)

    def test_mandatory_suppress_flagged_by_dfmt(self, *args, **kwargs):
        tree, _ = _parse("mandatory_suppress.py")
        _, e = _c_dfmt_check(tree, "fixtures/mandatory_suppress.py", rules=CHECKS)
        self.assertTrue(any("cannot suppress mandatory rule c1" in m for m in e), e)

    def test_short_prose_has_no_front_matter(self, *args, **kwargs):
        tree, _ = _parse("short_prose_docstring.py")
        _, e = _c_dfmt_check(tree, "fixtures/short_prose_docstring.py", rules=CHECKS)
        self.assertTrue(any("no front-matter mapping" in m for m in e), e)

    def test_wrong_scope_exception_flagged(self, *args, **kwargs):
        tree, _ = _parse("wrong_scope_exception.py")
        records = _simulate_records(tree)
        _, e = _c_dscope_check(tree, records, rules=CHECKS)
        self.assertTrue(any("c25:" in m and "not def" in m for m in e), e)

    def test_orphan_exception_flagged(self, *args, **kwargs):
        tree, _ = _parse("orphan_exception.py")
        records = {code: [] for code in CHECKS}  # no records → orphan
        _, e = _c_dorph_check(tree, records, rules=CHECKS)
        self.assertTrue(any("orphan c25" in m for m in e), e)

    def test_match_not_orphan(self, *args, **kwargs):
        tree, _ = _parse("match.py")
        records = _simulate_records(tree)
        _, e = _c_dorph_check(tree, records, rules=CHECKS)
        self.assertEqual(e, [])


if __name__ == "__main__":
    unittest.main()
