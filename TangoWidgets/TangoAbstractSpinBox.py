# coding: utf-8
'''
Created on Jan 3, 2020

@author: sanin
'''
import math

from PyQt5 import QtCore
from PyQt5.QtWidgets import QAbstractSpinBox
from TangoWidgets.TangoWriteWidget import TangoWriteWidget


class TangoAbstractSpinBox(TangoWriteWidget):
    def __init__(self, name, widget: QAbstractSpinBox, readonly=False):
        super().__init__(name, widget, readonly)
        self.widget.setKeyboardTracking(False)
        self.widget.old_step_by = self.widget.stepBy
        self.widget.stepBy = self.step_by
        if not readonly:
            self.widget.valueChanged.connect(self.callback)
            self.widget.old_keyPressEvent = self.widget.keyPressEvent
            self.widget.keyPressEvent = self.keyPressEvent
        self.read()
        self.set_widget_value()

    # def update(self, decorate_only=False):
    #     super().update(decorate_only)
    #     self.widget.lineEdit().deselect()

    def set_widget_value(self):
        if not self.attribute.is_valid():
            # dont set value from invalid attribute
            return
        bs = self.widget.blockSignals(True)
        try:
            if math.isnan(self.attribute.value()):
                self.widget.setValue(0)
            else:
                self.widget.setValue(int(self.attribute.value()))
        except:
            self.logger.warning('Exception set widget value for %s' % self.attribute.full_name)
            self.logger.debug('Exception Info:', exc_info=True)
        self.widget.blockSignals(bs)

    def keyPressEvent(self, e):
        self.widget.old_keyPressEvent(e)
        k = e.key()
        if k == QtCore.Qt.Key_Enter or k == QtCore.Qt.Key_Return:
            self.callback(self.widget.value())

    def callback(self, value):
        super().callback(value)
        self.widget.lineEdit().deselect()

    def deselect(self):
        self.widget.lineEdit().deselect()

    def step_by(self, n):
        self.widget.old_step_by(n)
        self.widget.lineEdit().deselect()
