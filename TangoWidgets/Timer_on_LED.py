from PyQt5.QtWidgets import QPushButton

from TangoWidgets.TangoAttribute import TangoAttribute
from TangoUtils import split_attribute_name
from TangoWidgets.TangoLED import TangoLED
from log_exception import log_exception


class Timer_on_LED(TangoLED):
    def __init__(self, name, widget: QPushButton, elapsed='binp/nbi/adc0/Elapsed'):
        timer, _ = split_attribute_name(name)
        self.value = False
        self.use_state = False
        self.elapsed = None
        # self.elapsed = TangoAttribute(elapsed)
        self.enable = []
        self.stop = []
        self.sate = []
        super().__init__(name, widget)
        al = self.attribute.device_proxy.get_attribute_list()
        al = list(al)
        al.sort()
        self.enable = [TangoAttribute(timer + '/' + a) for a in al if 'channel_enable' in a]
        self.stop = [TangoAttribute(timer + '/' + a) for a in al if 'pulse_stop' in a]
        self.state = [TangoAttribute(timer + '/' + a) for a in al if 'channel_state' in a]
        self.use_state = len(self.state) > 0
        if not self.use_state:
            self.elapsed = TangoAttribute(elapsed)

    def read(self, force=False, **kwargs):
        self.value = self.check_state()
        return self.value

    def set_widget_value(self, value=None):
        if value is None:
            value = self.value
        else:
            self.value = value
        self.widget.setEnabled(bool(value))
        return self.widget.isEnabled()

    def decorate(self):
        self.set_widget_value()

    def check_state(self):
        timer_device = self.attribute.device_proxy
        if timer_device is None:
            return False
        if self.use_state:
            avs = []
            try:
                avs = timer_device.read_attributes(self.state)
            except KeyboardInterrupt:
                raise
            except:
                pass
            state = False
            for av in avs:
                state = bool(av.value) or state
            # self.logger.debug('%s %s', state)
            return state
        else:
            max_time = 0.0
            if self.elapsed is None:
                return False
            try:
                for i in range(len(self.enable)):
                    self.enable[i].read_sync()
                    if self.enable[i].value():
                        self.stop[i].read_sync()
                        max_time = max(max_time, self.stop[i].value())
                # during pulse
                # if self.timer_on_led.value:   # pulse is on
                # self.logger.debug('%s %s', self.elapsed.value(), max_time)
                self.elapsed.read()
                if self.elapsed.value() < (max_time / 1000.0):
                    return True
                else:  # pulse is off
                    return False
            except KeyboardInterrupt:
                raise
            except:
                log_exception('********')
                return False

    def update(self, decorate_only=False, **kwargs) -> None:
        self.set_widget_value(self.check_state())
