---
script_path: src/protolib/test/Readme.md
description: >-
  Documents the protolib test suite layout, entry points, and governance integration. Defines
  the sync boundary between core and app tests, and details the manual end-to-end protocol
  for validating clone self-similarity. Serves as the operational guide for running integration
  tests and debugging sync regressions.
tags:
- docs
- governance
- testing
update_rules: Update when suite layout, entry points, or EtE protocol change.
---

# protolib — Test Suite

Master test suite for protolib and the self-similar template all clones inherit.
`test/core/` is sync-owned (propagates to every clone); `test/app/` is clone-owned.

## Layout

```
src/protolib/test
├── app/       # application ITs (clone-owned)
├── core/      # framework ITs (sync-owned)
├── data/      # test fixtures (test_protopy.yml, …)
├── helpers/   # package-level helper ITs
└── test_results.yaml
```

For more detail, RUN: `tree -L 2 -I '__pycache__|*.pyc' src/protolib/test`.

Key files in `core/`: `test_all.py` (per-module orchestrator → `test_results.yaml`), `test_kwargs.py`.

Governance scanning is owned by the standalone `governance` package
(`~/repos/governance`) — run via `gov run --target ~/repos/protolib`.
Kitchen-sink fixture: `test/core/data/gov_violations.py`.

**Sync boundary:** `test/core/` follows `core/` + `helpers/` to every clone; `test/app/` stays clone-local.

## Entry Points

| Layer | Command |
|---|---|
| Full test suite | `uv run pytest src/protolib/test/` |
| Per-module IT orchestrator | `uv run python -m protolib.test.core.test_all` |
| Governance scan | `cd ~/repos/governance && uv run gov run --target ~/repos/protolib` |
| Self-similar EtE | `~/scripts/testing/test_e2e_recursive.sh` |

Results:
- `test/test_results.yaml` — per-module IT orchestrator output
- `~/.governance/logs/protolib_gov_log.yaml` — governance violations per source file
- `~/.protolib/test_results.json` — consumed by the PACKAGE terminal-header coverage field

## Philosophy

- Integration tests + End-to-End only. No unit tests, no mocking.
- Realistic inputs; expected outputs independently derivable.
- Every test validates its own prerequisites — a failed prerequisite produces a clear error, not a cryptic test failure.
- `testhelper.py` is gone; infrastructure lives in `test/core/helpers/setup.py`, re-exported via `test/core/helpers/__init__.py`. Consumers keep writing `import protolib.test.core.helpers as testhelper` and calling `@testhelper.test_setup(...)`.

## Governance

Governance scanning is owned by the standalone `governance` package
(`~/repos/governance`). Run against this repo with:

```bash
cd ~/repos/governance && uv run gov run --target ~/repos/protolib
```

See the governance package's `Readme.md` for rule catalog, severity policy,
and exception conventions.

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
