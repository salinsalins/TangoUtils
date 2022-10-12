import inspect

import serial
from threading import RLock, Lock

from Moxa import MoxaTCPComPort
from config_logger import config_logger
from log_exception import log_exception


def get_caller():
    return inspect.stack()[1].frame.f_locals['self']


class ComPort:
    _ports = {}
    _lock = Lock()

    def __new__(cls, port: str, *args, **kwargs):
        port = port.strip()
        if port.upper().startswith('COM'):
            port = port.upper()
        with ComPort._lock:
            if port in cls._ports:
                return cls._ports[port]
        return super().__new__(cls)

    def __init__(self, port: str, *args, **kwargs):
        port = port.strip()
        if port.upper().startswith('COM'):
            port = port.upper()
        # use existing device
        with ComPort._lock:
            if port in ComPort._ports:
                ComPort._ports[port].logger.debug(f'Using existing COM port {port}')
                if not ComPort._ports[port].ready:
                    ComPort._ports[port].device.close()
                    ComPort._ports[port].open()
                ComPort._ports[port].open_counter += 1
                if not ComPort._ports[port].ready:
                    ComPort._ports[port].logger.error('Existing COM port is not ready')
                return
        # create new port
        self.lock = RLock()
        self.logger = kwargs.pop('logger', config_logger())
        self.emulated = kwargs.pop('emulated', None)
        self.open_counter = 1
        self.port = port
        self.args = args
        self.kwargs = kwargs
        # address for RS485 devices
        self.current_addr = -1
        self.device = None
        self.open()
        with ComPort._lock:
            ComPort._ports[self.port] = self
        self.logger.debug(f'{self.port} has been initialized')
        if not ComPort._ports[self.port].ready:
            ComPort._ports[port].logger.warning(f'{self.port} is not ready')

    def open(self):
        with self.lock:
            try:
                # initialize real device
                if self.port.startswith('FAKE') or self.port.startswith('EMULATED'):
                    if self.emulated is None:
                        self.device = EmptyComPort()
                        self.logger.error('Emulated port class not defined for %s', self.port)
                    else:
                        self.device = self.emulated(self.port, *self.args, **self.kwargs)
                elif (self.port.upper().startswith('COM')
                      or self.port.startswith('tty')
                      or self.port.startswith('/dev')
                      or self.port.startswith('cua')):
                    self.kwargs['timeout'] = 0.0
                    self.kwargs['write_timeout'] = 0.0
                    self.device = serial.Serial(self.port, *self.args, **self.kwargs)
                else:
                    self.kwargs['logger'] = self.logger
                    self.device = MoxaTCPComPort(self.port, *self.args, **self.kwargs)
            except:
                log_exception(self.logger)
                self.device = EmptyComPort()

    def read(self, *args, **kwargs):
        try:
            with ComPort._ports[self.port].lock:
                if ComPort._ports[self.port].ready:
                    return ComPort._ports[self.port].device.read(*args, **kwargs)
                else:
                    return b''
        except:
            log_exception(self.logger)
            self.device = EmptyComPort()

    def write(self, *args, **kwargs):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                return ComPort._ports[self.port].device.write(*args, **kwargs)
            else:
                return 0

    def reset_input_buffer(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                    ComPort._ports[self.port].device.reset_input_buffer()
                    return True
                except:
                    return False
            else:
                return True

    def reset_output_buffer(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                    ComPort._ports[self.port].device.reset_output_buffer()
                    return True
                except:
                    return False
            else:
                return True

    def close(self):
        with ComPort._ports[self.port].lock:
            ComPort._ports[self.port].open_counter -= 1
            if ComPort._ports[self.port].open_counter <= 0:
                result = ComPort._ports[self.port].device.close()
                # ComPort._ports.pop(self.port)
                self.logger.debug('COM port closed %s', result)
                return result
            else:
                self.logger.debug('Skipped COM port close request')
                return True

    @property
    def ready(self):
        return ComPort._ports[self.port].device.isOpen()

    @property
    def in_waiting(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                    return ComPort._ports[self.port].device.in_waiting
                except:
                    return False
            else:
                return False


class EmptyComPort():
    @property
    def in_waiting(self):
        return False

    def open(self):
        pass

    def isOpen(self):
        return False

    def close(self):
        return True

    def reset_output_buffer(self):
        pass

    def reset_input_buffer(self):
        pass

    def write(self, *args, **kwargs):
        return 0

    def read(self, *args, **kwargs):
        return b''
