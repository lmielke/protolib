<!--
source_path: /home/lars/repos/protolib/CLAUDE.md
edit: true
purpose: "Claude Code context for the protolib package."
update_rules: "Update when repo structure, commands, or entry points change."
-->

If you have not yet read `~/.claude/CLAUDE.md`, do so before continuing.
If you have not yet read `~/repos/protolib/Readme.md`, do so before continuing.

## Key Documents
- `~/repos/protolib/Readme.md` — architecture and usage
- `~/repos/protolib/MAINTENANCE.md` — open issues
- `~/repos/protolib/PROJECT.md` — design decisions
- `~/repos/protolib/CHANGELOG.md` — change history
- `~/repos/protolib/INBOX.md` — drop box (process with /inbox)

# protolib — Package Context

Template package for all protolib-based clones. All other packages (`bridge`, `speaker`, `whisker`, etc.) are cloned from this one.

## Key Commands
- `proto info` — package info
- `proto info -i package python -v 1` — detailed info
- `proto server` — start HTTP server (default port 9001)
- `proto clone -i <name>` — clone template into a new package (always ask user approval before running)

## Project Structure
- `src/protolib/apis/` — API entry points, each exposes `main(*args, **kwargs)`
- `src/protolib/helpers/` — utility modules
- `src/protolib/creator/` — clone logic
- `src/protolib/protopy.py` — core logic (DefaultClass)
- `src/protolib/registry.py` — registry connector
- `src/protolib/settings.py` — configuration
- `src/protolib/contracts.py` — validation stubs (overridden in clones)
- `src/protolib/resources/` — files copied to new packages on clone

## Clone Notes
- Shared modules must not hardcode package-specific dependencies.
- `resources/CLAUDE.md` is the minimal skeleton shipped to clones — keep it generic.
- `ignore_dirs` in `settings.py` controls what clone skips. `.claude` must NOT be listed.
- Text replacement in clone handles renaming (`protolib` → new name) across all copied files.

## Conventions
- Package manager: `uv` — use `uv sync`, `uv run`, `uv add` etc. Do not use pip directly.
