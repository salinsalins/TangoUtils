# coding: utf-8
"""
Created on Mar 14, 2020

@author: sanin
"""

import math

from PyQt5.QtWidgets import QLabel
from TangoWidgets.TangoLabel import TangoLabel


class TangoPfiefferPressure(TangoLabel):
    def __init__(self, name, widget: QLabel):
        super().__init__(name, widget)

    def pressure(self):
        if self.attribute.value() is not None:
            return math.pow(10.0, (1.667 * self.attribute.value() - 11.46))
        return float('nan')

    def set_widget_value(self):
        try:
            txt = self.attribute.format % self.pressure()
        except:
            txt = str(self.pressure())
        self.widget.setText(txt)

