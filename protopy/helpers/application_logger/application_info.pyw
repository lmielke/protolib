"""
application_info.pyw
This module contains the ApplicationInfo class and related functions.
It is responsible for logging application activity and performance.
The module uses various libraries to track keyboard and mouse events.
"""
import os
import string
import logging
import pygetwindow as gw
import psutil, time, win32gui, win32process
from datetime import datetime
from pynput.keyboard import Key, Listener as KeyboardListener, KeyCode
from pynput.mouse import Listener as MouseListener
from protopy.helpers.application_logger.proto_logger import BufferedLogger
from threading import Timer
from functools import lru_cache
from typing import Dict, Tuple
from collections import OrderedDict
import protopy.settings as sts


class ApplicationInfo:
    log_dir = os.path.expanduser("~/.testlogs/windows")

    def __init__(self, pause_threshold: int = 2):
        """
        Initialize the ApplicationInfo class.

        Args:
            pause_threshold (int): Time in seconds to detect typing pause.
        """
        self.running = True
        self.key_sequence = []
        self.not_tracked = {"sublime_text.exe"}
        self.pause_timer = None
        self.PAUSE_THRESHOLD = pause_threshold
        self.mouse_event_buffer = {}
        self.mouse_down = False
        self.elevator_keys = set()
        self.modifier_detected = None
        self.elevators = set()
        self.modifier_keys = {'ctrl_l', 'ctrl_r', 'alt_l', 'alt_r'}
        self.active_window, self.previous_window, self.switched_window = None, None, False
        self.keyboard_listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener = MouseListener(on_click=self.on_click)
        self.logger = BufferedLogger(ApplicationInfo.log_dir)

    def log(self, *args, **kwargs):
        """
        Log a message using the buffered logger.
        """
        self.logger.log(*args, **kwargs)

    def log_initial_info(self):
        self.log(f"\n### User Application/Activity log from {datetime.now()} ###\n")
        self.log_open_windows()
        self.logger.flush()

    def run(self):
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.log_initial_info()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt as e:
            self.log(f"Error: {e}")
        finally:
            self.keyboard_listener.stop()
            self.mouse_listener.stop()
            if self.pause_timer:
                self.pause_timer.cancel()
            self.logger.stop()
            self.log("Application stopped.")

    def monitor_performance(self):
        """
        Log the current CPU and memory usage of the script.
        """
        process = psutil.Process(os.getpid())
        cpu_usage = process.cpu_percent(interval=1)
        memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        self.log(f"Performance: CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage} MB")
        self.schedule_performance_monitoring()

    def schedule_performance_monitoring(self):
        """
        Schedule the next performance monitoring.
        """
        self.performance_timer = Timer(self.performance_interval, self.monitor_performance)
        self.performance_timer.start()

    def stop_performance_monitoring(self):
        """
        Stop the performance monitoring timer if it is running.
        """
        if self.performance_timer:
            self.performance_timer.cancel()
            self.performance_timer = None

    def setup_logging(self, log_dir: str):
        """
        Set up logging configuration without a timestamp.

        Args:
            log_dir (str): Directory where log files will be stored.
        """
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        current_time = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"os_activity_{current_time}.log")
        # Create a custom logger
        logger = logging.getLogger('ApplicationInfoLogger')
        logger.setLevel(logging.DEBUG)
        # Create handlers
        f_handler = logging.FileHandler(log_file)
        f_handler.setLevel(logging.DEBUG)
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.DEBUG)
        # Create formatters and add them to handlers
        f_format = logging.Formatter('%(message)s')
        c_format = logging.Formatter('%(message)s')
        f_handler.setFormatter(f_format)
        c_handler.setFormatter(c_format)
        # Add handlers to the logger
        logger.addHandler(f_handler)
        logger.addHandler(c_handler)
        return logger

    @staticmethod
    def load_log_file(date: str = None, *args, **kwargs) -> Tuple[str, Dict[str, str]]:
        """
        Load the log file content and split it into a dictionary based on flush headers.
        Args:
            date (str): The date of the log file to load. Defaults to None.
        Returns:
            Tuple[str, Dict[str, str]]: The name of the log file and a dictionary with flush timestamps as keys and log entries as values.
        """
        content = [l for l in os.listdir(ApplicationInfo.log_dir) 
                                                            if l.endswith('.log')
                                                            and l.startswith('os_activity')]
        log_file_name = None
        if date is None:
            # Find latest log file
            log_file_name = sorted(content, reverse=True)[0]
        elif date == 'today':
            log_file_name = f"os_activity_{datetime.now().strftime('%Y-%m-%d')}.log"
        else:
            # Find log file for the given date
            log_file_name = f"os_activity_{date}.log"
        
        log_file_path = os.path.join(ApplicationInfo.log_dir, log_file_name)
        # in any case the choosen log file would not exist, we take the latest log file
        if not os.path.exists(log_file_path):
            log_file_name = sorted(content, reverse=True)[0]
            log_file_path = os.path.join(ApplicationInfo.log_dir, log_file_name)
        
        with open(log_file_path, 'r') as f:
            content = f.read()
        
        log_dict = {}
        current_key = 'start'
        log_dict[current_key] = ''
        
        for line in content.split('\n'):
            if line.startswith('flush at'):
                current_key = line.split(' at ')[1].strip()
                log_dict[current_key] = ''
            else:
                log_dict[current_key] += line + '\n'
        log_dict = OrderedDict(sorted(log_dict.items(), reverse=True))
        cleaned_log_dict = ApplicationInfo.clean_logs(log_dict)
        return log_file_name, cleaned_log_dict

    @staticmethod
    def clean_logs(log_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Clean the log entries by summarizing consecutive similar events involving button clicks.

        Args:
            log_dict (Dict[str, str]): Dictionary with log timestamps as keys and log entries as values.

        Returns:
            Dict[str, str]: The cleaned dictionary with summarized log entries.
        """
        cleaned_log_dict = OrderedDict()
        sequence_triggers = ["Button.left clicked", "Button.right clicked"]
        check_len = len(max(sequence_triggers, key=len))

        for timestamp, log in log_dict.items():
            lines = log.split('\n')
            cleaned_lines = []
            in_sequence = False
            count = 1

            for line in lines:
                if any(trigger in line[:check_len] for trigger in sequence_triggers):
                    if in_sequence:
                        count += 1
                    else:
                        first_line = line
                        in_sequence = True
                        count = 1
                else:
                    if in_sequence:
                        cleaned_lines.append(f"{first_line} ({count} times)")
                        in_sequence = False
                    cleaned_lines.append(line)
            if in_sequence:
                cleaned_lines.append(f"{first_line} ({count} times)")
            cleaned_log_dict[timestamp] = '\n'.join(cleaned_lines)
        return cleaned_log_dict

    # Function to log open windows and their applications
    def log_open_windows(self, *args, **kwargs):
        self.log(f"\n### Windows and Applications ###")
        for i, window in enumerate([window for window in gw.getAllTitles() if window]):
            if window:
                try:
                    hwnd = win32gui.FindWindow(None, window)
                    if hwnd:
                        process_name = ApplicationInfo.get_process_name(hwnd)
                        window = window.replace(os.path.expanduser("~"), '~')
                        self.log(f"{i}: {process_name} -> {window}")
                except Exception as e:
                    self.log.error(f"Error retrieving process for window '{window}': {e}")


    def track_mouse(self, button, x, y, pressed):
        """
        Track mouse events and set the mouse down state.

        Args:
            button: The mouse button that was clicked or released.
            x: The x-coordinate of the mouse event.
            y: The y-coordinate of the mouse event.
            pressed: Whether the button was pressed or released.
        """
        if pressed:
            self.mouse_down = True
            self.mouse_event_buffer[button] = f"{button} clicked at ({x}, {y})"
        else:
            self.mouse_down = False
            if button in self.mouse_event_buffer:
                self.log(f"{self.mouse_event_buffer[button]}, released at ({x}, {y})")
                del self.mouse_event_buffer[button]


    def build_key_sequence(self, key_str):
        """
        Add the next letter to the key sequence until an exit condition is found.
        Then log the sequence and initialize it.

        Args:
            key_str: The string representation of the key to be added to the sequence.
        """
        if key_str == '[enter]' and self.key_sequence:
            self.key_sequence.append(' [ENTER] ')
            self.log(f"Key sequence: {''.join(self.key_sequence)}")
            self.key_sequence = []
        elif key_str == '[esc]' and self.key_sequence:
            self.key_sequence.append(' [ESC] ')
            self.log(f"Key sequence: {''.join(self.key_sequence)}")
            self.key_sequence = []
        elif key_str in ('[space]', '[tab]'):
            self.key_sequence.append(' ')
        elif key_str == 'backspace':
            if self.key_sequence:
                self.key_sequence.pop()
        elif key_str in ['shift_r', 'shift_l']:
            pass
        elif key_str == 'cmd':
            self.key_sequence.append(" [WIN] ")
            self.log_open_windows()
        else:
            self.key_sequence.append(key_str)



    def handle_elevators(self, key_str):
        """
        Handle elevator keys (Ctrl, Alt) and their combinations.

        Args:
            key_str: The string representation of the key that was pressed or released.
        """
        # check if any modifier key from set self.modifier_keys is in self.elevator_keys
        if key_str in self.modifier_keys and not self.modifier_detected:
            self.elevators.update(self.elevator_keys)
            self.modifier_detected = key_str
        elif self.modifier_detected and key_str != self.modifier_detected:
            self.elevators.add(key_str)
            self.elevator_keys.add(key_str)
        else:
            self.elevator_keys.add(key_str)

    def clean_elevators(self, *args, **kwargs):
        if not self.elevator_keys and self.modifier_detected:
            # create a copy of self.elevators to be returned
            elevators = self.elevators.copy()
            mod_str = (
                f"{self.modifier_detected.split('_')[0]}+"
                f"{'+'.join(sorted(list(elevators), key=len, reverse=True))}"
            )
            self.log(f"clean_elevators info elevators: {mod_str}")
            elevators.add(self.modifier_detected)
            self.modifier_detected = False
            self.elevators.clear()
            return elevators

    def reset_pause_timer(self):
        """
        Reset the typing pause timer.
        """
        if self.pause_timer:
            self.pause_timer.cancel()
        self.pause_timer = Timer(self.PAUSE_THRESHOLD, self.log_key_sequence)
        self.pause_timer.start()

    def log_key_sequence(self):
        """
        Log the current key sequence.
        """
        if self.key_sequence:
            self.log(f"Key sequence: {''.join(self.key_sequence)}")
            self.key_sequence = []

    @staticmethod
    @lru_cache(maxsize=128)
    def get_str_representation(key) -> str:
        """
        Get the string representation of the key.

        Args:
            key: The key to be converted to its string representation.

        Returns:
            str: The string representation of the key.
        """
        if isinstance(key, KeyCode) and key.char:
            return key.char
        elif isinstance(key, Key):
            if key == Key.enter:
                return '[enter]'
            elif key == Key.esc:
                return '[esc]'
            elif key == Key.space:
                return '[space]'
            elif key == Key.tab:
                return '[tab]'
            elif key == Key.backspace:
                return 'backspace'
            elif key == Key.shift:
                return 'shift'
            return str(key).replace('Key.', '')
        elif isinstance(key, str):
            return key
        else:
            return repr(key)

    @staticmethod
    @lru_cache(maxsize=128)
    def ctrl_mapping(key_str) -> str:
        """
        Map Ctrl key combinations to their corresponding letters.

        Args:
            key: The key to be mapped.

        Returns:
            str: The corresponding letter for Ctrl key combinations.
        """
        print(f"ctrl_mapping: {key_str = }, {type(key_str) = }")
        if key_str.startswith("\\x"):
            hex_value = key_str[2:]
            ascii_value = int(hex_value, 16)
            if 1 <= ascii_value <= 26:
                return chr(ascii_value + 96)  # Convert to corresponding letter
        if len(key_str) == 1 and 1 <= ord(key_str) <= 26:
            return chr(ord(key_str) + 96)
        return key_str

    def check_exit_condition(self, key) -> bool:
        """
        Check if the key pressed should trigger an exit condition and perform the exit if true.

        Args:
            key: The key to check.

        Returns:
            bool: True if the key should trigger an exit, False otherwise.
        """
        if ApplicationInfo.get_str_representation(key).lower() == 'q':
            self.running = False
            self.keyboard_listener.stop()
            self.mouse_listener.stop()
            return True
        return False

    def on_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: The key that was pressed.
        """
        if self.check_exit_condition(ApplicationInfo.get_str_representation(key)):
            return

        # Run ctrl_mapping first to convert control characters
        key_str = ApplicationInfo.ctrl_mapping(ApplicationInfo.get_str_representation(key))
        # Handle elevator keys
        self.handle_elevators(key_str)
        # Build key sequence only if elevator keys are empty
        if not self.modifier_detected and self.get_active_window()[0] not in self.not_tracked:
            self.build_key_sequence(key_str)
            self.reset_pause_timer()  # Reset the typing pause timer

    def on_release(self, key, *args, **kwargs):
        """
        Handle key release events.
        
        Args:
            key: The key that was released.
        """
        key_str = ApplicationInfo.ctrl_mapping(ApplicationInfo.get_str_representation(key))
        # handle_elevator_removals
        if key_str in self.elevator_keys:
            self.elevator_keys.remove(key_str)
        self.elevator_actions(self.clean_elevators(*args, **kwargs), *args, **kwargs)

    def elevator_actions(self, elevators, *args, **kwargs):
        if elevators is not None:
            # Check if elevators is identical to one of the following sets
            if elevators == {'alt_l', '[tab]'} or elevators == {'ctrl_l', '[tab]'}:
                self.log(f"entering: {self.get_active_window()[0]}")
            if elevators == {'ctrl_l', 's'} or elevators == {'ctrl_r', 's'}:
                active_window = self.get_active_window()
                file_name = self.extract_file_name(active_window[1])
                self.log(f"saving file: {file_name} in {active_window[0]}")

    def extract_file_name(self, active_window, *args, **kwargs):
        """
        Extract the file name from the active window title.
        This implementation assumes that the file name is part of the \
        window title.
        """
        if active_window:
            # Assuming the file name is part of the window title and \
            # follows a common pattern
            # Example: "something.py - Sublime Text"
            parts = active_window.split('-')
            if len(parts) > 1:
                file_name = parts[0].strip()
                return file_name
        return "Unknown file"

    def on_click(self, x, y, button, pressed):
        """
        Handle mouse click events.

        Args:
            x: The x-coordinate of the mouse click.
            y: The y-coordinate of the mouse click.
            button: The mouse button that was clicked.
            pressed: Whether the button was pressed.
        """
        self.track_mouse(button, x, y, pressed)
        self.get_active_window()
        if self.switched_window:
            self.log(f"Window change: {self.previous_window} -> {self.active_window}")
            self.switched_window = False

    @staticmethod
    @lru_cache(maxsize=128)
    def get_process_name(hwnd, *args, **kwargs):
        """
        Get the process name for a given window handle.

        Args:
            hwnd: Window handle.

        Returns:
            str: The name of the process associated with the window handle.
        """
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid <= 0:
                raise ValueError(f"Invalid PID: {pid}")
            return psutil.Process(pid).name()
        except Exception as e:
            return f"Error: {e}"

    def get_active_window(self, *args, **kwargs):
        """
        Get the active window process name and title.
        Returns:
            Tuple[str, str]: The process name and title of the active window.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                raise ValueError("Invalid hwnd: 0")
            active_window = ApplicationInfo.get_process_name(hwnd, *args, **kwargs)
            window_title = win32gui.GetWindowText(hwnd)
            if active_window != self.active_window:
                self.previous_window = self.active_window
                self.active_window = active_window
                self.switched_window = True
            return self.active_window, window_title
        except Exception as e:
            self.log(f"Error getting active window: {e}")
            return f"Error: {e}", ""

    # def get_active_window(self, *args, **kwargs):
    #     """
    #     Get the active window process name.

    #     Returns:
    #         str: The process name of the active window.
    #     """
    #     try:
    #         hwnd = win32gui.GetForegroundWindow()
    #         if hwnd == 0:
    #             raise ValueError("Invalid hwnd: 0")
    #         active_window = ApplicationInfo.get_process_name(hwnd, *args, **kwargs)
    #         if active_window != self.active_window:
    #             self.previous_window = self.active_window
    #             self.active_window = active_window
    #             self.switched_window = True
    #         return self.active_window
    #     except Exception as e:
    #         self.log(f"Error getting active window: {e}")
    #         return f"Error: {e}"


if __name__ == "__main__":
    app_info = ApplicationInfo()
    app_info.run()

