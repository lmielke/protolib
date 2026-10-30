"""
script_path: src/protolib/core/settings.py
description: >-
  Defines structural path constants and configuration values for the protolib core framework
  layer. Derives all directory paths from the file location using Django-style resolution
  to support package cloning without modification. Exposes API package pairs, registry endpoints,
  and user settings locations consumed by the registry and app dispatcher.
  _PyProjectReader parses pyproject.toml to extract the primary script file name.
tags:
- infra
- parsing
- settings
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


class _PyProjectReader:
    """description: 'Parses pyproject.toml to extract the primary script file name.'"""

    def __init__(self, *args, path: str, **kwargs):
        """description: 'Load and parse the scripts table from pyproject.toml at path.'"""
        scripts = tomllib.loads(open(path).read()).get("project", {}).get("scripts", {})
        self._first = next(iter(scripts.values()), "")

    def main_file(self, *args, **kwargs) -> str:
        """description: 'Return the Python file name for the first project.scripts entry.'"""
        return f"{self._first.split(':')[0].split('.')[-1]}.py" if self._first else ""

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Human-readable summary.'"""
        return f"_PyProjectReader(first={self._first!r})"

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "_PyProjectReader(*args, path=..., **kwargs)"


main_file_name = _PyProjectReader(path=os.path.join(project_dir, "pyproject.toml")).main_file()
