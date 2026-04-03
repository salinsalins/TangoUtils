# coding: utf-8
'''
Created on Jan 3, 2020

@author: sanin
'''
import math

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDoubleSpinBox

from TangoAbstractSpinBox import TangoAbstractSpinBox


class TangoDoubleSpinBox(TangoAbstractSpinBox):
    def __init__(self, name, widget: QDoubleSpinBox, readonly=False):
        super().__init__(name, widget, readonly)
    def set_widget_value(self):
        if not self.attribute.is_valid():
            # dont set value from invalid attribute
            return
        bs = self.widget.blockSignals(True)
        try:
            if math.isnan(self.attribute.value()):
                self.widget.setValue(0.0)
            else:
                self.widget.setValue(float(self.attribute.value()))
        except:
            self.logger.warning('Exception set widget value for %s' % self.attribute.full_name)
            self.logger.debug('Exception Info:', exc_info=True)
        self.widget.blockSignals(bs)
