#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prototype for Python based tango device server
A. L. Sanin, started 04.11.2022
"""

import logging
import time

import tango
from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command

from Configuration import Configuration
from TangoUtils import TangoLogHandler, TANGO_LOG_LEVELS, TangoDeviceProperties, TangoName
from config_logger import config_logger
from log_exception import log_exception

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'Python Prototype Tango Server'
APPLICATION_NAME_SHORT = 'Python Prototype Tango Server'
APPLICATION_VERSION = '2.0'


class TangoProperty:
    def __init__(self, property_name: str, **kwargs):
        # self.logger = kwargs.pop('config_logger', config_logger())
        self.name = property_name
        self.tango_name = TangoName(property_name)
        self.db = tango.Database()

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
