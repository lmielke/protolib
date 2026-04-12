# settings.py
import os, re, socket, sys, time, yaml
from datetime import datetime as dt

package_name = "protolib"
package_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(package_dir)
project_dir = os.path.dirname(src_dir)
project_name = os.path.basename(project_dir)

apis_dir = os.path.join(package_dir, "apis")
apis_json_dir = os.path.join(package_dir, "apis", "json_schemas")

test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")

time_stamp = lambda: re.sub(r"([: .])", r"-" , str(dt.now()))
session_time_stamp = time_stamp()

ignore_dirs = {
    ".git",
    ".venv",
    ".uv",
    "build",
    "gp",
    "dist",
    "models",
    "*.egg-info",
    "__pycache__",
    ".pytest_cache",
    ".tox",
    "*helpers",
}
abrev_dirs = {
    "log",
    "logs",
    "testopia_logs",
    "chat_logs",
}

# for some purposes file content has to be displayed to the user
# some technical files should be excluded here
ignore_files = {
    5: {
        'CHANGELOG.md',
        'LICENSE',
        'MANIFEST.in',
        'testhelper.py',
        '__init__.py',
        'server.py',
        'info.py',
    },
    6: {
        '.gitignore',
        'uv.lock',
    },
    7: {
        '.sublime-',
    },
    99: {
        'Readme.md',
        '.png',
        '.jpg',
        '.jpeg',
        '.gif',
        '.bmp',
        '.tiff',
    },
}

resources_dir = os.path.expanduser(f'~{os.sep}.{package_name}')
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)

user_settings_name = "settings.yml"
user_settings_path = os.path.join(resources_dir, user_settings_name)
if not os.path.exists(user_settings_path):
    with open(user_settings_path, 'w') as f:
        yaml.dump({
            'package_name': package_name,
            'port': 9001,
            'registry_host_enabled': False,
            'registry_heartbeat_interval': 60,
        }, f)

# Load user settings from resources YAML file
def load_user_settings():
    """Load user settings from the YAML file."""
    if not os.path.exists(user_settings_path):
        return {}

    with open(user_settings_path, 'r') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error loading user settings: {e}")
            return {}

# Registry defaults
def _resolve_host() -> str:
    """Return this machine's hostname. In Docker, returns the container name for DNS resolution."""
    return socket.gethostname()

registry_port = int(os.environ.get("REGISTRY_PORT", 9000))
service_host = os.environ.get("SERVICE_HOST", "127.0.0.1")
registry_url = f"http://127.0.0.1:{registry_port}"
registry_host_enabled = False
registry_state_file = os.path.join(resources_dir, "registry_state.json")
registry_heartbeat_interval = 60

# we add user settings to the global namespace
user_settings = load_user_settings()
# Update the global namespace with user settings
globals().update(user_settings)

table_max_chars = 200
error_path = os.path.join(resources_dir, "error.log")
