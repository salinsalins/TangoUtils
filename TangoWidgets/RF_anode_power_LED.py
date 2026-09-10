import tango
from PyQt5.QtWidgets import QPushButton
from TangoWidgets.TangoAttribute import TangoAttribute
from TangoWidgets.TangoLED import TangoLED


class RF_anode_power_LED(TangoLED):
    def __init__(self, name, widget: QPushButton):
        self.st = TangoAttribute('binp/nbi/rfpowercontrol/state')
        self.ap = TangoAttribute('binp/nbi/rfpowercontrol/anode_power')
        super().__init__(name, widget)

    def read(self, force=False, **kwargs):
        self.st.read(force)
        self.ap.read(force)
        return self.attribute.read(force)

    def decorate(self):
        self.set_widget_value()

    def set_widget_value(self, value=None):
        try:
            if not (self.st.value() != tango.DevState.RUNNING or self.ap.value() > 50.0):
                self.widget.setDisabled(False)
                self.widget.setChecked(False)
            else:
                self.widget.setDisabled(False)
                self.widget.setChecked(True)
        except:
            self.widget.setDisabled(False)
            self.widget.setChecked(False)
        return self.widget.isChecked()
