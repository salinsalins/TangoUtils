import logging


def config_logger(name: str = None, level: int = logging.DEBUG):
    if name is None:
        if hasattr(config_logger, 'name'):
            name = config_logger.name
            logger = logging.getLogger(name)
            return logger
        else:
            name = __name__
            config_logger.name = name
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.propagate = False
        logger.setLevel(level)
        f_str = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'
        log_formatter = logging.Formatter(f_str, datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
    return logger

