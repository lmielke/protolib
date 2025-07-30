# settings.py
import os, re, sys, time, yaml
from datetime import datetime as dt

package_name = "protopy"
package_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(package_dir)
project_name = os.path.basename(project_dir)

apis_dir = os.path.join(package_dir, "apis")
apis_json_dir = os.path.join(package_dir, "apis", "json_schemas")
chat_logs_dir = os.path.join(package_dir, 'gp', 'chat_logs')
resources_dir = os.path.join(package_dir, "resources")

test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")

time_stamp = lambda: re.sub(r"([: .])", r"-" , str(dt.now()))
session_time_stamp = time_stamp()

ignore_dirs = {
                ".git",
                "build",
                "gp",
                "dist",
                "models",
                "*.egg-info",
                "__pycache__",
                ".pytest_cache",    
                ".tox",
}
abrev_dirs = {
                "log",
                "logs",
                "testopia_logs",
                "chat_logs",
}
