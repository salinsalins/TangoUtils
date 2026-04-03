from tango import DevFailed

from TangoWidgets.TangoAttribute import TangoAttribute
from TangoWidgets.TangoLED import TangoLED
from log_exception import log_exception


class Lauda_small_ready_LED(TangoLED):
    def __init__(self, name, widget, run='run', pressure='pressure', pressure_limit=1.5):
        self.value = False
        self.pressure_limit = pressure_limit
        if not name.endswith('/'):
            name += '/'
        if '/' in run:
            run_name = run
        else:
            run_name = name + run
        if '/' in pressure:
            pressure_name = pressure
        else:
            pressure_name = name + pressure
        self.run = TangoAttribute(run_name)  # output valve
        self.pressure = TangoAttribute(pressure_name)  # pump motor
        super().__init__(pressure_name, widget)
        # self.motor = self.attribute  # Lauda pump motor

    def read(self, force=None, sync=None, **kwargs):
        self.value = False
        try:
            self.value = bool(self.run.read(force) and (self.pressure.read(force) > self.pressure_limit))
        except KeyboardInterrupt:
            raise
        # except DevFailed:
        #     pass
        except:
            log_exception()
        # self.logger.debug("value=%s", self.value)
        return self.value

    def decorate(self):
        self.set_widget_value()

    def set_widget_value(self, value=None):
        try:
            if self.run.is_valid() and self.pressure.is_valid() and self.value:
                self.widget.setDisabled(False)
                self.widget.setChecked(True)
            else:
                self.widget.setDisabled(False)
                self.widget.setChecked(False)
        except KeyboardInterrupt:
            raise
        except:
            self.widget.setChecked(False)
        return self.widget.isChecked()
    
    def update(self, *args, **kwargs):
        # if self.value:
        #     self.logger.debug('Update %s', self.value)
        # else:
        #     self.logger.debug('Update %s', self.value)
        super().update(*args, **kwargs)
