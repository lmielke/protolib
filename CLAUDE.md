<!--
script_path: /home/lars/repos/protolib/CLAUDE.md
edit: true
purpose: "Claude Code context for the protolib package."
update_rules: "Update when repo structure, commands, or entry points change."
-->

If you have not yet read `~/.claude/CLAUDE.md`, do so before continuing.
If you have not yet read `~/repos/protolib/Readme.md`, do so before continuing.

## Key Documents
- `~/repos/protolib/Readme.md` — architecture and usage
- `~/repos/protolib/MAINTENANCE.yaml` — open issues
- `~/repos/protolib/PROJECT.yaml` — design decisions
- `~/repos/protolib/CHANGELOG.yaml` — change history
- `~/repos/protolib/INBOX.md` — drop box (process with /inbox)

Run `docs -h` for the full docs command reference. Use `docs -n protolib` to target this workspace.


# protolib — Package Context

Template package for all protolib-based clones. All other packages (`bridge`, `speaker`, `whisker`, etc.) are cloned from this one.

## Key Commands
- `proto info` — package info
- `proto info -i package python -v 1` — detailed info
- `proto server` — start HTTP server (default port 9001)
- `proto-admin clone -pr <pr> -n <pkg> -a <alias> -t <dir> --port <n>` — clone template
- `proto-admin sync` — push core/+helpers/ to all registered clones (recursive)

## Project Structure
- `src/protolib/app/` — application layer (apis, arguments, contracts, protopy, settings)
- `src/protolib/core/` — framework layer (admin, arguments, registry, settings, VERSION, apis/, creator/)
- `src/protolib/helpers/` — pure utilities (no app/core dependencies)
- `src/protolib/test/` — integration tests
- `src/protolib/app/resources/` — CLAUDE.md + .clone/ skeleton (inherited by clones via copytree)

## Entry Points
- `proto` → `app.protopy:main` (application APIs)
- `proto-admin` → `core.admin:main` (framework ops: clone, sync)

## Clone Notes
- Self-similar: clones receive the full source unmodified — no resource copying, no marker stripping.
- `ignore_dirs` in `core/settings.py` controls what `shutil.copytree` skips during clone. `.claude` must NOT be listed.
- Aliases should be ≥ 3 characters to avoid collateral text substitutions.
- `app/` is user-owned in clones; `core/` + `helpers/` stay in sync with protolib via `proto-admin sync`.

## Conventions
- Package manager: `uv` — use `uv sync`, `uv run`, `uv add` etc. Do not use pip directly.
