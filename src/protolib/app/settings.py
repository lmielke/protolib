"""
script_path: src/protolib/app/settings.py
description: >-
  Derives filesystem paths from the module location to remain valid after cloning. Loads user
  overrides from a YAML file in the home directory and merges them into the module namespace
  at import time. Provides configuration constants for ports, registry endpoints, and directory
  exclusions consumed by the Cloner and introspection tools.
tags:
- infra
- parsing
- settings
governance_exceptions:
- c41: duplicate basename at app/settings.py, core/settings.py
"""
import os, re, yaml
from datetime import datetime as dt

root_dir = os.path.dirname(__file__)
package_dir = os.path.dirname(root_dir)
package_name = os.path.basename(package_dir)
src_dir = os.path.dirname(package_dir)
project_dir = os.path.dirname(src_dir)
project_name = os.path.basename(project_dir)

# Identity — used by Cloner and introspection. Override via ~/.<package>/settings.yml.
alias = "proto"
port = 9001

apis_dir = os.path.join(root_dir, "apis")
apis_json_dir = os.path.join(root_dir, "apis", "json_schemas")

test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")

time_stamp = lambda: re.sub(r"([: .])", r"-", str(dt.now()))
session_time_stamp = time_stamp()

ignore_dirs = {
    ".git", ".venv", ".uv", "build", "gp", "dist", "models",
    "*.egg-info", "__pycache__", ".pytest_cache", ".tox", "*helpers",
}
abrev_dirs = {"log", "logs", "testopia_logs", "chat_logs"}

ignore_files = {
    5: {'CHANGELOG.md', 'LICENSE', 'MANIFEST.in', 'testhelper.py',
        '__init__.py', 'server.py', 'info.py'},
    6: {'.gitignore', 'uv.lock'},
    7: {'.sublime-'},
    99: {'Readme.md', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'},
}

resources_dir = os.path.expanduser(f'~{os.sep}.{package_name}')
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)

user_settings_name = "settings.yml"
user_settings_path = os.path.join(resources_dir, user_settings_name)

_DEFAULT_SETTINGS = {
    'package_name': package_name, 'port': 9001,
    'registry_host_enabled': False,
    'registry_heartbeat_interval': 60,
}


registry_port = int(os.environ.get("REGISTRY_PORT", 9000))
service_host = os.environ.get("SERVICE_HOST", "127.0.0.1")
registry_url = f"http://127.0.0.1:{registry_port}"
registry_host_enabled = False
registry_state_file = os.path.join(resources_dir, "registry_state.json")
registry_heartbeat_interval = 60

table_max_chars = 200
error_path = os.path.join(resources_dir, "error.log")

def _ensure_user_settings(*args, **kwargs):
    if os.path.exists(user_settings_path):
        return
    with open(user_settings_path, 'w') as f:
        yaml.dump(_DEFAULT_SETTINGS, f)

def load_user_settings(*args, **kwargs) -> dict:
    """
    description: Load user settings from the YAML file.
    """
    with open(user_settings_path, 'r') as f:
        return yaml.safe_load(f) or {}

_ensure_user_settings()
user_settings = load_user_settings()
globals().update(user_settings)
