import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class CustomRotatingFileHandler(RotatingFileHandler):
    def __init__(self, base_name, *args, **kwargs):
        """
        Initialize the CustomRotatingFileHandler with a base name, used to generate
        module-specific log file names. This handler supports customized log file
        rollover with filenames in the format: <base_name>_<timestamp>_<counter>.log.

        Args:
            base_name (str): The base name used to identify the module (e.g., 'main').
            *args: Variable length argument list passed to the RotatingFileHandler.
            **kwargs: Arbitrary keyword arguments passed to the RotatingFileHandler.
        """
        self.base_name = base_name
        self.rotation_count = 0
        self.current_time = datetime.now().strftime("%Y%m%d")
        super().__init__(self._generate_filename(), *args, **kwargs)

    def _generate_filename(self):
        """
        Generate a filename based on the base name, current timestamp, and rotation count.

        Returns:
            str: The generated filename in the format <base_name>_<timestamp>_<counter>.log.
        """
        return f"{self.base_name}_{self.current_time}_{self.rotation_count}.log"

    def doRollover(self):
        """
        Perform a log rollover, closing the current log file and creating a new file
        with an incremented counter in the filename. This method renames the existing
        log file and creates a new log file with the current timestamp, ensuring unique
        filenames with each rotation.

        - Closes the existing log file if open.
        - Updates the filename based on the current timestamp and rotation counter.
        - Resets the timestamp and rotation counter if the date/time changes.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Increment rotation count and update the filename with timestamp and counter
        self.rotation_count += 1
        rotated_filename = self._generate_filename()

        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, rotated_filename)

        # Reset timestamp and rotation count if date/time changes
        new_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        if new_time != self.current_time:
            self.current_time = new_time
            self.rotation_count = 1

        self.baseFilename = self._generate_filename()
        self.stream = self._open()


def get_logger(module_name, log_level=logging.INFO):
    """
    Retrieve a logger configured for a specific module, with console and optional file logging.
    If running in a local environment, a rotating file handler is added, which creates
    log files specific to each module with rollover support.

    Args:
        module_name (str): The name of the module for which logging is configured, used in the filename.
        log_level (int, optional): The logging level, default is logging.INFO.

    Returns:
        logging.Logger: A configured logger instance with console and file handlers.
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - Line: %(lineno)d')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Conditionally add a module-specific FileHandler if running locally
        env = os.environ.get("ENV", "")
        if env == 'LOCAL':
            # Use CustomRotatingFileHandler with module-specific base name
            file_handler = CustomRotatingFileHandler(module_name, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
