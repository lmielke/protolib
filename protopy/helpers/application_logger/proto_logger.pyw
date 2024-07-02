import os
from datetime import datetime as dt
from threading import Timer, Lock

class BufferedLogger:
    def __init__(self, log_dir: str, flush_interval: int = 300):
        """
        Initialize the BufferedLogger class.

        Args:
            log_dir (str): Directory where log files will be stored.
            flush_interval (int): Interval in seconds to flush the log buffer to the file.
        """
        self.log_dir = log_dir
        self.flush_interval = flush_interval
        self.log_buffer = []
        self.lock = Lock()
        self.timer = None  # Initialize the timer attribute as None

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.current_log_file = os.path.join(log_dir, f"os_activity_{dt.now().strftime('%Y-%m-%d')}.log")
        # Force an initial flush to create the log file
        self.flush()

        # Start the timer after the initial flush
        self.timer = Timer(self.flush_interval, self.flush)
        self.timer.start()

    def log(self, message: str, flush: bool = False):
        """
        Log a message to the buffer.

        Args:
            message (str): The message to be logged.
            flush (bool): Whether to flush the buffer immediately after logging.
        """
        with self.lock:
            self.log_buffer.append(message)
        if flush:
            self.flush()

    def flush(self):
        """
        Flush the log buffer to the log file.
        """
        with self.lock:
            if self.log_buffer:
                buffer_str = '\n'.join(self.log_buffer)
                flush_str = (
                                f"\nflush at {dt.now().strftime('%Y-%m-%d %H:%M')}\n"
                                f"{buffer_str}\n"
                                )
                with open(self.current_log_file, 'a') as log_file:
                    log_file.write(flush_str)
                self.log_buffer = []

        if self.timer is not None:
            self.timer.cancel()

        self.timer = Timer(self.flush_interval, self.flush)
        self.timer.start()

    def stop(self):
        """
        Stop the timer and flush any remaining log messages.
        """
        if self.timer is not None:
            self.timer.cancel()
        self.flush()
