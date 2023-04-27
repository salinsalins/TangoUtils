import inspect
import logging

import sys
from tango import DevFailed

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
            # self.device.fatal_stream(log_entry)
            print(log_entry, file=self.device.log_fatal)
        elif level >= logging.WARNING:
            log_entry = self.format(record)
            # self.device.error_stream(log_entry)
            print(log_entry, file=self.device.log_error)
        elif level >= logging.INFO:
            log_entry = self.format(record)
            # self.device.info_stream(log_entry)
            print(log_entry, file=self.device.log_info)
        elif level >= logging.DEBUG:
            log_entry = self.format(record)
            # self.device.debug_stream(log_entry)
            print(log_entry, file=self.device.log_debug)


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


def convert_polling_status2(status_string_array: str, name: str = ''):
    result = {}
    s0 = 'Polled attribute name = '
    s1 = 'Polling period (mS) = '
    s2 = 'Polling ring buffer depth = '
    # s3 = 'Polled attribute type = '
    # s4 = 'Time needed for the last attribute reading (mS) = 100'
    # s4 = 'Data not updated since 54 mS'
    # s6 = 'Delta between last records (in mS) = 98, 100, 101, 98'
    ss = status_string_array.split('\n')
    i = 0
    while i < len(ss):
        if ss[i].startswith(s0):
            n = ss[i].replace(s0, '')
            if not name or name == n:
                result[n] = {}
                i += 1
                if ss[i].startswith(s1):
                    result[n]['period'] = int(ss[i].replace(s1, ''))
                    i += 1
                if ss[i].startswith(s2):
                    result[n]['buffer_depth'] = int(ss[i].replace(s2, ''))
                    i += 1
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


class TangoName:
    # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
    def __init__(self, name: str):
        v = self.from_str(name)
        self.protocol = v[0]
        self.host = v[1]
        self.port = v[2]
        self.device = v[3]
        self.attribute = v[4]
        self.property = v[5]
        self.dbase = v[6]

    def __str__(self):
        v = ''
        if self.protocol:
            v += self.protocol + '//'
        if self.host and self.port:
            v += self.host + ':' + self.port + '/'
        elif self.host:
            v += self.host + '/'
        if self.device:
            v += self.device
        if self.attribute:
            v += '/' + self.attribute
        if self.property:
            v += '->' + self.property
        if self.dbase:
            v += ' dbase=' + self.dbase
        return v

    @staticmethod
    def from_str(name):
        """
        Full object naming schema is

        [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]

        The protocol, host, port, attribute, property and dbase fields are optional. The meaning of these fields are:

        protocol: Specifies which protocol is used(Tango or Taco).Tango is the default

        dbase: The supported value for xx is yes and no.
        This field is used to specify that the device is a device served
         by a device server started with or without database usage. The default value is dbase=yes

        host: port: This field has different meaning according to the dbase value.
        If dbase = yes(the default),
            the host is the host where the control system database server is running and port is the
            database server port. It has a higher priority than the value
            defined by the TANGO_HOST environment variable.
        If dbase = no,
            host is the host name where the device server process
            serving the device is running and port is the device server process port.

        attribute: The attribute name

        property: The property name

        The host: port and dbase = xx fields are necessary only when
        creating the DeviceProxy object used to remotely access the device.
        The -> characters are used to specify a property name.
        """
        na = str(name).split('//')
        # split protocol
        if len(na) == 2:
            protocol = na[0].strip()
            na = na[1]
        elif len(na) == 1:
            protocol = ''
            na = na[0]
        else:
            raise ValueError(f'Incorrect Tango name {name}')
        # split dbase
        n = na.find('dbase=')
        if n > 0:
            dbase = na[n:n + 8]
            na = na[:n]
        else:
            dbase = ''
        # split others
        na = na.split('/')
        # split host:port
        n = na[0].find(':')
        if n > 0:
            host = na[0][:n]
            port = na[0][n + 1:]
            na = na[1:]
        else:
            host = ''
            port = ''
        # split property name and attribute name
        n = na[-1].find('->')
        if n > 0:
            attribute = na[-1][:n].strip()
            property = na[-1][n + 2:].strip()
            na = na[:-1]
        else:
            attribute = ''
            property = ''
        if len(na) != 3:
            raise ValueError(f'Incorrect Tango name {name}')
        device = na[0] + '/' + na[1] + '/' + na[2]
        return protocol, host, port, device, attribute, property, dbase


class TangoProperties:
    #   dict like interface for Tango device attribute properties;
    #   properties = TangoDeviceAttributeProperties(device_name, attribute_name)
    #   property_value = properties[property_name]
    #       property_value is a list['str'] or [] if property_name is absent
    #       to get single value it is necessary to add [0] : a =  properties['b'][0]
    #   properties[property_name] = new_property_value
    def __init__(self):
        self.db = tango.Database()

    def __getitem__(self, key):
        v = self.get_property(key)
        if len(v) <= 0:
            raise KeyError(f'Property {key} does not exist for {self}')
        return v

    def __setitem__(self, key, value):
        self.set_property(key, value)
        return

    def __contains__(self, key):
        v = self.get_property(key)
        return len(v) > 0

    def __delitem__(self, key):
        self.delete_property(key)

    def __iter__(self):
        names = self.get_property_list()
        return iter(names)

    def __reversed__(self):
        names = self.get_property_list()
        return reversed(names)

    def __len__(self):
        names = self.get_property_list()
        return len(names)

    def __call__(self, *args):
        if len(args) <= 0:
            names = self.get_property_list()
        else:
            names = args
        data = {nm: self.get_property(nm) for nm in names}
        return data

    # def __get__(self, instance, owner):
    #     return self.__call__()
    def get_property(self, prop: str) -> list:
        raise NotImplemented

    def get_property_list(self) -> list:
        raise NotImplemented

    def delete_property(self, prop: str):
        raise NotImplemented

    def set_property(self, prop_name: str, value):
        raise NotImplemented

    def convert_value(self, value):
        if isinstance(value, str):
            return [value]
        try:
            return [str(v) for v in value]
        except:
            return [str(value)]

    def get(self, key, default=None):
        v = self.get_property(key)
        if len(v) <= 0:
            v = default
        return v

    def pop(self, key, default=None):
        v = self.get(key, default)
        self.delete_property(key)
        return v

    def to_dict(self):
        return self.__call__()


class TangoDeviceProperties(TangoProperties):
    def __init__(self, device_name=None):
        super().__init__()
        if device_name is None:
            device_name = inspect.stack()[1].frame.f_locals['self'].get_name()
        if isinstance(device_name, tango.server.Device):
            self.device_name = device_name.get_name()
        elif isinstance(device_name, str):
            self.device_name = device_name
        else:
            raise ValueError('Parameter device_name should be string or tango.server.Device')

    def get_property_list(self):
        return self.db.get_device_property_list(self.device_name, '*').value_string

    def get_property(self, prop) -> list:
        # exception free and decompose db results to list
        try:
            sprop = str(prop)
            result = self.db.get_device_property(self.device_name, sprop)[sprop]
            return list(result)
        except:
            return []

    def delete_property(self, prop: str):
        try:
            self.db.delete_device_property(self.device_name, str(prop))
        except:
            pass

    def set_property(self, prop_name: str, value):
        try:
            data = self.convert_value(value)
            self.db.put_device_property(self.device_name, {str(prop_name): data})
            return True
        except:
            return False


class TangoDeviceAttributeProperties(TangoProperties):
    def __init__(self, device_name=None, attribute_name=None):
        super().__init__()
        if isinstance(device_name, tango.server.Device):
            self.device_name = device_name.get_name()
        if isinstance(device_name, str):
            self.device_name = device_name
        else:
            raise ValueError('Parameter device_name should be string or tango.server.Device')
        if isinstance(attribute_name, attribute):
            self.attribute_name = attribute_name.name
        elif isinstance(attribute_name, str):
            self.attribute_name = attribute_name
        else:
            raise ValueError('Parameter attribute_name should be string or tango.server.attribute')

    def get_property(self, property_name: str):
        result = self.db.get_device_attribute_property(self.device_name, self.attribute_name)[self.attribute_name]
        try:
            return self.convert_value(result[property_name])
        except:
            return []

    def get_property_list(self) -> list:
        result = self.db.get_device_attribute_property(self.device_name, {self.attribute_name: []})
        return result[self.attribute_name]

    def set_property(self, prop: str, value):
        data = {str(prop): self.convert_value(value)}
        try:
            self.db.put_device_attribute_property(self.device_name, {self.attribute_name: data})
            return True
        except:
            return False

    def delete_property(self, prop: str):
        try:
            self.db.delete_device_attribute_property(self.device_name, {self.attribute_name: [str(prop)]})
            return True
        except:
            return False


def tango_exception_reason():
    ex_type, ex_value, traceback = sys.exc_info()
    if ex_type == DevFailed:
        return ex_value.args[0].reason
    else:
        # Not DevFailed Exception
        return ''
