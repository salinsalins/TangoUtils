# coding: utf-8
'''
Created on Feb 25, 2020

@author: sanin
'''
import logging
import sys
import time

import tango
from PyQt5.QtWidgets import QWidget

from TangoWidgets.TangoWidget import TangoWidget
from TangoWidgets.TangoAttribute import TangoAttribute


class TangoMultiAttributeWidget(TangoWidget):
    def __init__(self, name: str, widget: QWidget, readonly=True, level=logging.DEBUG, attributes=[]):
        self.attributes = attributes
        super().__init__(name, widget, readonly, level)
        self.tango_attributes = {self.attribute.full_name: self.attribute}
        for attr in attributes:
            if attr not in self.tango_attributes:
                self.tango_attributes[attr] = TangoAttribute(attr, level=level, readonly=readonly)
        self.update(decorate_only=False)

    def read(self, force=False, **kwargs):
        if not self.connected:
            raise ConnectionError('Attribute disconnected')
        try:
            if not force and self.dp.is_attribute_polled(self.an):
                attrib = self.dp.attribute_history(self.an, 1)[0]
                t1 = attrib.time.tv_sec + (1.0e-6 * attrib.time.tv_usec)
                t2 = self.attr.time.tv_sec + (1.0e-6 * self.attr.time.tv_usec)
                if t1 > t2:
                    self.attr = attrib
            else:
                self.attr = self.dp.read_attribute(self.an)
        except Exception as ex:
            #self.logger.debug('Exception in read', exc_info=True)
            self.attr = None
            self.disconnect_attribute_proxy()
            raise
        self.ex_count = 0
        return self.attr

    def write(self, value):
        if self.readonly:
            return
        try:
            self.dp.write_attribute(self.an, value/self.coeff)
        except Exception as ex:
            self.disconnect_attribute_proxy()
            raise ex

    def write_read(self, value):
        if self.readonly:
            return None
        self.attr = None
        try:
            self.attr = self.dp.write_read_attribute(self.an, value/self.coeff)
            #self.attr = self.attr_proxy.write_read(value/self.coeff)
        except Exception as ex:
            self.attr = None
            self.disconnect_attribute_proxy()
            raise ex
        self.ex_count = 0

    # compare widget displayed value and read attribute value
    def compare(self):
        return True

    def set_widget_value(self):
        if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
            # dont set value from invalid attribute
            return
        bs = self.widget.blockSignals(True)
        if hasattr(self.attr, 'value'):
            if hasattr(self.widget, 'setValue'):
                self.widget.setValue(self.attr.value * self.coeff)
            elif hasattr(self.widget, 'setChecked'):
                self.widget.setChecked(bool(self.attr.value))
            elif hasattr(self.widget, 'setText'):
                if self.format is not None:
                    text = self.format % (self.attr.value * self.coeff)
                else:
                    text = str(self.attr.value)
                self.widget.setText(text)
        self.widget.blockSignals(bs)

    def update(self, decorate_only=False, **kwargs) -> None:
        t0 = time.time()
        try:
            self.read()
            if self.attr.data_format != tango._tango.AttrDataFormat.SCALAR:
                self.logger.debug('Non scalar attribute')
                self.decorate_invalid_data_format()
            else:
                if not decorate_only:
                    self.set_widget_value()
                if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
                    self.logger.debug('%s %s' % (self.attr.quality, self.attr.name))
                    self.decorate_invalid_quality()
                else:
                    if not self.compare():
                        self.decorate_not_equal()
                    else:
                        self.decorate_valid()
        except:
            if self.connected:
                self.logger.debug('Exception updating widget', exc_info=True)
                self.disconnect_attribute_proxy()
            else:
                if (time.time() - self.time) > TangoWidget.RECONNECT_TIMEOUT:
                    self.connect_attribute_proxy()
                if self.connected:
                    if hasattr(self.widget, 'value'):
                        self.write(self.widget.value())
                    elif hasattr(self.widget, 'getChecked'):
                        self.write(self.widget.getChecked())
                    elif hasattr(self.widget, 'getText'):
                        self.write(self.widget.getText())
                    if self.attr.quality != tango._tango.AttrQuality.ATTR_VALID:
                        self.logger.debug('%s %s' % (self.attr.quality, self.attr.name))
                        self.decorate_invalid_quality()
                    else:
                        self.decorate_valid()
                else:
                    self.decorate_error()
        self.update_dt = time.time() - t0
        #print('update', self.attr_proxy, int(self.update_dt*1000.0), 'ms')

    def callback(self, value):
        #self.logger.debug('Callback entry')
        if self.readonly:
            return
        if self.connected:
            try:
                #self.write_read(value)
                self.write(value)
                self.read(True)
                #print('wr', self.attr.value, value)
                if self.attr.quality == tango._tango.AttrQuality.ATTR_VALID:
                    self.decorate_valid()
                else:
                    self.decorate_invalid()
            except:
                self.logger.debug('Exception %s in callback', sys.exc_info()[0])
                self.decorate_error()
        else:
            self.connect_attribute_proxy()
            self.decorate_error()
