import os
import sys
import time
import subprocess
import psutil
import ctypes

import protopy.helpers.collections as hlp
import protopy.settings as sts
from protopy.helpers.application_logger.application_info import ApplicationInfo

PID_FILE = os.path.expanduser("~/.testlogs/application_info.pid")

def set_process_name(pid, new_name: str):
    """
    Set the process name on Windows using ctypes.
    """
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(new_name)
        print(f"{sts.YELLOW}Process {pid} Name:{sts.RESET} {new_name}")
    except Exception as e:
        print(f"Error renaming process: {e}")

def run_application_info_detached():
    """
    Run the ApplicationInfo module as a detached subprocess and rename it.
    """
    print("Starting ApplicationInfo process in detached mode...")
    python_executable = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    script_path = os.path.abspath(__file__)
    application_info_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'application_info.py'))
    print(f"Python executable: {python_executable}")
    print(f"ApplicationInfo script path: {application_info_path}")

    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NO_WINDOW = 0x08000000

    process = subprocess.Popen([python_executable, "-m", "protopy.helpers.application_logger.application_info"],
                               creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL,
                               close_fds=True)

    time.sleep(0.5)

    # Set the process name
    set_process_name(process.pid, "ApplicationInfoLogger")

    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    print(f"PID file created at {PID_FILE} with PID {process.pid}")

    return process.pid

def stop_application_info():
    """
    Stop the ApplicationInfo module subprocess.
    """
    if not os.path.exists(PID_FILE):
        print("No running process found.")
        return

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    print(f"Stopping process with PID: {pid}")
    try:
        process = psutil.Process(pid)
        process.terminate()
        process.wait(timeout=5)
        print(f"Process {pid} terminated successfully.")
    except psutil.NoSuchProcess:
        print(f"No process with PID {pid} found.")
    except psutil.TimeoutExpired:
        print(f"Process {pid} did not terminate in time.")
    except Exception as e:
        print(f"Error terminating process: {e}")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            print(f"PID file {PID_FILE} removed.")

def is_application_info_running():
    """
    Check if the ApplicationInfo process is running.
    """
    if not os.path.exists(PID_FILE):
        print("No running process found.")
        return False

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        process = psutil.Process(pid)
        if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
            print(f"ApplicationInfo is running with PID {pid}.")
            return True
        else:
            print("No running process found.")
            return False
    except psutil.NoSuchProcess:
        print("No running process found.")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detached_runner.py [start|stop|info]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "start":
        run_application_info_detached()
    elif command == "stop":
        stop_application_info()
    elif command == "info":
        is_application_info_running()
    else:
        print("Invalid command. Use 'start', 'stop', or 'info'.")
