<!--
source_path: /home/lars/repos/protolib/Readme.md
edit: true
purpose: "User-facing documentation. Explains installation, usage, and commands."
update_rules: "Update when user-facing behaviour, commands, or parameters change."
format: "prose + code blocks"
-->

# Protolib — Python Package Template

Creates a ready-to-use Python package from a template with a single command.
After `proto clone`, you can start coding immediately in the new package.

## Install

```sh
git clone git@gitlab.com:larsmielke2/protopy.git ./protolib
cd protolib
uv python install 3.13
uv sync
```

Add an activate shortcut (optional):
```sh
echo '\nalias activate="source .venv/bin/activate"' >> ~/.zshrc && source ~/.zshrc
```

## Clone a New Package

```sh
activate
proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/tmp' --port 9005 -p 3.13 --install
```

| Flag | Required | Description |
|------|----------|-------------|
| `-pr` | yes | Project folder name |
| `-n` | yes | Package name (must differ from project name) |
| `-a` | yes | Package alias (CLI command name) |
| `-t` | yes | Target directory |
| `--port` | yes | HTTP port for server.py |
| `-p` | no | Python version for environment |
| `--install` | no | Run `uv sync` after cloning |
| `-y` | no | Skip confirmation prompts |

After cloning, read the target project's `Readme.md` — it has been replaced with new instructions for your package.

## Daily Use

```sh
activate
proto info                                        # show package info
proto info -i package python -v 1                 # detailed info
proto server                                      # start HTTP server (default port from settings)
proto server --port 9005                          # start on specific port
curl http://localhost:9005/info/?infos=package     # test the server
```

## Registry APIs

Every protolib-based package includes built-in service discovery. These work both as CLI commands and HTTP endpoints:

```sh
proto register                               # register with registry (one-shot)
proto expose_api                             # show this service's API signatures
proto discover --service_id ollama           # look up a service by ID

# HTTP equivalents (server must be running)
curl http://localhost:9006/register/
curl http://localhost:9006/expose_api/
curl http://localhost:9006/discover/?service_id=ollama
```

Registry integration is optional — if the registry is down, the package operates normally. See `BLUEPRINT_REGISTRY.md` for the full design.

---

## System Service (optional)

A `protolib.service` file is included in the project root.

User service (starts on login):
```sh
systemctl --user enable --now ~/repos/protolib/protolib.service
```

System service (starts on boot):
```sh
sudo cp ~/repos/protolib/protolib.service /etc/systemd/system/
sudo systemctl enable --now protolib
```

Managing the service:
```sh
systemctl --user status protolib
systemctl --user restart protolib
journalctl --user -u protolib -f
```
