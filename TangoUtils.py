import inspect
import logging

import config_logger
import tango
from tango.server import Device, attribute

# from tango._tango import DbData, DbDatum

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
                try:
                    log_formatter = logging.Formatter(config_logger.LOG_FORMAT_STRING, datefmt='%H:%M:%S')
                    self.setFormatter(log_formatter)
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


def get_device_property(device_name: str, prop_name: str, default=None, db=None):
    try:
        if db is None:
            db = tango.Database()
        pr = db.get_device_property(device_name, prop_name)[prop_name]
        result = None
        if len(pr) > 0:
            result = pr[0]
        if default is None:
            return result
        if result is None or result == '':
            return default
        else:
            return type(default)(result)
    except:
        return default


def set_device_property(device_name: str, prop_name: str, value: str, db=None) -> bool:
    try:
        if db is None:
            db = tango.Database()
        db.put_device_property(device_name, {prop_name: [value]})
        return True
    except:
        return False


class TangoDeviceProperties:
    def __init__(self, device_name=None):
        if device_name is None:
            device_name = inspect.stack()[1].frame.f_locals['self'].get_name()
        if isinstance(device_name, tango.server.Device):
            self.name = device_name.get_name()
        elif isinstance(device_name, str):
            self.name = device_name
        else:
            raise ValueError('Parameter device should be string or tango.server.Device')
        self.db = tango.Database()
        names = self.db.get_device_property_list(self.name, '*').value_string
        self.data = {nm: self.get_device_property(nm) for nm in names}

    def __getitem__(self, key):
        if key not in self.data:
            self.data[key] = self.get_device_property(key)
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[str(key)] = self.convert_value(value)
        self.set_device_property(str(key), value)
        return

    def __contains__(self, key):
        return key in self.data

    def __delitem__(self, key):
        if key in self.data:
            self.data.pop(key)
            self.delete_device_property(key)

    def __iter__(self):
        return iter(self.data)

    def __reversed__(self):
        return reversed(self.data)

    def __len__(self):
        return len(self.data)

    def __call__(self):
        return self.data

    def get_device_property(self, prop: str, default=None):
        try:
            result = self.db.get_device_property(self.name, prop)[prop]
            if default is None:
                return self.convert_value(result)
            if result is None or len(result) <= 0:
                return default
            # return type(default)(result)
            return self.convert_value(result)
        except:
            return default

    def delete_device_property(self, prop: str):
        try:
            self.db.delete_device_property(self.name, prop)
        except:
            pass

    def set_device_property(self, prop: str, value):
        prop_name = str(prop)
        try:
            data = self.convert_value(value)
            self.db.put_device_property(self.name, {prop_name: data})
            return True
        except:
            return False

    def convert_value(self, value):
        if isinstance(value, str):
            return [value]
        data = []
        try:
            for v in value:
                data.append(str(v))
            return data
        except:
            return [str(value)]

    def get(self, key, default=None):
        try:
            result = self.data.get(key, default)
            if default is not None and result is not None:
                result = type(default)(result)
        except:
            result = default
        self.__setitem__(key, result)
        return result

    def pop(self, key, default=None):
        try:
            result = self.data.pop(key, default)
            if default is not None and result is not None:
                result = type(default)(result)
        except:
            result = default
        return result


class TangoServerAttribute(attribute):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.properties = TangoServerAttributeProperties()


class TangoServerAttributeProperties:
    def __init__(self, device_name=None, attribute_name=None):
        if device_name is None:
            device_name = inspect.stack()[2].frame.f_locals['self'].get_name()
        if isinstance(device_name, tango.server.Device):
            self.name = device_name.get_name()
        if isinstance(device_name, str):
            self.device_name = device_name
        else:
            raise ValueError('Parameter device_name should be string or tango.server.Device')

        if attribute_name is None:
            attribute_name = inspect.stack()[1].frame.f_locals['self'].name
        if isinstance(attribute_name, attribute):
            self.name = attribute_name.name
        elif isinstance(attribute_name, str):
            self.name = attribute_name
        else:
            raise ValueError('Parameter attribute_name should be string or tango.server.attribute')
        self.db = tango.Database()
        apr = self.db.get_device_attribute_property(self.device_name, self.name)
        self.data = apr[self.name]

    def __getitem__(self, key):
        if key not in self.data:
            self.data[key] = self.get_device_property(key)
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[str(key)] = self.convert_value(value)
        self.set_device_property(str(key), value)
        return

    def __contains__(self, key):
        return key in self.data

    def __delitem__(self, key):
        if key in self.data:
            self.data.pop(key)
            self.delete_device_property(key)

    def __iter__(self):
        return iter(self.data)

    def __reversed__(self):
        return reversed(self.data)

    def __len__(self):
        return len(self.data)

    def __call__(self):
        return self.data

    def get_property(self, property_name: str):
        result = self.db.get_device_attribute_property(self.device_name, self.name)
        return self.convert_value(result[self.name][property_name])

    def delete_property(self, prop: str):
        try:
            self.db.delete_device_property(self.name, prop)
        except:
            pass

    def set_property(self, prop: str, value):
        prop_name = str(prop)
        try:
            data = self.convert_value(value)
            self.db.put_device_property(self.name, {prop_name: data})
            return True
        except:
            return False

    def convert_value(self, value):
        if isinstance(value, str):
            return [value]
        data = []
        try:
            for v in value:
                data.append(str(v))
            return data
        except:
            return [str(value)]

    def get(self, key, default=None):
        try:
            result = self.data.get(key, default)
            if default is not None and result is not None:
                result = type(default)(result)
        except:
            result = default
        self.__setitem__(key, result)
        return result

    def pop(self, key, default=None):
        try:
            result = self.data.pop(key, default)
            if default is not None and result is not None:
                result = type(default)(result)
        except:
            result = default
        return result
