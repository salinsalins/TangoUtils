import logging

import tango
from tango.server import Device


# Handler for logging to the tango log system
class TangoLogHandler(logging.Handler):
    def __init__(self, device: tango.server.Device, level=logging.DEBUG, formatter=None):
        global config_logger
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
            self.device.fatal_stream(log_entry)
        elif level >= logging.WARNING:
            log_entry = self.format(record)
            self.device.error_stream(log_entry)
        elif level >= logging.INFO:
            log_entry = self.format(record)
            self.device.info_stream(log_entry)
        elif level >= logging.DEBUG:
            log_entry = self.format(record)
            self.device.debug_stream(log_entry)
