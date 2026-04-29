<!--
script_path: src/protolib/test/Readme.md
purpose: "Test-suite guide: layout, entry points, governance engine, manual EtE protocol."
update_rules: "Update when suite layout, entry points, or EtE protocol change."
-->

# protolib — Test Suite

Master test suite for protolib and the self-similar template all clones inherit.
`test/core/` is sync-owned (propagates to every clone); `test/app/` is clone-owned.

## Layout

```
src/protolib/test
├── app/       # application ITs (clone-owned)
├── core/      # framework + governance ITs (sync-owned)
│   └── gov/   # master governance engine (governance.py + helpers/cN.py + base.py + settings.yml + logs/)
├── data/      # test fixtures (governance_fixtures, test_protopy.yml, …)
├── helpers/   # package-level helper ITs
└── test_results.yaml
```

For more detail, RUN: `tree -L 2 -I '__pycache__|*.pyc' src/protolib/test`.

Key files in `core/`: `test_all.py` (per-module orchestrator → `test_results.yaml`), `test_kwargs.py`, plus the `gov/` master-engine subtree.

Master-engine gov suite lives in `core/gov/`: `governance.py` is the literate master (one `## cN` block per rule, plus a callable `run()` returning `(warnings, errors)`), `helpers/cN.py` are dumb helpers, `base.py` is the orchestrator, `settings.yml` holds thresholds, `logs/` carries runtime + audit yamls. Run with `uv run python -m protolib.test.core.gov.governance` (exits 0 clean, 1 on errors). Kitchen-sink fixture: `test/core/data/gov_violations.py`.

Legacy `test/core/test_governance*.py` and `test/core/helpers/gov/*` are tagged `[TO_DELETE]` (slated for removal — replaced by `core/gov/`).

**Sync boundary:** `test/core/` follows `core/` + `helpers/` to every clone; `test/app/` stays clone-local.

## Entry Points

| Layer | Command |
|---|---|
| Full test suite | `uv run pytest src/protolib/test/` |
| Per-module IT orchestrator | `uv run python -m protolib.test.core.test_all` |
| Governance | `uv run python -m protolib.test.core.gov.governance` |
| Auto-correct (c24/c26/c28) | `uv run python -m protolib.test.core.helpers.auto_correct` |
| Self-similar EtE | `~/scripts/testing/test_e2e_recursive.sh` |

Results:
- `test/test_results.yaml` — per-module IT orchestrator output
- `test/core/gov/logs/governance_log.yaml` — governance violations per source file
- `test/core/gov/logs/governance_exceptions_log.yaml` — active `governance_exceptions` entries
- `~/.protolib/test_results.json` — consumed by the PACKAGE terminal-header coverage field

## Philosophy

- Integration tests + End-to-End only. No unit tests, no mocking.
- Realistic inputs; expected outputs independently derivable.
- Every test validates its own prerequisites — a failed prerequisite produces a clear error, not a cryptic test failure.
- `testhelper.py` is gone; infrastructure lives in `test/core/helpers/setup.py`, re-exported via `test/core/helpers/__init__.py`. Consumers keep writing `import protolib.test.core.helpers as testhelper` and calling `@testhelper.test_setup(...)`.

## Governance Engine

Rule catalog is the literate master `test/core/gov/governance.py` itself: one `## cN`
markdown block per rule, parsed at run time by `base.py` into the runtime `CHECKS` dict.
Each block carries the rule's `scope`, `level`, exception policy, and a docstring of
the matching helper at `test/core/gov/helpers/cN.py`. Per-scope contract: declaration
scope ≡ emission scope (a `governance_exception` for `cN` lives in the docstring of
the node — module / class / def — where the violation fires).

| Category | Rules |
|---|---|
| Mandatory (no exception) | c1 (fn len ≤ 7), c11 (line len ≤ 95), c_dfmt, c_dscope, c_dorph |
| Auto-fixable | c24 (def spacing), c26 (relative imports), c28 (bare except) |
| Suppressible | all others via docstring `governance_exceptions: [- cN: "reason"]` |

Adding a new rule: create `test/core/gov/helpers/cN.py` with the check function, add a
`## cN` block in `governance.py` with the YAML front-matter (scope, level, etc.), and add
the helper to `base.py`'s dispatch table. The literate master picks it up at next run.

Programmatic entry point: `from protolib.test.core.gov.governance import run` — returns
`(warnings, errors)` lists. Used by `protopy.DefaultClass._check_governance` when
`settings.run_checks` is enabled.

## Manual End-to-End Protocol

`test_e2e_recursive.sh` is the automated acceptance test for the self-similar property.
The following manual walkthrough mirrors what it does and is useful for debugging
clone/sync regressions by hand. All commands run from `~/repos/protolib/`.

### 1. Clone protolib into a throwaway child

```bash
cd ~/repos/protolib
uv run python -m protolib.core.admin clone \
    -pr testchild -n testchild -a tch -t ~/repos \
    --port 9099 -p 3.13 --install -y
```

Expected: clone completes, gate validation passes, full test suite runs inside the new
child as part of `--install`, ending in `454 passed` (or whatever the current baseline is).

### 2. Run the test suite in the child

```bash
cd ~/repos/testchild
uv run pytest src/testchild/test/
```

Expected: same pass count as protolib — governance rules, helper ITs, and app ITs all
green against the clone's renamed paths.

### 3. Bring the child server up and down

```bash
# start (background)
cd ~/repos/testchild
uv run python -m testchild.app.tchpy server &
SERVER_PID=$!

# verify
sleep 2
curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://localhost:9099/info/?infos=package"
# → HTTP 200

# stop
kill $SERVER_PID
sleep 1
curl -s --max-time 2 -o /dev/null -w "HTTP %{http_code}\n" "http://localhost:9099/info/" \
    || echo "server down"
# → HTTP 000 + "server down"
```

Port matches `--port` passed to clone. `/info/?infos=package` returns ANSI-styled HTML
with the clone's resolved `sts.project_name`, `sts.package_dir`, `sts.test_dir` — confirming
settings-layer path resolution works unchanged in the clone.

### 4. Sync protolib → child

```bash
cd ~/repos/protolib
uv run python -m protolib.core.admin sync -v 2
```

Expected: `<child>: N file(s) synced.` followed by `<child>: recursing...`. The recurse
step runs `proto-admin sync` inside each child so grandchildren stay current.

### 5. Re-run tests post-sync

```bash
cd ~/repos/testchild
uv run pytest src/testchild/test/
```

Expected: same pass count as step 2. Any regression here is a sync-path bug (files
mis-copied, stale `__pycache__`, tree-transform missed a rename).

### 6. Tear down

```bash
rm -rf ~/repos/testchild
# clone registry is cleaned by the next `proto-admin sync`
```

### Failure-mode checklist

| Symptom | Likely cause |
|---|---|
| Governance run fails to parse rule blocks | malformed `## cN` front-matter in `gov/governance.py` or missing helper at `gov/helpers/cN.py` |
| Clone stops at gate validation | alias < 3 chars, or port collision with registered clone |
| Tests pass in protolib, fail in clone | tree-transform missed a rename — grep the failing path in clone for residual `protolib`/`proto` tokens |
| Post-sync test count drops | sync didn't copy a new file; check `-v 2` output for the missing relpath |
| Server returns `API 'X' not found` with a list | endpoint typo — pick one from the returned `Available APIs` list |

## Known Gaps

- `test_clone.py` has no real-directory clone scenario (deferred).
- No governance EtE against a known-bad source tree — coverage is IT-level via meta-rule tests (deferred).
- 7 legacy tests re-implement tempdir+chdir manually instead of `@test_setup` — tracked in
  docs ma `2026-04-18_09-15-09`; migration path is `from protolib.test.core.helpers import test_setup`.
