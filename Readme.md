<!--
source_path: /home/lars/repos/protolib/Readme.md
edit: true
purpose: "User-facing documentation. Explains installation, usage, and commands."
update_rules: "Update when user-facing behaviour, commands, or parameters change."
format: "prose + code blocks"
-->

# Protolib — Self-Similar Python Package Template

Protolib is both a working package and the template for all derived packages.
Every clone inherits the full `core/` + `helpers/` framework and can produce
more clones itself. Framework updates propagate via `proto-admin sync`.

## Install

```sh
git clone git@gitlab.com:larsmielke2/protopy.git ./protolib
cd protolib
uv python install 3.13
uv sync
```

## Layout

```
src/protolib/
├── app/            # application layer (clone owners edit here)
├── core/           # framework: registry, APIs, admin, creator
├── helpers/        # pure utilities (no app/core dependencies)
├── test/           # integration tests + master governance engine (test/core/gov/)
```

Tests: see [`src/protolib/test/Readme.md`](src/protolib/test/Readme.md).

## Core vs App

`core/` and `helpers/` form the shared framework that every clone inherits.
`app/` is the clone-owned layer where features and APIs live. `proto-admin sync`
pushes `core/` and `helpers/` from protolib to every registered clone, so edits
in those layers propagate system-wide. Because of this, **`core/` and `helpers/`
are not to be edited outside protolib** — changes there must be made here and
synced out. Clone owners edit only `app/`; protolib owns the framework.

## Two Entry Points

| Command | Dispatches to | Purpose |
|---|---|---|
| `proto` | `app.protopy:main` | application APIs (info, server, register, ...) |
| `proto-admin` | `core.admin:main` | framework ops (clone, sync) |

## Clone a New Package

```sh
proto-admin clone -pr my_superlib -n my_superpackage -a supi -t /tmp --port 9005 -p 3.13 --install
```

| Flag | Required | Description |
|------|----------|-------------|
| `-pr` | yes | Project folder name |
| `-n` | yes | Package name (inside `src/`) |
| `-a` | yes | Package alias (CLI command for the clone) |
| `-t` | yes | Target directory |
| `--port` | yes | HTTP port for the server |
| `-p` | no | Python version for the clone's venv |
| `--install` | no | Run `uv sync` after cloning |
| `-y` | no | Skip confirmation prompts |

Aliases should be ≥ 3 characters to avoid collateral text substitutions.

## Daily Use

```sh
proto info                                         # show package info
proto server                                       # start HTTP server
curl http://localhost:9001/info/?infos=package     # test the server
proto register                                     # register with registry
proto discover --service_id ollama                 # look up a service
```

## Framework Sync

Clones stay in sync with protolib's framework layer:

```sh


proto-admin sync                                   # push core/+helpers/ to all registered clones

```

Sync touches only `core/` and `helpers/`. `app/` is never modified.

## System Service (optional)

```sh
systemctl --user enable --now ~/repos/protolib/protolib.service
journalctl --user -u protolib -f
```
