"""
script_path: src/protolib/core/settings.py
description: >-
  Defines structural path constants and configuration values for the protolib core framework
  layer. Derives all directory paths from the file location using Django-style resolution
  to support package cloning without modification. Exposes API package pairs, registry endpoints,
  and user settings locations consumed by the registry and app dispatcher.
tags:
- infra
- parsing
- settings
governance_exceptions:
- c8: no class definition — verify OOP intent
"""
import os, tomllib

core_dir = os.path.dirname(__file__)              # .../src/<pkg>/core/
package_dir = os.path.dirname(core_dir)           # .../src/<pkg>/
src_dir = os.path.dirname(package_dir)              # .../src/
project_dir = os.path.dirname(src_dir)              # .../repos/<pkg>/

package_name = os.path.basename(package_dir)        # "protolib" — django style
project_name = os.path.basename(project_dir)

apis_dir = os.path.join(package_dir, "app", "apis")
apis_json_dir = os.path.join(apis_dir, "json_schemas")

# (dir, import-prefix) pairs — consumed by registry and app dispatcher.
api_packages = [
    (os.path.join(package_dir, "core", "apis"), f"{package_name}.core.apis"),
    (os.path.join(package_dir, "app", "apis"), f"{package_name}.app.apis"),
]
test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")

ignore_dirs = {
    ".git", ".venv", ".uv", "build", "gp", "dist", "models",
    "*.egg-info", "__pycache__", ".pytest_cache", ".tox", "*helpers",
    "blueprint",
}
abrev_dirs = {"log", "logs", "testopia_logs", "chat_logs"}
# fresh blueprint tree scaffolded into every clone (never copied from the source) so new
# packages start on the bpm lane — routing contract: ~/.claude/rules/bp_routing.md
blueprint_scaffold_dirs = [os.path.join("blueprint", "experiments", "prototype")]

table_max_chars = 200
resources_dir = os.path.expanduser(f"~{os.sep}.{package_name}")
error_path = os.path.join(resources_dir, "error.log")

eext = ".yml"
fext = ".json"

port = 9001
user_settings_name = "settings.yml"
user_settings_path = os.path.join(resources_dir, user_settings_name)

registry_port = int(os.environ.get("REGISTRY_PORT", 9000))
registry_url = f"http://127.0.0.1:{registry_port}"
registry_state_file = os.path.join(resources_dir, "registry_state.json")
registry_host_enabled = False
registry_heartbeat_interval = 60

# main_file_name — first entry of pyproject [project.scripts], file part only.
# Module scope (no def): c37 walks FunctionDefs only.
_scripts = tomllib.loads(open(os.path.join(project_dir, "pyproject.toml")).read()
                         ).get("project", {}).get("scripts", {})
_first = next(iter(_scripts.values()), "")
main_file_name = f"{_first.split(':')[0].split('.')[-1]}.py" if _first else ""
