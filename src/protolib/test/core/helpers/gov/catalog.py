"""
script_path: src/protolib/test/core/helpers/gov/catalog.py
purpose: "[TO_DELETE] Build the CHECKS dict from TestGovernance docstring catalog."
description: |-
  Parses test_governance.py::TestGovernance via Docstrings.from_class (helpers/docstrings),
  combines per-rule metadata (code/mandatory/why/fix) with fn references (gov/cN.py) and
  scope/auto constants. Bootstrap is fail-loud: a malformed or missing catalog raises a
  RuntimeError at import so the suite stops before scanning.
update_rules: "Do not modify in clones."
"""
import os, ast
import protolib.core.settings as sts
from protolib.helpers.docstrings import Docstrings

from protolib.test.core.helpers.gov.c1 import _c1_function_length
from protolib.test.core.helpers.gov.c2 import _c2_one_line_functions
from protolib.test.core.helpers.gov.c3 import _c3_module_length
from protolib.test.core.helpers.gov.c4 import _c4_kwargs_access
from protolib.test.core.helpers.gov.c5 import _c5_kwargs_signature
from protolib.test.core.helpers.gov.c6 import _c6_statement_semicolon
from protolib.test.core.helpers.gov.c7 import _c7_eval_exec
from protolib.test.core.helpers.gov.c8 import _c8_class_presence
from protolib.test.core.helpers.gov.c10 import _c10_flat_imports
from protolib.test.core.helpers.gov.c11 import _c11_line_length
from protolib.test.core.helpers.gov.c12 import _c12_class_count
from protolib.test.core.helpers.gov.c13 import _c13_class_before_function
from protolib.test.core.helpers.gov.c14 import _c14_elif_chains
from protolib.test.core.helpers.gov.c15 import _c15_deep_nesting
from protolib.test.core.helpers.gov.c16 import _c16_pass_only
from protolib.test.core.helpers.gov.c17 import _c17_docstring
from protolib.test.core.helpers.gov.c18 import _c18_test_pairing
from protolib.test.core.helpers.gov.c19 import _c19_mutable_defaults
from protolib.test.core.helpers.gov.c20 import _c20_name_guard
from protolib.test.core.helpers.gov.c21 import _c21_repeated_locals
from protolib.test.core.helpers.gov.c24 import _c24_def_spacing
from protolib.test.core.helpers.gov.c25 import _c25_local_imports
from protolib.test.core.helpers.gov.c26 import _c26_relative_imports
from protolib.test.core.helpers.gov.c27 import _c27_wildcard_imports
from protolib.test.core.helpers.gov.c28 import _c28_bare_except
from protolib.test.core.helpers.gov.c29 import _c29_hardcoded_paths
from protolib.test.core.helpers.gov.c30 import _c30_raw_print
from protolib.test.core.helpers.gov.c32 import _c32_stdlib_logging
from protolib.test.core.helpers.gov.c34 import _c34_strip_ansi_redef
from protolib.test.core.helpers.gov.c35 import _c35_core_imports_app
from protolib.test.core.helpers.gov.c36 import _c36_inline_dict_size
from protolib.test.core.helpers.gov.c40 import _c40_helpers_purity
from protolib.test.core.helpers.gov.c41 import _c41_filename_collision

_CATALOG_PATH = os.path.join(sts.test_dir, "core", "test_governance.py")
_CLASS_NAME = "TestGovernance"
_METHOD_PREFIX = "test_c"


_FN_MAP = {
    'c1':  _c1_function_length,       'c2':  _c2_one_line_functions,
    'c3':  _c3_module_length,         'c4':  _c4_kwargs_access,
    'c5':  _c5_kwargs_signature,      'c6':  _c6_statement_semicolon,
    'c7':  _c7_eval_exec,             'c8':  _c8_class_presence,
    'c10': _c10_flat_imports,         'c11': _c11_line_length,
    'c12': _c12_class_count,          'c13': _c13_class_before_function,
    'c14': _c14_elif_chains,          'c15': _c15_deep_nesting,
    'c16': _c16_pass_only,            'c17': _c17_docstring,
    'c18': _c18_test_pairing,         'c19': _c19_mutable_defaults,
    'c20': _c20_name_guard,           'c21': _c21_repeated_locals,
    'c24': _c24_def_spacing,          'c25': _c25_local_imports,
    'c26': _c26_relative_imports,     'c27': _c27_wildcard_imports,
    'c28': _c28_bare_except,          'c29': _c29_hardcoded_paths,
    'c30': _c30_raw_print,            'c32': _c32_stdlib_logging,
    'c34': _c34_strip_ansi_redef,    'c35': _c35_core_imports_app,
    'c36': _c36_inline_dict_size,     'c40': _c40_helpers_purity,
    'c41': _c41_filename_collision,
}

_SCOPES = {
    'c1':  'def',    'c2':  'def',    'c3':  'module', 'c4':  'def',
    'c5':  'def',    'c6':  'line',   'c7':  'line',   'c8':  'module',
    'c10': 'module', 'c11': 'line',   'c12': 'module', 'c13': 'module',
    'c14': 'line',   'c15': 'line',   'c16': 'def',    'c17': 'module',
    'c18': 'module', 'c19': 'def',    'c20': 'module', 'c21': 'def',
    'c24': 'line',   'c25': 'module', 'c26': 'module', 'c27': 'module',
    'c28': 'line',   'c29': 'line',   'c30': 'line',   'c32': 'line',
    'c34': 'line',   'c35': 'module', 'c36': 'line',   'c40': 'module',
    'c41': 'module',
}

_AUTO = {'c24', 'c26', 'c28'}


def _parse_catalog(*args, path=None, **kwargs) -> dict:
    """purpose: Map rule code to Docstring for each test_c method in TestGovernance."""
    path = path or _CATALOG_PATH
    with open(path) as f: tree = ast.parse(f.read())
    methods = Docstrings.from_class(tree, class_name=_CLASS_NAME)
    return {ds.get(key='code'): ds
            for name, ds in methods.items()
            if name.startswith(_METHOD_PREFIX) and ds.get(key='code')}


def _rule_entry(*args, code, ds, **kwargs) -> dict:
    """purpose: Assemble one CHECKS entry from catalog docstring + fn/scope tables."""
    entry = {'fn': _FN_MAP[code], 'scope': _SCOPES[code],
             'exceptions_apply': not ds.get(key='mandatory', default=False),
             'why': ds.get(key='why', default=""),
             'fix': ds.get(key='fix', default="")}
    if code in _AUTO: entry['auto'] = True
    return entry


def build_checks(*args, path=None, **kwargs) -> dict:
    """purpose: Build CHECKS from catalog; raise bootstrap RuntimeError on any error."""
    try:
        catalog = _parse_catalog(path=path)
        missing = set(_FN_MAP) - set(catalog)
        if missing: raise KeyError(f"catalog missing codes: {sorted(missing)}")
        return {code: _rule_entry(code=code, ds=catalog[code]) for code in _FN_MAP}
    except Exception as e:
        raise RuntimeError(f"governance catalog bootstrap failed: {e}") from e
