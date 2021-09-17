import json
import logging

import tango
from tango.server import Device


def config_logger(name: str = None, level: int = logging.DEBUG):
    if name is None:
        if hasattr(config_logger, 'name'):
            name = config_logger.name
            logger = logging.getLogger(name)
            return logger
        else:
            name = __name__
    logger = logging.getLogger(name)
    config_logger.name = name
    logger.propagate = False
    logger.setLevel(level)
    if not hasattr(config_logger, 'f_str'):
        f_str = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'
        # f_str = '%(asctime)s,%(msecs)3d %(levelname)-7s [%(process)d:%(thread)d] %(filename)s ' \
        #         '%(funcName)s(%(lineno)s) %(message)s'
        log_formatter = logging.Formatter(f_str, datefmt='%H:%M:%S')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        config_logger.f_str = f_str
        config_logger.log_formatter = log_formatter
        config_logger.console_handler = console_handler
    return logger


# Logging to the tango log system
class TangoLogHandler(logging.Handler):
    def __init__(self, name=None):
        super().__init__()
        self.logger = config_logger()
        self.setFormatter(config_logger.log_formatter)

    def emit(self, record):
        level = self.logger.getEffectiveLevel()
        log_entry = self.format(record)
        if level >= logging.CRITICAL:
            Device.fatal_stream(log_entry)
        elif level >= logging.WARNING:
            Device.error_stream(log_entry)
        elif level >= logging.INFO:
            Device.info_stream(log_entry)
        elif level >= logging.DEBUG:
            Device.debug_stream(log_entry)


def split_attribute_name(name):
    # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
    split = name.split('/')
    a_n = split[-1]
    m = -1 - len(a_n)
    d_n = name[:m]
    return d_n, a_n


def convert_polling_status(status_string, name):
    result = {'period': 0, 'depth': 0}
    s1 = 'Polled attribute type = '
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


class Configuration:
    def __init__(self, file_name=None, default=None):
        if default is None:
            default = {}
        self.data = default
        self.file_name = file_name
        if file_name is not None:
            if not self.read(file_name):
                self.data = default

    def get(self, name, default=None):
        try:
            result = self.data.get(name, default)
            if default is not None:
                result = type(default)(result)
        except:
            result = default
        return result

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        return

    def __contains__(self, key):
        return key in self.data

    def read(self, file_name):
        try:
            # Read config from file
            with open(file_name, 'r') as configfile:
                self.data = json.loads(configfile.read())
                self.file_name = file_name
            return True
        except:
            return False

    def write(self, file_name=None):
        if file_name is None:
            file_name = self.file_name
        if file_name is None:
            return False
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(self.data, indent=4))
        return True
