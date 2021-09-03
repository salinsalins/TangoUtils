#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shot dumper tango device server
A. L. Sanin, started 05.07.2021
"""
import logging
import sys
import json

import numpy
import tango
from tango import AttrQuality, AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command, pipe, device_property

from Utils import config_logger


class TangoServerPrototype(Device):
    # ******** class variables ***********
    server_version = '0.0'
    server_name = 'Python Prototype Tango Server'
    device_list = []

    # ******** attributes ***********
    version = attribute(label="version", dtype=str,
                        display_level=DispLevel.OPERATOR,
                        access=AttrWriteType.READ,
                        unit="", format="%s",
                        doc="Server version")

    name = attribute(label="name", dtype=str,
                     display_level=DispLevel.OPERATOR,
                     access=AttrWriteType.READ,
                     unit="", format="%s",
                     doc="Server name")

    log_level = attribute(label="log_level", dtype=str,
                          display_level=DispLevel.OPERATOR,
                          access=AttrWriteType.READ_WRITE,
                          unit="", format="%7s",
                          doc="Server log level")

    # ******** attribute r/w procedures ***********
    def read_version(self):
        return self.server_version

    def read_name(self):
        return self.server_name

    def read_log_level(self):
        return logging.getLevelName(self.logger.getEffectiveLevel())

    def write_log_level(self, value):
        try:
            self.logger.setLevel(int(value))
        except:
            try:
                self.logger.setLevel(value.upper())
            except:
                pass

    # ******** commands ***********
    @command(dtype_in=int)
    def set_log_level(self, level):
        self.write_log_level(level)
        msg = '%s Log level has been set to %s' % (self.get_name(), self.read_log_level())
        self.logger.info(msg)
        self.info_stream(msg)

    # ******** init_device ***********
    def init_device(self):
        # default logger
        self.logger = config_logger()
        self.set_state(DevState.INIT)
        # default properties
        self.config = Configuration()
        self.device_proxy = tango.DeviceProxy(self.get_name())
        # config from file
        self.read_config_from_file()
        # config from properties
        self.read_config_from_properties()
        # set config
        if self.set_config():
            self.set_state(DevState.RUNNING)
        else:
            self.set_state(DevState.FAULT)

    # ******** additional helper functions ***********
    def log_exception(self, message=None, level=logging.ERROR):
        ex_type, ex_value, traceback = sys.exc_info()
        tail = ' %s %s' % (ex_type, ex_value)
        if message is None:
            message = 'Exception'
        message += tail
        self.logger.log(level, message)
        self.error_stream(message)
        self.logger.debug('', exc_info=True)

    def get_device_property(self, prop: str, default=None):
        try:
            pr = self.device_proxy.get_property(prop)[prop]
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

    def set_device_property(self, prop: str, value: str):
        try:
            self.device_proxy.put_property({prop: value})
        except:
            self.log_exception('Error writing property %s for %s' % (prop, self.get_name()))

    def properties(self, filter: str = '*'):
        # returns dictionary with device properties
        names = self.device_proxy.get_property_list(filter)
        if len(names) > 0:
            return self.device_proxy.get_property(names)
        else:
            return {}

    def read_config_from_properties(self):
        props = self.properties()
        if not hasattr(self, 'config'):
            self.config = Configuration()
        for p in props:
            if p in self.config:
                self.config[p] = type(self.config[p])(props[p][0])
            else:
                self.config[p] = props[p][0]

    def read_config_from_file(self, file_name=None):
        if file_name is None:
            file_name = self.__class__.__name__ + '.json'
        config_file = self.get_device_property('config_file', file_name)
        self.config = Configuration(config_file)

    def set_config(self):
        # set log level
        self.logger.setLevel(self.config.get('log_level', logging.DEBUG))
        self.logger.debug('Log level has been set to %s',
                          logging.getLevelName(self.logger.getEffectiveLevel()))
        return True

    @staticmethod
    def config_logger(name: str = __name__, level: int = None):
        if level is None:
            return  config_logger(name, logging.DEBUG)
        #     if hasattr(TangoServerPrototype.config_logger, 'level'):
        #         level = TangoServerPrototype.config_logger.level
        else:
            return  config_logger(name, level)
        #         level = logging.DEBUG
        # logger = logging.getLogger(name)
        # if not logger.hasHandlers():
        #     logger.propagate = False
        #     logger.setLevel(level)
        #     f_str = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'
        #     log_formatter = logging.Formatter(f_str, datefmt='%H:%M:%S')
        #     console_handler = logging.StreamHandler()
        #     console_handler.setFormatter(log_formatter)
        #     logger.addHandler(console_handler)
        # TangoServerPrototype.config_logger.level = logger.getEffectiveLevel()
        # return logger

    @staticmethod
    def convert_polling_status(p_s, name):
        result = {'period': 0, 'depth': 0}
        s1 = 'Polled attribute name = '
        s2 = 'Polling period (mS) = '
        s3 = 'Polling ring buffer depth = '
        # s4 = 'Time needed for the last attribute reading (mS) = '
        # s4 = 'Data not updated since 54 mS'
        # s6 = 'Delta between last records (in mS) = 98, 100, 101, 98'
        n1 = s1 + name
        for s in p_s:
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

    @staticmethod
    def split_attribute_name(name):
        # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
        split = name.split('/')
        a_n = split[-1]
        m = -1 - len(a_n)
        d_n = name[:m]
        return d_n, a_n

    # def write_attribute(self, attr_name, value):
    #     self.set_device_property(attr_name, str(value))
    #     self.shot_number_value = value
    #     db = self.device_proxy.get_device_db()
    #     apr = db.get_device_attribute_property(self.device_proxy.name(), attr_name)
    #     apr[attr_name]['__value'] = str(value)
    #     db.put_device_attribute_property(self.device_proxy.name(), apr)

def looping():
    pass


def post_init_callback():
    pass


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


if __name__ == "__main__":
    TangoServerPrototype.run_server(post_init_callback=post_init_callback, event_loop=looping)
