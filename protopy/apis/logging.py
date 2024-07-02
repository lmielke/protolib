import os
import sys
import psutil
from pathlib import Path
from protopy.helpers.application_logger.detached_runner import run_application_info_detached, stop_application_info

PID_FILE = Path(os.path.expanduser("~/.testlogs/application_info.pid"))

def is_process_running(pid):
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False

def start(prompt_user=True, *args, **kwargs):
    if PID_FILE.exists():
        with PID_FILE.open("r") as f:
            pid = int(f.read().strip())
        if is_process_running(pid):
            print(f"Process is already running with PID {pid}.")
            return
        else:
            PID_FILE.unlink()

    if prompt_user:
        user_input = input("application_info not running, do you want to start the process? (yes/no): ").strip().lower()
        if user_input != "yes":
            print("Process not started.")
            return

    pid = run_application_info_detached()
    with PID_FILE.open("w") as f:
        f.write(str(pid))
    print(f"Started ApplicationInfo process with PID {pid}.")

def stop(*args, **kwargs):
    if not PID_FILE.exists():
        print("No running process found.")
        return

    with PID_FILE.open("r") as f:
        pid = int(f.read().strip())
    
    if is_process_running(pid):
        stop_application_info()
        print(f"Stopped ApplicationInfo process with PID {pid}.")
    else:
        print(f"No process running with PID {pid}.")
    
    if PID_FILE.exists():
        PID_FILE.unlink()
        print(f"PID file {PID_FILE} removed.")

def status(*args, **kwargs):
    if not PID_FILE.exists():
        print("No running process found.")
        return

    with PID_FILE.open("r") as f:
        pid = int(f.read().strip())
    
    if is_process_running(pid):
        print(f"ApplicationInfo is running with PID {pid}.")
    else:
        print(f"No process running with PID {pid}.")
        PID_FILE.unlink()
        print(f"PID file {PID_FILE} removed.")

def main(*args, **kwargs):
    if len(sys.argv) != 4 or sys.argv[2] != '-f':
        print("Usage: proto start_stop -f [start|stop|status]")
        return

    command = sys.argv[3].lower()
    if command == "start":
        start(prompt_user=False)
    elif command == "stop":
        stop()
    elif command == "status":
        status()
    else:
        print("Invalid command. Use 'start', 'stop', or 'status'.")

if __name__ == "__main__":
    main()
