"""
script_path: src/protolib/test/core/helpers/gov/pkg.py
purpose: "[TO_DELETE] Package-level governance checks — invariants across the whole test/ tree."
description: |-
  mock usage, testhelper candidates, test file location, sync drift, plus two
  new test-layout errors: core-helper location, test-file importing test-file.
update_rules: "Do not modify in clones."
"""
import os, re
import yaml
from datetime import datetime as dt
import protolib.core.settings as sts
from protolib.test.core.helpers.gov.base import SRC_ROOT

PKG = sts.package_name

_MOCK_PAT = re.compile(r'from unittest\.mock import|from unittest import mock|import mock\b')
_C38_SETUP_BLOCK = re.compile(
    r'def setUp\s*\([^)]*\)[^:]*:.*?(?=\n {0,4}def |\Z)', re.DOTALL)
_TEST_IMPORT_PAT = re.compile(
    rf'(?:from|import)\s+{re.escape(PKG)}(?:\.[\w.]*)?\.test_[\w]+')


def _iter_test_files(*args, **kwargs):
    """purpose: Yield (abs_path, rel_path) for every test_*.py under test/."""
    for root, _, files in os.walk(sts.test_dir):
        for f in sorted(files):
            if not f.startswith("test_") or not f.endswith(".py"): continue
            path = os.path.join(root, f)
            yield path, os.path.relpath(path, SRC_ROOT)


def _setup_reimplements(*args, block: str, **kwargs) -> bool:
    """purpose: True if a setUp block manually recreates tmpdir+chdir+makedirs."""
    return (bool(re.search(r'tempfile\.(mkdtemp|TemporaryDirectory)', block))
            and "os.chdir" in block and "os.makedirs" in block)


def check_mock_usage(*args, **kwargs) -> tuple:
    """purpose: Flag unittest.mock imports in test files."""
    warn = []
    for path, rel in _iter_test_files():
        with open(path) as fh:
            if _MOCK_PAT.search(fh.read()):
                warn.append(f"[{rel}] uses mock — prefer real IT or testhelper.test_setup")
    return warn, []


def check_testhelper_candidates(*args, **kwargs) -> tuple:
    """purpose: Flag test setUp blocks that manually reimplement @test_setup."""
    warn = []
    for path, rel in _iter_test_files():
        with open(path) as fh: text = fh.read()
        if "@testhelper.test_setup" in text or "@test_setup" in text: continue
        if any(_setup_reimplements(block=b) for b in _C38_SETUP_BLOCK.findall(text)):
            warn.append(
                f"[{rel}] setUp uses tempfile + os.chdir + os.makedirs"
                f" — use @test_setup from test/core/helpers/setup.py")
    return warn, []


def check_test_file_location(*args, **kwargs) -> tuple:
    """purpose: Flag test_*.py / testhelper.py files outside any test/ directory."""
    err = []
    for root, dirs, files in os.walk(SRC_ROOT):
        dirs[:] = [d for d in dirs if d not in {"__pycache__"}]
        for f in files:
            if not (f.startswith("test_") or f == "testhelper.py"): continue
            rel = os.path.relpath(os.path.join(root, f), SRC_ROOT).replace(os.sep, "/")
            if "test/" not in rel: err.append(f"[{rel}] test file outside test/ dir")
    return [], err


def check_sync_drift(*args, project_dir=None, sync_log=None, **kwargs) -> tuple:
    """purpose: Flag framework files with mtime > last_synced. Skip if sync_log absent."""
    pdir = project_dir or sts.package_dir
    slog = sync_log or os.path.join(os.path.expanduser("~"), f".{PKG}", "sync_log.yaml")
    if not os.path.exists(slog): return [], []
    with open(slog) as f: data = yaml.safe_load(f) or {}
    cutoff = dt.fromisoformat(data["last_synced"]).timestamp()
    err = [f"[{rel}] drift: modified after last_synced" for rel in _framework_files(pdir)
           if os.path.getmtime(os.path.join(pdir, rel)) > cutoff]
    return [], err


def _framework_files(pdir, *args, **kwargs):
    """purpose: Yield rel paths under framework scopes (core, helpers, test/core)."""
    for scope in ("core", "helpers", "test/core"):
        sdir = os.path.join(pdir, scope)
        if not os.path.isdir(sdir): continue
        for root, dirs, files in os.walk(sdir):
            dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
            for f in files:
                yield os.path.relpath(os.path.join(root, f), pdir).replace(os.sep, "/")


def check_test_core_helper_location(*args, **kwargs) -> tuple:
    """purpose: Flag non-test files in test/core/ that live outside helpers/."""
    err = []
    core_dir = os.path.join(sts.test_dir, "core")
    if not os.path.isdir(core_dir): return [], err
    for f in sorted(os.listdir(core_dir)):
        full = os.path.join(core_dir, f)
        if not os.path.isfile(full): continue
        if f.startswith("test_") or f == "__init__.py": continue
        rel = os.path.relpath(full, SRC_ROOT).replace(os.sep, "/")
        err.append(f"[{rel}] helper file in test/core/ — move under test/core/helpers/")
    return [], err


def check_test_imports_test_file(*args, **kwargs) -> tuple:
    """purpose: Flag test_*.py modules that import from another test_*.py."""
    err = []
    for path, rel in _iter_test_files():
        with open(path) as fh: text = fh.read()
        if _TEST_IMPORT_PAT.search(text):
            err.append(
                f"[{rel}] imports from another test_*.py — "
                f"extract shared code to test/core/helpers/")
    return [], err


_PKG_CHECKS = [
    ("mock usage",                check_mock_usage),
    ("testhelper candidates",     check_testhelper_candidates),
    ("test file location",        check_test_file_location),
    ("sync drift",                check_sync_drift),
    ("test core helper location", check_test_core_helper_location),
    ("test imports test file",    check_test_imports_test_file),
]


_PKG_META = {
    "mock usage": (
        "Mocking hides real behavior — prefer real integration tests or test_setup.",
        "Remove mock imports; use realistic inputs and @test_setup for temp dirs.",
    ),
    "testhelper candidates": (
        "setUp manually re-implements tmpdir+chdir setup that @test_setup provides.",
        "Replace setUp with @test_setup from test/core/helpers/setup.py.",
    ),
    "test file location": (
        "test_*.py outside test/ is not collected by the runner and can shadow real modules.",
        "Move the file under src/<pkg>/test/ mirroring the module it tests.",
    ),
    "sync drift": (
        "Framework files modified after last_synced indicate manual drift from upstream.",
        "Run 'proto-admin sync' from upstream, or propagate the change upstream first.",
    ),
    "test core helper location": (
        "Non-test files in test/core/ bypass the helpers/ boundary and shadow real modules.",
        "Move the file under test/core/helpers/ and update imports.",
    ),
    "test imports test file": (
        "test_*.py importing another test_*.py creates hidden coupling across tests.",
        "Extract shared code into test/core/helpers/ and import from there.",
    ),
}
