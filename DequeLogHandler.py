#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prototype for Python based tango device server
A. L. Sanin, started 04.07.2025
"""
import collections
import logging

LOG_FORMAT = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'

class DequeLogHandler(logging.Handler):
    def __init__(self, maxlen=100, level=logging.DEBUG, formatter=None):
        super().__init__(level)
        self.deque = collections.deque(maxlen=maxlen)
        if formatter is None:
            formatter = logging.Formatter(LOG_FORMAT, datefmt='%H:%M:%S')
        self.setFormatter(formatter)
        self.setLevel(level)

    def emit(self, record):
        log_entry = self.format(record)
        self.deque.append(log_entry)

    def get_value(self):
        return list(self.deque)
