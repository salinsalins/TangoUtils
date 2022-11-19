import json
import logging
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QPoint
from PyQt5.QtWidgets import QPlainTextEdit, QLineEdit, QComboBox, QWidget

from log_exception import log_exception


def get_widget_state(widget: QWidget, config: dict, widget_name=None):
    try:
        if widget_name is None:
            widget_name = widget.objectName()
        if isinstance(widget, QLineEdit):
            config[widget_name] = str(widget.text())
        elif isinstance(widget, QComboBox):
            config[widget_name] = {'items': [str(widget.itemText(k)) for k in range(widget.count())],
                            'index': widget.currentIndex()}
        elif isinstance(widget, QtWidgets.QAbstractButton):
            config[widget_name] = widget.isChecked()
        elif isinstance(widget, QPlainTextEdit) or isinstance(widget, QtWidgets.QTextEdit):
            config[widget_name] = str(widget.toPlainText())
        elif isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            config[widget_name] = widget.value()
    except:
        return


def set_widget_state(widget: QWidget, config: dict, widget_name=None):
    try:
        if widget_name is None:
            widget_name = widget.objectName()
        if widget_name not in config:
            return
        if isinstance(widget, QLineEdit):
            widget.setText(config[widget_name])
        elif isinstance(widget, QComboBox):
            widget.setUpdatesEnabled(False)
            bs = widget.blockSignals(True)
            widget.clear()
            widget.addItems(config[widget_name]['items'])
            widget.blockSignals(bs)
            widget.setUpdatesEnabled(True)
            widget.setCurrentIndex(config[widget_name]['index'])
            # Force index change event in the case of index=0
            if config[widget_name]['index'] == 0:
                widget.currentIndexChanged.emit(0)
        elif isinstance(widget, QtWidgets.QAbstractButton):
            widget.setChecked(config[widget_name])
        elif isinstance(widget, QPlainTextEdit) or isinstance(widget, QtWidgets.QTextEdit):
            widget.setPlainText(config[widget_name])
        elif isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(config[widget_name])
    except:
        return


def restore_settings(obj, file_name='config.json', widgets=()):
    try:
        if not hasattr(obj, 'config'):
            obj.config = {}
        try:
            # open and read config file
            with open(file_name, 'r') as configfile:
                s = configfile.read()
            # interpret file contents by json
            obj.config = json.loads(s)
        except:
            log_exception(obj, 'Can not read config from %s' % file_name)
        # restore log level
        if 'log_level' in obj.config:
            v = obj.config['log_level']
            obj.logger.setLevel(v)
        # restore window size and position (can be changed by user during operation)
        if 'main_window' in obj.config:
            obj.resize(QSize(obj.config['main_window']['size'][0], obj.config['main_window']['size'][1]))
            obj.move(QPoint(obj.config['main_window']['position'][0], obj.config['main_window']['position'][1]))
        # restore widgets state
        for w in widgets:
            set_widget_state(w, obj.config)
        # OK message
        obj.logger.info('Configuration restored from %s', file_name)
    except:
        log_exception(obj, 'Can not restore settings')
    return obj.config


def save_settings(obj, file_name='config.json', widgets=()):
    try:
        # save current window size and position
        p = obj.pos()
        s = obj.size()
        obj.config['main_window'] = {'size': (s.width(), s.height()), 'position': (p.x(), p.y())}
        #
        obj.config['log_level'] = obj.logger.level
        # get state of widgets
        for w in widgets:
            get_widget_state(w, obj.config)
        # write to file
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(obj.config, indent=4))
        # OK message
        obj.logger.info('Configuration saved to %s', file_name)
        return True
    except:
        log_exception(obj, 'Can not save settings')
        return False


# Logging to the text panel
class TextEditHandler(logging.Handler):
    def __init__(self, widget=None):
        if not hasattr(widget, 'appendPlainText'):
            raise ValueError('Incompatible widget for Log Handler')
        logging.Handler.__init__(self)
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget is not None:
            self.widget.appendPlainText(log_entry)


class WidgetLogHandler(logging.Handler):
    def __init__(self, widget, limit=-1, formatter=None):
        if not hasattr(widget, 'setText'):
            raise ValueError('Incompatible widget for Log Handler')
        logging.Handler.__init__(self)
        self.widget = widget
        self.limit = limit
        self.widget.time = time.time()
        if formatter is not None:
            pass

    def emit(self, record):
        log_entry = self.format(record)
        if self.limit > 0:
            log_entry = log_entry[:self.limit]
        if self.widget is not None:
            self.widget.setText(log_entry)
            self.widget.time = time.time() + 10.0
