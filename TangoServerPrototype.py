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

from TangoUtils import config_logger, Configuration, log_exception


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
                     doc="Server type")

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
                self.logger.error('Can not set Log level to %s', value)

    # ******** commands ***********
    @command(dtype_in=int)
    def set_log_level(self, level):
        self.write_log_level(level)
        msg = '%s Log level has been set to %s' % (self.get_name(), self.read_log_level())
        self.logger.info(msg)
        self.info_stream(msg)

    # ******** init_device ***********
    def init_device(self):
        # default LOGGER
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
    def log_exception(self, message=None, *args, level=logging.ERROR):
        log_exception(self, message, *args, level=level)

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

    def get_attribute_property(self, attr_name, prop_name=None):
        db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        if prop_name is None:
            return apr[attr_name]
        return apr[attr_name][prop_name][0]

    def set_attribute_property(self, attr_name, prop_name, value):
        db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        apr[attr_name][prop_name] = str(value)
        db.put_device_attribute_property(self.get_name(), apr)

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
            if len(sys.argv) > 1:
                file_name = self.__class__.__name__ + '_' + sys.argv[1].strip() + '.json'
            else:
                file_name = self.__class__.__name__ + '.json'
        config_file = self.get_device_property('config_file', file_name)
        self.config = Configuration(config_file)

    def set_config(self):
        # set log level
        level = self.config.get('log_level', logging.DEBUG)
        self.logger.setLevel(level)
        self.logger.log(level, 'Log level has been set to %s',
                        logging.getLevelName(self.logger.getEffectiveLevel()))
        return True


def looping():
    pass


def post_init_callback():
    pass


if __name__ == "__main__":
    TangoServerPrototype.run_server(post_init_callback=post_init_callback, event_loop=looping)
