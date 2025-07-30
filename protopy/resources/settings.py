# settings.py
import os, re, sys, time, yaml
from datetime import datetime as dt

package_name = "protopy"
package_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(package_dir)
project_name = os.path.basename(project_dir)
test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")
apis_dir = os.path.join(package_dir, "apis")

time_stamp = lambda: re.sub(r"([: .])", r"-" , str(dt.now()))
session_time_stamp = time_stamp()
