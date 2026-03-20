# coding: utf-8
"""
Created on Jan 3, 2020

@author: sanin
"""
import sys

from PyQt5.QtWidgets import QComboBox

from TangoWidgets.TangoWriteWidget import TangoWriteWidget


class TangoComboBox(TangoWriteWidget):
    def __init__(self, name, widget: QComboBox, readonly=False):
        super().__init__(name, widget)
        self.widget.currentIndexChanged.connect(self.callback)

    def decorate_error(self, color='red'):
        self.widget.setStyleSheet('color: red')

    def update(self, decorate_only=True, **kwargs):
        # self.logger.debug('Entry')
        super().update(decorate_only)

    def set_widget_value(self):
        #bs = self.widget.blockSignals(True)
        try:
            self.widget.setCurrentIndex(int(self.attribute.value()))
        except KeyboardInterrupt:
            raise
        except:
            pass
        #self.widget.blockSignals(bs)
        return self.attribute.value()

    def compare(self, delta_v=None):
        try:
            return int(self.attribute.value()) == self.widget.currentIndex()
        except KeyboardInterrupt:
            raise
        except:
            self.logger.debug('Exception in ComboBox compare', exc_info=True)
            return False

    def callback(self, value):
        if self.attribute.connected:
            try:
                self.write(int(value))
                self.decorate_valid()
            except KeyboardInterrupt:
                raise
            except:
                self.logger.debug('Exception %s in callback', sys.exc_info()[1])
                self.decorate_error()
        else:
            self.attribute.reconnect()
            self.decorate_error()
