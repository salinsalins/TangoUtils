#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prototype for Python based tango device server
A. L. Sanin, started 04.07.2025
"""
import collections
import logging
import time

LOG_FORMAT = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'

class WidgetLogHandler(logging.Handler):
    def __init__(self, widget, maxlen=-1, formatter=None):
        self.widget = None
        if not hasattr(widget, 'setText'):
            raise ValueError('Incompatible widget for Log Handler')
        super().__init__()
        self.widget = widget
        self.limit = maxlen
        if formatter is None:
            formatter = logging.Formatter(LOG_FORMAT, datefmt='%H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        log_entry = self.format(record)
        if self.limit > 0:
            log_entry = log_entry[:self.limit]
        if self.widget is not None:
            self.widget.setText(log_entry)
