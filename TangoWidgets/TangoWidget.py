# coding: utf-8
"""
Created on Jan 1, 2020

@author: sanin
"""

import sys
import logging

from PyQt5.QtWidgets import QWidget

from config_logger import config_logger
from log_exception import log_exception
from TangoWidgets.TangoAttribute import TangoAttribute, TangoAttributeConnectionFailed


class TangoWidget:
    ERROR_TEXT = '****'
    RECONNECT_TIMEOUT = 3.0  # seconds

    def __init__(self, name: str, widget: QWidget, readonly: bool = True,
                 decorate_only: bool = False, level=logging.DEBUG, **kwargs):
        self.name = name
        self.logger = kwargs.pop('logger', config_logger(level=level))
        self.decorate_only = decorate_only
        # widget
        self.widget = widget
        self.widget.tango_widget = self
        # create attribute proxy
        self.attribute = TangoAttribute(name, logger=self.logger, readonly=readonly, **kwargs)
        # first update
        self.update(decorate_only=False, sync=True, force_read=True)

    def decorate_error(self, color: str = 'gray', **kwargs):
        if hasattr(self.widget, 'setText'):
            text = kwargs.get('text', TangoWidget.ERROR_TEXT)
            self.widget.setText(text)
        self.widget.setStyleSheet('color: ' + color)

    def decorate_invalid(self, color: str = 'red', **kwargs):
        self.decorate_error(color=color)

    def decorate_invalid_data_format(self, color: str = 'red', text: str = None, **kwargs):
        self.decorate_invalid(text=text, color=color, **kwargs)

    def decorate_not_equal(self, color: str = 'red', text: str = None, **kwargs):
        self.decorate_invalid(text=text, color=color, **kwargs)

    def decorate_invalid_quality(self, **kwargs):
        self.decorate_invalid(**kwargs)

    def decorate_valid(self, *args, **kwargs):
        self.widget.setStyleSheet('')

    def read(self, **kwargs):
        return self.attribute.read(**kwargs)

    def write(self, value):
        self.attribute.write(value)

    # compare widget displayed value and read attribute value
    def compare(self):
        return True

    def set_widget_value(self):
        if not (self.attribute.is_scalar() and self.attribute.is_valid()):
            self.logger.debug('Value from invalid attribute is not set')
            # dont set value from invalid attribute
            return
        # block update events for widget
        bs = self.widget.blockSignals(True)
        # set widget value
        if hasattr(self.widget, 'setValue'):
            self.widget.setValue(self.attribute.value())
        elif hasattr(self.widget, 'setChecked'):
            self.widget.setChecked(bool(self.attribute.value()))
        elif hasattr(self.widget, 'setText'):
            self.widget.setText(self.attribute.text())
        # restore update events for widget
        self.widget.blockSignals(bs)

    def update(self, decorate_only=None, **kwargs) -> None:
        if decorate_only is None:
            decorate_only = self.decorate_only
        try:
            self.read(**kwargs)
            if not decorate_only:
                self.set_widget_value()
            self.decorate()
        except TangoAttributeConnectionFailed:
            # log_exception(self.logger, no_info=True)
            # self.set_attribute_value()
            self.logger.error('Connection failed for %s', self.name)
            self.decorate_error()
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger)
            self.decorate_error()

    def decorate(self):
        if not self.attribute.connected:
            # self.logger.debug('%s is not connected' % self.name)
            self.decorate_error()
        elif not self.attribute.is_scalar():
            # self.logger.debug('%s is non scalar' % self.name)
            self.decorate_invalid_data_format()
        elif not self.attribute.is_valid():
            # self.logger.debug('%s is invalid' % self.name)
            self.decorate_invalid_quality()
        else:
            if not self.compare():
                # self.logger.debug('%s not equal' % self.name)
                self.decorate_not_equal()
            else:
                self.decorate_valid()

    def set_attribute_value(self, value=None):
        if self.attribute.is_readonly():
            return
        if value is None:
            value = self.get_widget_value()
        if value is None:
            return
        if isinstance(value, bool) and (not self.attribute.is_boolean()):
            return
        try:
            self.write(value)
        except KeyboardInterrupt:
            raise
        except:
            log_exception('Exception')

    def get_widget_value(self):
        result = None
        if hasattr(self.widget, 'value'):
            result = self.widget.value()
        elif hasattr(self.widget, 'isChecked'):
            result = self.widget.isChecked()
        elif hasattr(self.widget, 'text'):
            result = self.widget.text()
        return result

    def callback(self, value):
        if self.attribute.is_readonly():
            return
        try:
            self.write(value)
            self.read(sync=True)
            # self.set_widget_value()
            # self.logger.debug('***** %s', self.attribute.read_result.value)
            self.decorate()
        except KeyboardInterrupt:
            raise
        except:
            log_exception('Exception in callback')
            self.decorate()
