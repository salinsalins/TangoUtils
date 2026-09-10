# coding: utf-8
'''
Created on Jan 3, 2020

@author: sanin
'''
import math

from PyQt5 import QtCore
from PyQt5.QtWidgets import QSpinBox

from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox


class TangoSpinBox(TangoAbstractSpinBox):
    def __init__(self, name, widget: QSpinBox, readonly=False):
        super().__init__(name, widget, readonly)
