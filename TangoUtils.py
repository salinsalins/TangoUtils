import json
import logging
import sys
import time

try:
    import tango
    from tango.server import Device

    # Handler for logging to the tango log system
    class TangoLogHandler(logging.Handler):
        def __init__(self, device: tango.server.Device, level=logging.DEBUG, formatter=None):
            super().__init__(level)
            self.device = device
            if formatter is None and hasattr(config_logger, 'log_formatter'):
                self.setFormatter(config_logger.log_formatter)

        def emit(self, record):
            level = self.level
            if level >= logging.CRITICAL:
                log_entry = self.format(record)
                Device.fatal_stream(log_entry)
            elif level >= logging.WARNING:
                log_entry = self.format(record)
                Device.error_stream(log_entry)
            elif level >= logging.INFO:
                log_entry = self.format(record)
                Device.info_stream(log_entry)
            elif level >= logging.DEBUG:
                log_entry = self.format(record)
                Device.debug_stream(log_entry)
except:
    pass

# log format string with process id and thread id
LOG_FORMAT_STRING = '%(asctime)s,%(msecs)3d %(levelname)-7s [%(process)d:%(thread)d] %(filename)s ' \
                    '%(funcName)s(%(lineno)s) %(message)s'
# log format string without process id and thread id
LOG_FORMAT_STRING_SHORT = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'


def config_logger(name=None, level: int = logging.DEBUG, format_string=None, force_add_handler=False):
    if name is None:
        if hasattr(config_logger, 'logger'):
            return config_logger.logger
        else:
            name = __name__
    # create an configure logger
    logger = logging.getLogger(name)
    config_logger.logger = logger
    logger.propagate = False
    logger.setLevel(level)
    # do not add extra console handlers if logger already has one. Add any manually if needed.
    if logger.hasHandlers() and not force_add_handler:
        return logger
    if format_string is None:
        format_string = LOG_FORMAT_STRING
    log_formatter = logging.Formatter(format_string, datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    config_logger.log_formatter = log_formatter
    return logger


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if te - ts > 0.01:
            print('%r %2.2f sec' % (method.__name__, te - ts))
        return result

    return timed


def log_exception(logger, message=None, *args, level=logging.ERROR):
    try:
        if not isinstance(logger, logging.Logger):
            logger = logger.logger
    except:
        return
    if not isinstance(logger, logging.Logger):
        return
    ex_type, ex_value, traceback = sys.exc_info()
    tail = ' %s' % ex_value
    if message is None:
        message = 'Exception '
    message += tail
    logger.log(level, message % args)
    logger.debug('Exception: ', exc_info=True)


def split_attribute_name(name):
    # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
    split = name.split('/')
    a_n = split[-1]
    m = -1 - len(a_n)
    d_n = name[:m]
    return d_n, a_n


def convert_polling_status(status_string_array, name: str):
    result = {'period': 0, 'depth': 0}
    s1 = 'Polled attribute type = '
    s2 = 'Polling period (mS) = '
    s3 = 'Polling ring buffer depth = '
    # s4 = 'Time needed for the last attribute reading (mS) = 100'
    # s4 = 'Data not updated since 54 mS'
    # s6 = 'Delta between last records (in mS) = 98, 100, 101, 98'
    n1 = s1 + name
    for s in status_string_array:
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
        self.file_name = None
        self.read(file_name)

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

    def read(self, file_name, append=True):
        try:
            # Read config from file
            with open(file_name, 'r') as configfile:
                data = json.loads(configfile.read())
            # import data
            if append:
                for d in data:
                    self.data[d] = data[d]
            else:
                self.data = data
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
