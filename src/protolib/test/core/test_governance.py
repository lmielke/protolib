"""
script_path: src/protolib/test/core/test_governance.py
purpose: "[TO_DELETE] Rule catalog and IT runner for all governance checks (c1–c_dorph + pkg)."
description: |-
  TestGovernance carries one 1-liner test method per rule, each with YAML
  front-matter (code/mandatory/why/fix) that catalog.py parses into CHECKS.
  setUpClass runs every check over discover_sources(); methods emit the
  per-rule results. TestSyncDrift covers the sync-drift pkg check.
update_rules: "Append rules as 1-liner methods with canonical YAML docstrings."
"""
import os, ast, unittest, yaml
from protolib.test.core.helpers.gov import CHECKS, META_CHECKS
from protolib.test.core.helpers.gov.base import SRC_ROOT, discover_sources
from protolib.test.core.helpers.gov.meta import (
    _filter_docstring_excs, _parse_legacy, _rec,
)
from protolib.test.core.helpers.gov.log import (
    GovernanceLog, EXCS_LOG_PATH, _collect_file_exceptions, _save_exceptions_log,
)
from protolib.test.core.helpers.gov.pkg import (
    check_mock_usage, check_testhelper_candidates, check_test_file_location,
    check_sync_drift, check_test_core_helper_location, check_test_imports_test_file,
    _PKG_META,
)

_AC = "Run: uv run python -m protolib.test.core.helpers.auto_correct"


class TestGovernance(unittest.TestCase):
    """
    purpose: "IT: run every CHECKS + META_CHECKS + pkg check over discover_sources()."
    description: "Scan in setUpClass; per-rule methods just report cached results."
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        log = GovernanceLog()
        all_codes = list(CHECKS) + list(META_CHECKS)
        cls.warns = {code: [] for code in all_codes}
        cls.errs = {code: [] for code in all_codes}
        cls.records = {code: [] for code in all_codes}
        cls.exceptions = []
        active = set(discover_sources())
        for rel in active:
            cls._scan_file(rel=rel, log=log)
        log.prune(active_keys=active)
        log.save()
        _save_exceptions_log(cls.exceptions, EXCS_LOG_PATH)

    @classmethod
    def _scan_file(cls, *args, rel, log, **kwargs):
        """purpose: Run all checks on one file and accumulate warns/errs/records."""
        abs_path = os.path.join(SRC_ROOT, rel)
        with open(abs_path) as f: src = f.read()
        lines = src.splitlines(keepends=True)
        tree = cls._safe_parse(src)
        all_w, all_e = cls._run_all(lines=lines, rel=rel, tree=tree)
        status = "error" if all_e else ("warn" if all_w else "pass")
        log.record(key=rel, mtime=os.path.getmtime(abs_path),
                   status=status, warnings=all_w, errors=all_e)

    @classmethod
    def _run_all(cls, *args, lines, rel, tree, **kwargs) -> tuple:
        """purpose: Dispatch CHECKS + META_CHECKS on one file; collect results."""
        all_w, all_e = [], []
        file_records = {code: [] for code in list(CHECKS) + list(META_CHECKS)}
        for code, meta in CHECKS.items():
            w, e = cls._run_check(code=code, meta=meta, lines=lines, rel=rel,
                                  tree=tree, file_records=file_records)
            all_w.extend(w); all_e.extend(e)
        for code, meta in META_CHECKS.items():
            w, e = cls._run_meta(code=code, meta=meta, rel=rel,
                                 tree=tree, file_records=file_records)
            all_w.extend(w); all_e.extend(e)
        cls.exceptions.extend(_collect_file_exceptions(tree, rel, file_records))
        return all_w, all_e

    @classmethod
    def _safe_parse(cls, src, *args, **kwargs):
        """purpose: ast.parse with None fallback on SyntaxError."""
        try: return ast.parse(src)
        except SyntaxError: return None

    @classmethod
    def _run_check(cls, *args, code, meta, lines, rel, tree=None,
                   file_records=None, **kwargs):
        """purpose: Run one per-file check; filter suppressions; record + render."""
        w, e = meta['fn'](lines, rel)
        cls._record(code=code, scope=meta['scope'], warns=w, errs=e,
                    file_records=file_records)
        if tree is not None:
            w = _filter_docstring_excs(w, code=code, tree=tree, rules=CHECKS)
            e = _filter_docstring_excs(e, code=code, tree=tree, rules=CHECKS)
        cls._render(code=code, rel=rel, warns=w, errs=e)
        return w, e

    @classmethod
    def _run_meta(cls, *args, code, meta, rel, tree, file_records, **kwargs):
        """purpose: Run one meta-rule check; dispatch by 'tree' vs 'records' kind."""
        if meta['kind'] == 'tree':
            w, e = meta['fn'](tree, rel, rules=CHECKS)
        else:
            w, e = meta['fn'](tree, file_records, rules=CHECKS)
        cls._record(code=code, scope='module', warns=w, errs=e, file_records=file_records)
        cls._render(code=code, rel=rel, warns=w, errs=e)
        return w, e

    @classmethod
    def _record(cls, *args, code, scope, warns, errs, file_records=None, **kwargs):
        """purpose: Append records for every warn/err, optionally to file_records."""
        for m in warns: cls._record_one(code, scope, m, 'warn', file_records)
        for m in errs: cls._record_one(code, scope, m, 'error', file_records)

    @classmethod
    def _record_one(cls, code, scope, msg, level, file_records, *args, **kwargs):
        """purpose: Parse one msg into a record; store globally and file-locally."""
        line, tech = _parse_legacy(msg)
        rec = _rec(line=line, scope=scope, technical=tech, level=level)
        cls.records[code].append(rec)
        if file_records is not None: file_records[code].append(rec)

    @classmethod
    def _render(cls, *args, code, rel, warns, errs, **kwargs):
        """purpose: Format and append printable warn/err lines with file prefix."""
        cls.warns[code].extend(f"  [{rel}] {m}" for m in warns)
        cls.errs[code].extend(f"  [{rel}] {m}" for m in errs)

    def _msg(self, all_v, *args, why='', fix='', auto=False, **kwargs):
        """purpose: Join violations + why/fix/auto footer into one message."""
        parts = ["\n".join(all_v)]
        if why: parts.append(f"  why: {why}")
        if fix: parts.append(f"  fix: {fix}")
        if auto: parts.append(f"  auto: {_AC}")
        return "\n".join(parts)

    def _report(self, warns, errs, *args, **kwargs):
        """purpose: Fail on errors, print on warns, noop when both empty."""
        all_v = warns + errs
        if not all_v: return
        msg = self._msg(all_v, **kwargs)
        if errs: self.fail(msg)
        else: print(f"\n{'─' * 60}\n{msg}")

    def _check(self, *args, code, **kwargs):
        """purpose: Report cached warns/errs for one rule with its why/fix footer."""
        m = CHECKS[code]
        self._report(self.warns[code], self.errs[code],
                     why=m['why'], fix=m['fix'], auto=m.get('auto', False))

    def _check_meta(self, *args, code, **kwargs):
        """purpose: Report cached warns/errs for one meta-rule with its why/fix footer."""
        m = META_CHECKS[code]
        self._report(self.warns[code], self.errs[code], why=m['why'], fix=m['fix'])

    # ── per-file checks ────────────────────────────────────────────

    def test_c1_function_length(self, *args, **kwargs):
        """
        code: c1
        mandatory: true
        why: "Long functions often mix concerns — harder to test and reason about in isolation."
        fix: "Split into smaller focused methods, or extract a helper."
        """
        self._check(code='c1')

    def test_c2_one_line_functions(self, *args, **kwargs):
        """
        code: c2
        mandatory: false
        why: "A one-liner wrapper adds a call frame without any abstraction value."
        fix: "Inline the expression at the call site and remove the wrapper."
        """
        self._check(code='c2')

    def test_c3_module_length(self, *args, **kwargs):
        """
        code: c3
        mandatory: false
        why: "Long modules tend to accumulate unrelated concerns."
        fix: "Split into focused sub-modules; move helpers to the appropriate layer."
        """
        self._check(code='c3')

    def test_c4_kwargs_access(self, *args, **kwargs):
        """
        code: c4
        mandatory: false
        why: "kwargs.get() bypasses named param forwarding — callers cannot rely on it passing through."
        fix: "Declare the parameter explicitly in the function signature."
        """
        self._check(code='c4')

    def test_c5_kwargs_signature(self, *args, **kwargs):
        """
        code: c5
        mandatory: false
        why: "Missing *args/**kwargs breaks hook-compatible forwarding across the call stack."
        fix: "Add *args, **kwargs to the function signature."
        """
        self._check(code='c5')

    def test_c6_statement_semicolon(self, *args, **kwargs):
        """
        code: c6
        mandatory: false
        why: "';' joins statements on one line — hides control flow and blocks per-line diffs."
        fix: "Split joined statements onto separate lines, or extract a helper method."
        """
        self._check(code='c6')

    def test_c7_eval_exec(self, *args, **kwargs):
        """
        code: c7
        mandatory: false
        why: "eval/exec execute arbitrary strings — a security risk and debuggability hazard."
        fix: "Use explicit data structures, importlib, or a dispatch dict instead."
        """
        self._check(code='c7')

    def test_c8_class_presence(self, *args, **kwargs):
        """
        code: c8
        mandatory: false
        why: "OOP is the primary paradigm — function-only modules often signal a missing abstraction."
        fix: "Wrap related functions in a class, or confirm the module is intentionally stateless."
        """
        self._check(code='c8')

    def test_c10_flat_imports(self, *args, **kwargs):
        """
        code: c10
        mandatory: false
        why: "Imports outside app/core/helpers create hidden coupling and break clone portability."
        fix: "Use only app/, core/, or helpers/ sub-packages."
        """
        self._check(code='c10')

    def test_c11_line_length(self, *args, **kwargs):
        """
        code: c11
        mandatory: true
        why: "Long lines reduce readability in split-screen editors and diff views."
        fix: "Wrap at a natural expression boundary, or extract a local variable."
        """
        self._check(code='c11')

    def test_c12_class_count(self, *args, **kwargs):
        """
        code: c12
        mandatory: false
        why: "Multiple classes in one module suggest it has more than one responsibility."
        fix: "Split into focused modules — one primary class per file."
        """
        self._check(code='c12')

    def test_c13_class_before_function(self, *args, **kwargs):
        """
        code: c13
        mandatory: false
        why: "Consistent ordering (classes first) makes navigation predictable."
        fix: "Move all module-level functions below the class definitions."
        """
        self._check(code='c13')

    def test_c14_elif_chains(self, *args, **kwargs):
        """
        code: c14
        mandatory: false
        why: "Long elif chains are hard to extend, test exhaustively, and read at a glance."
        fix: "Replace with a lookup dict or a dispatch table keyed on the condition value."
        """
        self._check(code='c14')

    def test_c15_deep_nesting(self, *args, **kwargs):
        """
        code: c15
        mandatory: false
        why: "Deep nesting increases cognitive load and makes logic harder to test."
        fix: "Extract inner blocks to helper methods, or invert conditions to reduce nesting."
        """
        self._check(code='c15')

    def test_c16_pass_only(self, *args, **kwargs):
        """
        code: c16
        mandatory: false
        why: "A pass-only function signals incomplete work or dead code."
        fix: "Implement the function body, or delete it if no longer needed."
        """
        self._check(code='c16')

    def test_c17_docstring(self, *args, **kwargs):
        """
        code: c17
        mandatory: false
        why: "Module docstrings with script_path enable traceability and tool support."
        fix: "Add a triple-quote docstring with script_path and a description."
        """
        self._check(code='c17')

    def test_c18_test_pairing(self, *args, **kwargs):
        """
        code: c18
        mandatory: false
        why: "Unpaired modules have no automated contract verification."
        fix: "Create the missing test file with at least one integration test scenario."
        """
        self._check(code='c18')

    def test_c19_mutable_defaults(self, *args, **kwargs):
        """
        code: c19
        mandatory: false
        why: "Mutable defaults persist across calls — mutations accumulate unexpectedly."
        fix: "Use None as default and assign the mutable value inside the function body."
        """
        self._check(code='c19')

    def test_c20_name_guard(self, *args, **kwargs):
        """
        code: c20
        mandatory: false
        why: "Without a __main__ guard the module body runs on import, not only when executed directly."
        fix: "Add 'if __name__ == __main__: main()' at the bottom of the file."
        """
        self._check(code='c20')

    def test_c21_repeated_locals(self, *args, **kwargs):
        """
        code: c21
        mandatory: false
        why: "Repeated locals across many functions suggest state that belongs on a class."
        fix: "Pass the value explicitly as a named parameter, or promote to a class attribute."
        """
        self._check(code='c21')

    def test_c24_def_spacing(self, *args, **kwargs):
        """
        code: c24
        mandatory: false
        why: "Inconsistent blank-line spacing makes file structure harder to scan visually."
        fix: "Use exactly 1 blank line before defs, 2 before classes."
        """
        self._check(code='c24')

    def test_c25_local_imports(self, *args, **kwargs):
        """
        code: c25
        mandatory: false
        why: "Local imports hide dependencies, delay import errors, and usually signal a circular-import workaround."
        fix: "Move the import to the module-level block. If circular, refactor the coupling."
        """
        self._check(code='c25')

    def test_c26_relative_imports(self, *args, **kwargs):
        """
        code: c26
        mandatory: false
        why: "Relative imports break grepability and make module moves fragile."
        fix: "Replace with absolute imports: 'from protolib.module import x'."
        """
        self._check(code='c26')

    def test_c27_wildcard_imports(self, *args, **kwargs):
        """
        code: c27
        mandatory: false
        why: "Wildcard imports hide dependencies and pollute the module namespace."
        fix: "Import only the names you use: 'from module import Foo, bar'."
        """
        self._check(code='c27')

    def test_c28_bare_except(self, *args, **kwargs):
        """
        code: c28
        mandatory: false
        why: "Bare except masks KeyboardInterrupt and SystemExit — real errors get swallowed."
        fix: "Catch the specific exception type(s) you expect: 'except ValueError:'."
        """
        self._check(code='c28')

    def test_c29_hardcoded_paths(self, *args, **kwargs):
        """
        code: c29
        mandatory: false
        why: "Hardcoded paths break portability across machines and environments."
        fix: "Use settings (sts.*), os.path, or pathlib.Path with relative anchors."
        """
        self._check(code='c29')

    def test_c30_raw_print(self, *args, **kwargs):
        """
        code: c30
        mandatory: false
        why: "Raw print() is unstructured and cannot be routed, filtered, or silenced."
        fix: "Use logprint() from helpers/printing, or move output to an API module."
        """
        self._check(code='c30')

    def test_c32_stdlib_logging(self, *args, **kwargs):
        """
        code: c32
        mandatory: false
        why: "stdlib logging adds unnecessary configuration and duplicates logprint()."
        fix: "Import and use logprint from helpers/printing instead."
        """
        self._check(code='c32')

    def test_c34_strip_ansi_redef(self, *args, **kwargs):
        """
        code: c34
        mandatory: false
        why: "Redefining strip_ansi_codes creates silent drift from the canonical version."
        fix: "Import strip_ansi_codes from helpers/printing instead of redefining it."
        """
        self._check(code='c34')

    def test_c35_core_imports_app(self, *args, **kwargs):
        """
        code: c35
        mandatory: false
        why: "core/ importing app/ creates circular dependency risk and breaks clones."
        fix: "Move shared logic to core/ or helpers/, then import from there."
        """
        self._check(code='c35')

    def test_c36_inline_dict_size(self, *args, **kwargs):
        """
        code: c36
        mandatory: false
        why: "Large inline dicts are hard to update without redeployment and obscure config intent."
        fix: "Move to settings.py or a yaml/json resource file and load at startup."
        """
        self._check(code='c36')

    def test_c40_helpers_purity(self, *args, **kwargs):
        """
        code: c40
        mandatory: false
        why: "helpers/ modules must be portable to clones — core/app imports break that."
        fix: "Remove the import; helpers/ may only depend on stdlib, app.settings, and other helpers/."
        """
        self._check(code='c40')

    def test_c41_filename_collision(self, *args, **kwargs):
        """
        code: c41
        mandatory: false
        why: "Two source modules with the same basename make imports ambiguous and grep noisy."
        fix: "Rename one module, or declare a c41 governance_exception if the duplication is by design."
        """
        self._check(code='c41')

    # ── meta-rules ─────────────────────────────────────────────────

    def test_c_dfmt_docstring_format(self, *args, **kwargs):
        """purpose: Report c_dfmt (docstring format) violations from the cached scan."""
        self._check_meta(code='c_dfmt')

    def test_c_dscope_exception_scope(self, *args, **kwargs):
        """purpose: Report c_dscope (exception scope mismatch) violations from the cached scan."""
        self._check_meta(code='c_dscope')

    def test_c_dorph_orphan_exception(self, *args, **kwargs):
        """purpose: Report c_dorph (orphan exception) violations from the cached scan."""
        self._check_meta(code='c_dorph')

    # ── package-level checks ───────────────────────────────────────

    def test_pkg_mock_usage(self, *args, **kwargs):
        """purpose: Mock-usage across test/ tree (not per-file)."""
        w, e = check_mock_usage()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["mock usage"])))

    def test_pkg_testhelper_candidates(self, *args, **kwargs):
        """purpose: setUp manually reimplements what @test_setup provides."""
        w, e = check_testhelper_candidates()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["testhelper candidates"])))

    def test_pkg_test_file_location(self, *args, **kwargs):
        """purpose: test_*.py / testhelper.py outside test/ dir."""
        w, e = check_test_file_location()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["test file location"])))

    def test_pkg_sync_drift(self, *args, **kwargs):
        """purpose: Framework files newer than last_synced indicate manual drift."""
        w, e = check_sync_drift()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["sync drift"])))

    def test_pkg_test_core_helper_location(self, *args, **kwargs):
        """purpose: Non-test files in test/core/ outside helpers/ shadow real modules."""
        w, e = check_test_core_helper_location()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["test core helper location"])))

    def test_pkg_test_imports_test_file(self, *args, **kwargs):
        """purpose: test_*.py importing another test_*.py creates hidden coupling."""
        w, e = check_test_imports_test_file()
        self._report(w, e, **dict(zip(('why', 'fix'), _PKG_META["test imports test file"])))

    # ── zero-warning invariant (runs last) ─────────────────────────

    def test_zz_zero_warnings(self, *args, **kwargs):
        """purpose: Aggregate guard — any warning from c1–c_dorph fails the suite."""
        lines = [f"[{code}] {m}" for code, ws in self.warns.items() for m in ws]
        if lines:
            self.fail(f"{len(lines)} governance warning(s):\n" + "\n".join(lines))


class TestSyncDrift(unittest.TestCase):
    """
    purpose: "IT for pkg.check_sync_drift — mtime > last_synced triggers drift."
    description: "Builds temp pkg tree, writes sync_log with controlled timestamp."
    """

    def setUp(self, *args, **kwargs):
        import tempfile, shutil
        self._shutil = shutil
        self.root = tempfile.mkdtemp()
        self.pkg_dir = os.path.join(self.root, "pkg")
        os.makedirs(os.path.join(self.pkg_dir, "core"))
        os.makedirs(os.path.join(self.pkg_dir, "helpers"))
        self.file = os.path.join(self.pkg_dir, "core", "settings.py")
        with open(self.file, "w") as f: f.write("x=1\n")
        self.sync_log = os.path.join(self.root, "sync_log.yaml")

    def tearDown(self, *args, **kwargs):
        self._shutil.rmtree(self.root)

    def _write_log(self, *args, ts: str, **kwargs):
        """purpose: Write a sync_log.yaml with last_synced=ts."""
        with open(self.sync_log, "w") as f:
            f.write(yaml.dump({"last_synced": ts, "synced_by": "protolib", "files": []}))

    def test_no_sync_log_skipped(self, *args, **kwargs):
        os.remove(self.sync_log) if os.path.exists(self.sync_log) else None
        warn, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertEqual((warn, err), ([], []))

    def test_no_drift_when_files_older_than_last_synced(self, *args, **kwargs):
        self._write_log(ts="2099-01-01T00:00:00")
        _, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertEqual(err, [])

    def test_drift_detected_when_file_newer(self, *args, **kwargs):
        self._write_log(ts="1990-01-01T00:00:00")
        _, err = check_sync_drift(project_dir=self.pkg_dir, sync_log=self.sync_log)
        self.assertTrue(any("core/settings.py" in line for line in err))


if __name__ == "__main__":
    unittest.main()
