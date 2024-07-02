"""
os_info.py
No description provided
"""
import protopy.settings as sts
import platform
import subprocess
import re
from typing import Any, Dict
from tabulate import tabulate as tb
from protopy.helpers.collections import group_text

from protopy.helpers.sys_state import state_cache

# these are Example lists for removing and keeping keys from the extracted system info
removes, replaces = ["Host", r"\[\d+\]"], [['\\', '/'], ]
# key system's identity, configuration, hardware, and operating environment parameter
keeps = [
    "Host Name",
    "OS Name",
    "OS Version",
    "OS Manufacturer",
    "System Manufacturer",
    "System Model",
    "System Type",
    "Processor(s)",
    "Total Physical Memory",
    "Available Physical Memory",
    "Hyper-V Requirements",
    "Boot Device",
    "PowerShell Version",
]

@state_cache(max_cache_hours=5)
def get_os_info(*args, **kwargs) -> Dict[str, Any]:
    """
    Extracts operating system information based on the current platform and returns it in
    a dictionary format.
    Filters out certain keys based on a provided regular expression list.
    selections can be reduced in size using the reduce parameter
    """
    sys_info = {}
    if platform.system() == "Windows":
        sys_info = _get_windows_os_info()
    elif platform.system() == "Linux":
        sys_info = _get_linux_os_info()
    elif platform.system() == "Darwin":
        sys_info = _get_mac_os_info()
    else:
        sys_info["error"] = "Unsupported OS"
    # Remove keys based on reduce
    if keeps is not None:
        sys_info = {k: v for k, v in sys_info.items() if k in keeps}
    if removes is not None:
        sys_info = {
            k: v for k, v in sys_info.items() if not any([re.search(r, k) for r in removes])
        }
    for repl in replaces:
        sys_info = {k: vs.replace(*repl) for k, vs in sys_info.items()}
    return sys_info


def _get_windows_os_info() -> Dict[str, str]:
    """Extracts OS information for Windows."""
    def get_ps_info():
        powershell_version = subprocess.check_output(
            "powershell $PSVersionTable.PSVersion", shell=True
        ).decode()
        # subprocess returns ugly unreadable string like this:
        # powershell_version = '\r\nMajor  Minor  Build  Revision\r\n-----  -----  ----- 
        # --------\r\n5      1      19041  4291    \r\n\r\n\r\n'
        # so, we need to clean it up
        cleaned = re.sub(r"\s+|-+", " ", powershell_version).strip().split(" ")
        return ' '.join([cl for cl in cleaned if cl])
    # update remaining os infos
    try:
        cmd = "systeminfo"
        output = subprocess.check_output(cmd).decode()
        infos = {
                        line.split(":")[0].strip(): line.split(":")[1].strip()
                        for line in output.split("\n")
                        if ":" in line
        }
        infos["PowerShell Version"] = get_ps_info()
        return infos

    except Exception as e:
        return {"error": str(e)}


def _get_linux_os_info() -> Dict[str, str]:
    """Extracts OS information for Linux."""
    try:
        with open("/etc/os-release") as f:
            return {
                line.split("=")[0].strip(): line.split("=")[1].strip().strip('"')
                for line in f
                if "=" in line
            }
    except Exception as e:
        return {"error": str(e)}


def _get_mac_os_info() -> Dict[str, str]:
    """Extracts OS information for macOS."""
    try:
        cmd = "sw_vers"
        output = subprocess.check_output(cmd, shell=True).decode()
        return {
            line.split(":")[0].strip(): line.split(":")[1].strip()
            for line in output.split("\n")
            if ":" in line
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    sys_info = {k: group_text(v, 50) for k, v in get_os_info(reduce="regexs").items()}
    # Example usage
    # from tabulate import tabulate as tb
    print(tb(sys_info.items(), headers="keys", tablefmt="psql", showindex=True))
