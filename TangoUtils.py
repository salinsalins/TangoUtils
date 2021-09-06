import logging

import tango


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


# Logging to the tango log system
# class TangoLogHandler(logging.Handler):
#     def __init__(self):
#         super().__init__()
#
#     def emit(self, record):
#         level = logging.DEBUG
#         log_entry = self.format(record)
#         if level >= logging.CRITICAL:
#             tango.server.Device.info_stream(log_entry)


def split_attribute_name(name):
    # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
    split = name.split('/')
    a_n = split[-1]
    m = -1 - len(a_n)
    d_n = name[:m]
    return d_n, a_n


def convert_polling_status(status_string, name):
    result = {'period': 0, 'depth': 0}
    s1 = 'Polled attribute name = '
    s2 = 'Polling period (mS) = '
    s3 = 'Polling ring buffer depth = '
    # s4 = 'Time needed for the last attribute reading (mS) = '
    # s4 = 'Data not updated since 54 mS'
    # s6 = 'Delta between last records (in mS) = 98, 100, 101, 98'
    n1 = s1 + name
    for s in status_string:
        if s.startswith(n1):
            for ss in s.split('\n'):
                try:
                    if ss.startswith(s2):
                        result['period'] = int(ss.replace(s2, ''))
                    elif ss.startswith(s3):
                        result['depth'] = int(ss.replace(s3, ''))
                except:
                    pass
    return result
