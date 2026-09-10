from TangoWidgets.TangoLED import TangoLED


class RF_on_LED(TangoLED):

    def decorate(self):
        self.set_widget_value()

    def set_widget_value(self, value=None):
        if not self.attribute.is_valid() or self.attribute.value() < 0.5:
            self.widget.setEnabled(False)
        else:
            self.widget.setEnabled(True)
        return self.widget.isEnabled()
