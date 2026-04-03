# coding: utf-8
"""
Created on Mar 2, 2020

@author: sanin
"""
import logging
import time

from TangoWidgets.TangoAttribute import TangoAttribute
from config_logger import config_logger


class TangoMultiAttribute:
    def __init__(self, attributes: [str], level=logging.DEBUG, readonly=False, use_history=True):
        self.attribute_names = attributes
        self.full_name = ''
        self.use_history = use_history
        self.connected = False
        self.readonly = readonly
        # configure logging
        self.logger = config_logger(level=level)
        self.tango_attributes = {}
        # connect attributes
        self.connect()
        self.read_result = []
        self.time = 0.0

    def connect(self):
        all_connected = True
        self.full_name = ''
        for attr in self.attribute_names:
            if attr not in self.tango_attributes:
                self.tango_attributes[attr] = TangoAttribute(attr, level=self.logger.level, readonly=self.readonly)
            if self.tango_attributes[attr].connected:
                self.full_name = self.full_name + ' ' + self.tango_attributes[attr].full_name
            all_connected = all_connected or self.tango_attributes[attr].connected
        self.connected = all_connected

    def disconnect(self):
        if not self.connected:
            return
        for attr in self.tango_attributes:
            self.tango_attributes[attr].disconnect()
        self.connected = False
        self.time = time.time()
        self.logger.debug('Attribute %s has been disconnected.', self.full_name)

    def reconnect(self):
        for attr in self.tango_attributes:
            self.tango_attributes[attr].reconnect()

    def is_readonly(self):
        result = True
        for attr in self.tango_attributes:
            result = result and self.tango_attributes[attr].is_readonly()
        return result

    def is_valid(self):
        result = True
        for attr in self.tango_attributes:
            result = result and self.tango_attributes[attr].is_valid()
        return result

    def is_boolean(self):
        result = True
        for attr in self.tango_attributes:
            result = result and self.tango_attributes[attr].is_boolean()
        return result

    def is_scalar(self):
        result = True
        for attr in self.tango_attributes:
            result = result and self.tango_attributes[attr].is_scalar()
        return result

    def read(self, force=False):
        self.reconnect()
        self.read_result = []
        for attr in self.tango_attributes:
            self.tango_attributes[attr].read()
            self.read_result.append(self.tango_attributes[attr].value())
        return self.value()

    def write(self, value):
        if self.readonly:
            return
        self.reconnect()
        for attr in self.tango_attributes:
            attr.write(value)
        return self.value()

    def value(self):
        v = True
        for rres in self.read_result:
            v = v and bool(rres)
        return v

    def text(self):
        try:
            txt = self.format % self.value()
        except:
            txt = str(self.value())
        return txt
