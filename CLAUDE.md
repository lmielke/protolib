---
script_path: /home/lars/repos/protolib/CLAUDE.md
edit: true
purpose: "App-tier Claude Code context for the protolib package."
update_rules: "Clone-editable. Sync never overwrites this file."
---

# protolib — Agent Notes

Template package for all protolib-based clones (`bridge`, `speaker`, `whisker`, …).

Global host context: `~/.claude/CLAUDE.md`.
Package rules auto-load from `.claude/rules/` (Python-scoped).
Architecture, layout, entry points, and commands: [`Readme.md`](Readme.md).

Run `docs -h` for the docs command reference (`docs -n protolib` to target this workspace).

## Clone Subtleties
- Self-similar: clones receive the full source unmodified — no resource copying, no marker stripping.
- `ignore_dirs` in `core/settings.py` controls what `shutil.copytree` skips during clone. `.claude` must NOT be listed.
- Aliases should be ≥ 3 characters to avoid collateral text substitutions.
- `app/` is user-owned in clones; `core/` + `helpers/` stay in sync with protolib via `proto-admin sync`.
