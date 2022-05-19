import logging

import tango
from tango.server import Device

import config_logger

TANGO_LOG_LEVELS = {'DEBUG': 5, 'INFO': 4, 'WARNING': 3, 'ERROR': 2, 'FATAL': 1, 'OFF': 0,
                    5: 'DEBUG', 4: 'INFO', 3: 'WARNING', 2: 'ERROR', 1: 'FATAL', 0: 'OFF'}


# Handler for logging to the tango log system
class TangoLogHandler(logging.Handler):
    def __init__(self, device: tango.server.Device, level=logging.DEBUG, formatter=None):
        super().__init__(level)
        self.device = device
        if formatter is None:
            try:
                self.setFormatter(config_logger.log_formatter)
            except:
                print('ERROR: Formatter is not defined for TangoLogHandler')
        else:
            self.setFormatter(formatter)

    def emit(self, record):
        level = self.level
        if level >= logging.CRITICAL:
            log_entry = self.format(record)
            self.device.fatal_stream(log_entry)
        elif level >= logging.WARNING:
            log_entry = self.format(record)
            self.device.error_stream(log_entry)
        elif level >= logging.INFO:
            log_entry = self.format(record)
            self.device.info_stream(log_entry)
        elif level >= logging.DEBUG:
            log_entry = self.format(record)
            self.device.debug_stream(log_entry)


def get_display_units(dp: tango.DeviceProxy, attrib_name: str):
    config = get_attribute_config(dp, attrib_name)
    try:
        coeff = float(config.display_unit)
    except:
        coeff = 1.0
    return coeff


def get_attribute_config(dp: tango.DeviceProxy, attrib_name: str):
    return dp.get_attribute_config_ex(attrib_name)[0]


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
