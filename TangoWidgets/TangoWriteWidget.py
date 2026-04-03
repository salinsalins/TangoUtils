# coding: utf-8
"""
Created on Jan 17, 2020

@author: sanin
"""

from PyQt5.QtWidgets import QWidget
from tango import DevFailed, DevSource

from TangoWidgets.TangoAttribute import TangoAttributeConnectionFailed
from TangoWidgets.TangoWidget import TangoWidget


class TangoWriteWidget(TangoWidget):
    def __init__(self, name, widget: QWidget,
                 readonly=False, decorate_only=True, **kwargs):
        super().__init__(name, widget, readonly=readonly,
                         decorate_only=decorate_only, **kwargs)
        # if self.attribute.device_proxy is None:
        #     return
        # try:
        #     self.attribute.device_proxy.set_source(DevSource.DEV)
        #     self.attribute.read_sync()
        # except (TangoAttributeConnectionFailed, DevFailed):
        #     pass
        # # update which set widget value from attribute
        # self.update(decorate_only=False)

    def decorate_error(self, *args, **kwargs):
        # self.logger.debug("ERROR decorated for %s", self.name)
        super().decorate_error(*args, **kwargs)
        self.widget.setEnabled(False)

    def decorate_invalid(self, *args, **kwargs):
        super().decorate_invalid(**kwargs)
        # self.widget.setStyleSheet('color: red')
        self.widget.setEnabled(True)

    def decorate_valid(self):
        super().decorate_valid()
        # self.widget.setStyleSheet('')
        self.widget.setEnabled(True)

    def update(self, decorate_only=True, **kwargs):
        super().update(decorate_only=decorate_only)

    # compare widget displayed value and read attribute value
    def compare(self, delta_v=None):
        if self.attribute.is_readonly():
            return True
        else:
            try:
                v = self.attribute.valid_value()
                if v is None:
                    return False
                if self.attribute.is_boolean():
                    flag = v == self.widget.value()
                    if not flag:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, self.widget.value())
                        return False
                    return True
                if self.attribute.is_int():
                    v1 = int(self.widget.value())
                    if v != v1:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                    return True
                if self.attribute.is_numerical():
                    v1 = float(self.widget.value())
                    if delta_v is None:
                        vs = self.attribute.format % v
                        v1s = self.attribute.format % v1
                        flag = v1s == vs
                    else:
                        if v == 0.0:
                            flag = abs(v - v1) <= 1e-3
                        else:
                            flag = abs(v - v1) <= (abs(v) * 3e-3)
                    if not flag:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                    return True
                if isinstance(v, str):
                    v1 = str(self.widget.value())
                    if v != v1:
                        self.logger.debug('%s %s != %s', self.attribute.full_name, v, v1)
                        return False
                else:
                    self.logger.debug('Unknown %s value %s', self.attribute.full_name, v)
                    return False
                return True
            except KeyboardInterrupt:
                raise
            except:
                self.logger.debug('%s Exception in compare' % self.attribute.full_name, exc_info=True)
                return False
