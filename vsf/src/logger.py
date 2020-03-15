import logging


class Logger:
    def __init__(self, log_file: str) -> None:
        self.log_file = log_file

    def get_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.ERROR)
        file_handle = logging.FileHandler(self.log_file)
        logger.addHandler(file_handle)
        return logger
