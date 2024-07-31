import logging
from logging.handlers import TimedRotatingFileHandler
from utils.constants import (
    LOG_FILE_TIME_FORMAT,
    LOG_LEVEL,
    TIMELY_LOGGER_INTERVAL,
    LOGGER_BACKUP_COUNT,
)
from datetime import datetime, timedelta


class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """Overwriting the default timed rotating file handler"""

    def rotation_filename(self, default_name: str) -> str:
        """Customizing the file name"""
        date_str = (datetime.now() - timedelta(days=1)).strftime(LOG_FILE_TIME_FORMAT)
        final_name = default_name.rindex(".log")
        base_file_name = default_name[:final_name]
        return f"{base_file_name}_{date_str}.log"


def singleton(cls):
    """Handles creating singleton class"""
    all_instance = [None]

    def decorator(*args, **kwargs):
        """Inner function"""
        if all_instance[0] is None:
            all_instance[0] = cls(*args, **kwargs)
        return all_instance[0]

    return decorator


@singleton
class CustomLogger:
    """Class to manage logging for this application"""

    def __init__(self, logger_file_path: str):
        """Initializing timely logger object

        params:
            - logger_file_path : Log file path
        """
        try:
            log_level = LOG_LEVEL
            logger = logging.getLogger(__name__)
            ch = CustomTimedRotatingFileHandler(
                logger_file_path,
                when=TIMELY_LOGGER_INTERVAL,
                backupCount=LOGGER_BACKUP_COUNT,
            )  # creating custom time rotating file handler
            formatter = logging.Formatter(
                "%(asctime)s,%(msecs)d - %(levelname)s - [%(filename)s:%(lineno)d] %(funcName)s - %(message)s"
            )  # adding logger formatter
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            logger.setLevel(log_level)
            self.logger = logger
        except Exception as err:
            print(f"Error in creating logger: {err}")
            self.logger = None

    def get_logger(self):
        """Function to get the logger instance.
        If the logger instance already exists then
        it will return the same.

        return:
            - logger_instance : The logger instance
        """
        return self.logger
