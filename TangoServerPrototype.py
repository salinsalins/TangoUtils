#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prototype for Python based tango device server
A. L. Sanin, started 05.07.2021
"""

import logging
import time

import tango
from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command

from Configuration import Configuration
from TangoUtils import TangoLogHandler, TANGO_LOG_LEVELS, TangoDeviceProperties, TangoDeviceAttributeProperties, \
    TangoServerAttribute
from config_logger import config_logger
from log_exception import log_exception

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'Python Prototype Tango Server'
APPLICATION_NAME_SHORT = 'Python Prototype Tango Server'
APPLICATION_VERSION = '2.0'


class TangoServerPrototype(Device):
    # ******** class variables ***********
    server_version_value = APPLICATION_VERSION
    server_name_value = APPLICATION_NAME_SHORT
    device_list = []

   # ******** attributes ***********
    server_version = attribute(label="server_version", dtype=str,
                        display_level=DispLevel.OPERATOR,
                        access=AttrWriteType.READ,
                        unit="", format="%s",
                        doc="Server version")

    server_name = attribute(label="server_name", dtype=str,
                     display_level=DispLevel.OPERATOR,
                     access=AttrWriteType.READ,
                     unit="", format="%s",
                     doc="Server name")

    log_level = attribute(label="log_level", dtype=str,
                          display_level=DispLevel.EXPERT,
                          access=AttrWriteType.READ_WRITE,
                          unit="", format="%7s",
                          doc="Server log level")

    # ******** init_device ***********
    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        # default logger
        self.logger = config_logger()
        # self.debug('%s', self.server_name)
        # self.server_name.properties = TangoDeviceAttributeProperties()
        # default configuration
        self.config = Configuration()
        # config from file
        self.read_config_from_file()
        # config from properties
        self.properties = TangoDeviceProperties(self.get_name())
        self.read_config_from_properties()
        # set config
        self.set_config()

    def set_config(self):
        # set log level
        level = self.config.get('log_level', logging.DEBUG)
        self.logger.setLevel(level)
        self.logger.debug('Log level has been set to %s',
                        logging.getLevelName(self.logger.getEffectiveLevel()))
        self.log_level.set_write_value(logging.getLevelName(self.logger.getEffectiveLevel()))
        self.set_state(DevState.RUNNING)
        TangoServerPrototype.device_list.append(self)
        return True

    def delete_device(self):
        self.write_config_to_properties()

    # ******** attribute r/w procedures ***********
    def read_server_version(self):
        return self.server_version_value

    def read_server_name(self):
        # self.debug('server_name properties %s', self.server_name.properties())
        # self.debug('server_name properties %s', self.server_name)
        # self.debug('server_name properties %s', hasattr(self.server_name, 'properties'))
        return self.server_name_value

    def read_log_level(self):
        return logging.getLevelName(self.logger.getEffectiveLevel())

    def write_log_level(self, value):
        try:
            try:
                v = int(value)
            except:
                v = value.upper()
            self.logger.setLevel(v)
            # configure tango logging
            util = tango.Util.instance(self)
            dserver = util.get_dserver_device()
            # 5 - DEBUG; 4 - INFO; 3 - WARNING; 2 - ERROR; 1 - FATAL; 0 - OFF
            level = TANGO_LOG_LEVELS[self.read_log_level()]
            tango.DeviceProxy(dserver.get_name()).command_inout('SetLoggingLevel', [[level], [self.get_name()]])
            self.set_running()
        except:
            self.set_fault()
            self.log_exception('Can not set Log level to %s', value)

    def set_tango_log_level(self, level=None):
        self.util = tango.Util.instance(self)
        self.dserver = self.util.get_dserver_device()
        self.dserver_name = self.dserver.get_name()
        self.dserver_proxy = tango.DeviceProxy(self.dserver_name)
        if level is None:
            level = TANGO_LOG_LEVELS[self.read_log_level()]
        elif isinstance(level, str):
            level = TANGO_LOG_LEVELS[level.upper()]
        self.dserver_proxy.command_inout('SetLoggingLevel', [[level], [self.get_name()]])

    # ******** commands ***********
    @command(dtype_in=int)
    def set_log_level(self, level):
        self.write_log_level(level)
        msg = '%s Log level has been set to %s' % (self.get_name(), self.read_log_level())
        self.info(msg)

    # ******** additional helper functions ***********
    def log_exception(self, message='', *args, level=logging.ERROR, **kwargs):
        msg = '%s %s ' % (self.get_name(), message)
        log_exception(self, msg, *args, level=level, stacklevel=3, **kwargs)

    def debug(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        self.logger.debug(message, *args, stacklevel=2, **kwargs)

    def info(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        self.logger.info(message, *args, stacklevel=2, **kwargs)

    def warning(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        self.logger.warning(message, *args, stacklevel=2, **kwargs)

    def error(self, message='', *args, **kwargs):
        message = self.get_name() + ' ' + message
        # kwargs['stacklevel'] = kwargs.copy().pop('stacklevel', 1) +1
        self.logger.error(message, *args, stacklevel=2, **kwargs)

    def get_device_property(self, prop: str, default=None):
        try:
            db = tango.Database()
            pr = db.get_device_property(self.get_name(), prop)[prop]
            # pr = self.device_proxy.get_property(prop)[prop]
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
        prop = str(prop)
        try:
            db = tango.Database()
            # self.device_proxy.put_property({prop: value})
            db.put_device_property(self.get_name(), {prop: [value]})
        except:
            self.log_exception('Error writing property %s for %s' % (prop, self.get_name()))

    def get_attribute_property(self, attr_name, prop_name=None):
        db = tango.Database()
        # db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        if prop_name is None:
            return apr[attr_name]
        return apr[attr_name][prop_name][0]

    def set_attribute_property(self, attr_name, prop_name, value):
        db = tango.Database()
        # db = self.device_proxy.get_device_db()
        apr = db.get_device_attribute_property(self.get_name(), attr_name)
        apr[attr_name][prop_name] = str(value)
        db.put_device_attribute_property(self.get_name(), apr)

    # def properties(self, fltr: str = '*'):
    #     # reg = fltr.replace('?', '.').replace('*', '.+')
    #     # returns dictionary with device properties
    #     db = tango.Database()
    #     names = db.get_device_property_list(self.get_name(), fltr).value_string
    #     # names = self.device_proxy.get_property_list(fltr)
    #     d_name = self.get_name()
    #     return {nm: db.get_device_property(d_name, nm)[nm] for nm in names}
    #     # return {n: db.get_device_property(self.get_name(), n)[n] for n in names if re.match(reg, n)}
    #     # if len(names) > 0:
    #     #     # return db.get_device_property(self.get_name(), names)
    #     #     return self.device_proxy.get_property(names)
    #     # else:
    #     #     return {}

    # def get_device_properties(self):
    #     return self.properties()
    #
    def read_config_from_properties(self):
        props = self.properties
        if not hasattr(self, 'config'):
            self.config = Configuration()
        for p in props:
            if p in self.config:
                self.config[p] = type(self.config[p])(props[p][0])
            else:
                self.config[p] = props[p][0]

    def write_config_to_properties(self):
        for p in self.config:
            if p not in self.properties:
                self.properties[p] = self.config[p]
        # self.device_proxy.put_property(self.config.data)

    def read_config_from_file(self, file_name=None):
        if file_name is None:
            file_name = self.__class__.__name__ + '.json'
        if not hasattr(self, 'config'):
            self.config = Configuration(file_name)
        else:
            self.config.read(file_name)

    def configure_tango_logging(self):
        # add logging to TLS
        tlh = TangoLogHandler(self)
        self.logger.addHandler(tlh)

        # set logging level via dserver !!! Working only after server start, not during init !!!
        # util = tango.Util.instance()
        # dserver = util.get_dserver_device()
        # 5 - DEBUG; 4 - INFO; 3 - WARNING; 2 - ERROR; 1 - FATAL; 0 - OFF
        # level = TANGO_LOG_LEVELS[self.logger.getEffectiveLevel()]
        # dserver.command_inout('SetLoggingLevel',[[level],[self.get_name()]])

        # set device logging properties - has no effect
        # self.set_device_property('logging_level', self.logger.getEffectiveLevel())
        # self.set_device_property('logging_level', "5")
        # self.set_device_property('logging_target', 'console')
        # self.init_logger() # has no effect
        # self.start_logging() # has no effect
        # self.tango_logging = True

    def set_running(self, msg='R/W OK'):
        self.set_state(DevState.RUNNING)
        self.set_status(msg)

    def set_fault(self, msg='Error during R/W'):
        self.set_state(DevState.FAULT)
        self.set_status(msg)


def looping():
    for dev in TangoServerPrototype.device_list:
        if not hasattr(dev.server_name, 'properties'):
            print('add')
            dev.server_name.properties = TangoDeviceAttributeProperties(dev.get_name(), 'server_name')
        else:
            print(dev.server_name.properties)
    print('Empty loop. Overwrite or disable.')
    time.sleep(1.0)
    pass


def post_init_callback():
    print('Empty post_init_callback. Overwrite or disable.')
    pass


if __name__ == "__main__":
    # TangoServerPrototype.run_server(post_init_callback=post_init_callback)
    # TangoServerPrototype.run_server(post_init_callback=post_init_callback, event_loop=looping)
    TangoServerPrototype.run_server(event_loop=looping)
    # TangoServerPrototype.run_server()
