# coding: utf-8
"""
Created on Jan 3, 2020

@author: sanin
"""
from PyQt5.QtWidgets import QRadioButton
from TangoWidgets.TangoWidget import TangoWidget


class TangoRadioButton(TangoWidget):
    def __init__(self, name, widget: QRadioButton, readonly=False):
        super().__init__(name, widget, readonly)
        self.widget.toggled.connect(self.callback)

    def decorate_error(self, color: str = 'grey', **kwargs):
        self.widget.setStyleSheet('color: ' + color)
        self.widget.setEnabled(False)

    def decorate_invalid(self):
        self.widget.setStyleSheet('color: red')
        self.widget.setEnabled(True)

    def decorate_valid(self):
        self.widget.setStyleSheet('color: black')
        self.widget.setEnabled(True)
