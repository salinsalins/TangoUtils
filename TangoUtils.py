import json
import logging
import sys
import time

# tango dependent definitions
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, QPoint
from PyQt5.QtWidgets import QPlainTextEdit, QLineEdit, QComboBox

try:
    import tango
    from tango.server import Device

    # Handler for logging to the tango log system
    class TangoLogHandler(logging.Handler):
        def __init__(self, device: tango.server.Device, level=logging.DEBUG, formatter=None):
            super().__init__(level)
            self.device = device
            if formatter is None:
                try:
                    self.setFormatter(config_logger.log_formatter)
                except:
                    pass
            else:
                self.setFormatter(formatter)

        def emit(self, record):
            level = self.level
            if level >= logging.CRITICAL:
                log_entry = self.format(record)
                Device.fatal_stream(log_entry)
            elif level >= logging.WARNING:
                log_entry = self.format(record)
                Device.error_stream(log_entry)
            elif level >= logging.INFO:
                log_entry = self.format(record)
                Device.info_stream(log_entry)
            elif level >= logging.DEBUG:
                log_entry = self.format(record)
                Device.debug_stream(log_entry)

except:
    pass


# Logging to the text panel
class TextEditHandler(logging.Handler):
    def __init__(self, widget=None):
        logging.Handler.__init__(self)
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget is not None:
            self.widget.appendPlainText(log_entry)


# log format string with process id and thread id
LOG_FORMAT_STRING = '%(asctime)s,%(msecs)3d %(levelname)-7s [%(process)d:%(thread)d] %(filename)s ' \
                    '%(funcName)s(%(lineno)s) %(message)s'
# log format string without process id and thread id
LOG_FORMAT_STRING_SHORT = '%(asctime)s,%(msecs)3d %(levelname)-7s %(filename)s %(funcName)s(%(lineno)s) %(message)s'


def config_logger(name=None, level: int = logging.DEBUG, format_string=None, force_add_handler=False):
    if name is None:
        if hasattr(config_logger, 'logger'):
            return config_logger.logger
        else:
            name = __name__
    # create an configure logger
    logger = logging.getLogger(name)
    config_logger.logger = logger
    logger.propagate = False
    logger.setLevel(level)
    # do not add extra console handlers if logger already has one. Add any manually if needed.
    if logger.hasHandlers() and not force_add_handler:
        return logger
    if format_string is None:
        format_string = LOG_FORMAT_STRING
    log_formatter = logging.Formatter(format_string, datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    config_logger.console_handler = console_handler
    config_logger.log_formatter = log_formatter
    return logger


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if te - ts > 0.01:
            print('%r %2.2f sec' % (method.__name__, te - ts))
        return result

    return timed


def log_exception(logger, message=None, *args, level=logging.ERROR):
    try:
        if not isinstance(logger, logging.Logger):
            logger = logger.logger
    except:
        return
    if not isinstance(logger, logging.Logger):
        return
    ex_type, ex_value, traceback = sys.exc_info()
    tail = ' %s' % ex_value
    if message is None:
        message = 'Exception '
    message += tail
    logger.log(level, message % args)
    logger.debug('Exception: ', exc_info=True)


def split_attribute_name(name):
    # [protocol: //][host: port /]device_name[ / attribute][->property][  # dbase=xx]
    split = name.split('/')
    a_n = split[-1]
    m = -1 - len(a_n)
    d_n = name[:m]
    return d_n, a_n


def convert_polling_status(status_string_array, name: str):
    result = {'period': 0, 'depth': 0}
    s1 = 'Polled attribute type = '
    s2 = 'Polling period (mS) = '
    s3 = 'Polling ring buffer depth = '
    # s4 = 'Time needed for the last attribute reading (mS) = 100'
    # s4 = 'Data not updated since 54 mS'
    # s6 = 'Delta between last records (in mS) = 98, 100, 101, 98'
    n1 = s1 + name
    for s in status_string_array:
        if s.startswith(n1):
            for ss in s.split('\n'):
                try:
                    if ss.startswith(s2):
                        result['period'] = int(ss.replace(s2, ''))
                    elif ss.startswith(s3):
                        result['depth'] = int(ss.replace(s3, ''))
                except:
                    pass
    return result


class Configuration:
    def __init__(self, file_name=None, default=None):
        if default is None:
            default = {}
        self.data = default
        self.file_name = None
        self.read(file_name)

    def get(self, name, default=None):
        try:
            result = self.data.get(name, default)
            if default is not None:
                result = type(default)(result)
        except:
            result = default
        self.data[name] = result
        return result

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        return

    def __contains__(self, key):
        return key in self.data

    def read(self, file_name, append=True):
        try:
            self.file_name = file_name
            # Read config from file
            with open(file_name, 'r') as configfile:
                data = json.loads(configfile.read())
            # import data
            if append:
                for d in data:
                    self.data[d] = data[d]
            else:
                self.data = data
            return True
        except:
            return False

    def write(self, file_name=None):
        if file_name is None:
            file_name = self.file_name
        if file_name is None:
            return False
        with open(file_name, 'w') as configfile:
            configfile.write(json.dumps(self.data, indent=4))
        return True


def get_widget_state(obj, config, name=None):
    try:
        if name is None:
            name = obj.objectName()
        if isinstance(obj, QLineEdit):
            config[name] = str(obj.text())
        elif isinstance(obj, QComboBox):
            config[name] = {'items': [str(obj.itemText(k)) for k in range(obj.count())],
                            'index': obj.currentIndex()}
        elif isinstance(obj, QtWidgets.QAbstractButton):
            config[name] = obj.isChecked()
        elif isinstance(obj, QPlainTextEdit) or isinstance(obj, QtWidgets.QTextEdit):
            config[name] = str(obj.toPlainText())
        elif isinstance(obj, QtWidgets.QSpinBox) or isinstance(obj, QtWidgets.QDoubleSpinBox):
            config[name] = obj.value()
    except:
        return


def set_widget_state(obj, config, name=None):
    try:
        if name is None:
            name = obj.objectName()
        if name not in config:
            return
        if isinstance(obj, QLineEdit):
            obj.setText(config[name])
        elif isinstance(obj, QComboBox):
            obj.setUpdatesEnabled(False)
            bs = obj.blockSignals(True)
            obj.clear()
            obj.addItems(config[name]['items'])
            obj.blockSignals(bs)
            obj.setUpdatesEnabled(True)
            obj.setCurrentIndex(config[name]['index'])
            # Force index change event in the case of index=0
            if config[name]['index'] == 0:
                obj.currentIndexChanged.emit(0)
        elif isinstance(obj, QtWidgets.QAbstractButton):
            obj.setChecked(config[name])
        elif isinstance(obj, QPlainTextEdit) or isinstance(obj, QtWidgets.QTextEdit):
            obj.setPlainText(config[name])
        elif isinstance(obj, QtWidgets.QSpinBox) or isinstance(obj, QtWidgets.QDoubleSpinBox):
            obj.setValue(config[name])
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
                log_exception(obj.logger)
            # restore log level
            if 'log_level' in obj.config:
                v = obj.config['log_level']
                obj.logger.setLevel(v)
            # restore window size and position (can be changed by user during operation)
            if 'main_window' in obj.config:
                obj.resize(QSize(obj.config['main_window']['size'][0], obj.config['main_window']['size'][1]))
                obj.move(QPoint(obj.config['main_window']['position'][0], obj.config['main_window']['position'][1]))
            # --- removed - should be configured in the UI file
            # if 'icon_file' in obj.config:
            #     obj.setWindowIcon(QtGui.QIcon(obj.config['icon_file']))  # icon
            # if 'application_name' in obj.config:
            #     obj.setWindowTitle(obj.config['application_name'])       # title
            # restore widgets state
            for w in widgets:
                set_widget_state(w, obj.config)
            # OK message
            obj.logger.info('Configuration restored from %s', file_name)
    except:
        log_exception(obj.logger)
    return obj.config


def save_settings(obj, file_name='config.json', widgets=()):
    try:
        # save current window size and position
        p = obj.pos()
        s = obj.size()
        obj.config['main_window'] = {'size': (s.width(), s.height()), 'position': (p.x(), p.y())}
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
        log_exception(obj.logger)
        return False



