import logging
from log_exception import *

# log format string with process id and thread id
LOG_FORMAT_STRING = '%(asctime)s,%(msecs)3d %(levelname)-7s [%(process)d:%(thread)d] %(filename)s ' \
                    '%(funcName)s(%(lineno)s) %(message)s'
# log format string without process id and thread id
LOG_FORMAT_STRING_SHORT = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'


def config_logger(name=None, level: int = logging.DEBUG, format_string=None):
    if name is None:
        if hasattr(config_logger, 'logger'):
            return config_logger.logger
        else:
            name = __name__
    try:
        logger = inspect.stack()[1].frame.f_locals['self'].logger
    except:
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.setLevel(level)
    config_logger.logger = logger
    # do not add extra console handlers if logger already has one. Add any later if needed.
    if logger.hasHandlers() and format_string is None:
        return logger
    if format_string is None:
        format_string = LOG_FORMAT_STRING
    log_formatter = logging.Formatter(format_string, datefmt='%H:%M:%S')
    config_logger.log_formatter = log_formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    config_logger.console_handler = console_handler
    return logger

