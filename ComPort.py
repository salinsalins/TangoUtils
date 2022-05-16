import inspect

import serial
from threading import RLock, Lock

from Moxa import MoxaTCPComPort
from config_logger import config_logger


def get_caller():
    return inspect.stack()[1].frame.f_locals['self']


class ComPort:
    _ports = {}
    dev_lock = Lock()

    def __new__(cls, port: str, *args, **kwargs):
        port = port.strip()
        with ComPort.dev_lock:
            if port in cls._ports:
                return cls._ports[port]
        return super().__new__(cls)

    def __init__(self, port: str, *args, **kwargs):
        port = port.strip()
        # use existed device
        with ComPort.dev_lock:
            if port in ComPort._ports:
                ComPort._ports[port].logger.debug('Using existent COM port')
                ComPort._ports[port].open_counter += 1
                return
        self.lock = RLock()
        with self.lock:
            self.logger = kwargs.pop('logger', config_logger())
            self.open_counter = 1
            emulated = kwargs.pop('emulated', None)
            self.port = port
            self.args = args
            self.kwargs = kwargs
            # address for RS485 devices
            self.current_addr = -1
            # initialize real device
            if self.port.startswith('FAKE') or self.port.startswith('EMULATED'):
                if emulated is None:
                    self._device = None
                    self.logger.error('Emulated port class not defined %s', self.port)
                else:
                    self._device = emulated(self.port, *self.args, **self.kwargs)
            elif (self.port.upper().startswith('COM')
                  or self.port.startswith('tty')
                  or self.port.startswith('/dev')
                  or self.port.startswith('cua')):
                self.kwargs['timeout'] = 0.0
                self.kwargs['write_timeout'] = 0.0
                self._device = serial.Serial(self.port, *self.args, **self.kwargs)
            else:
                self._device = MoxaTCPComPort(self.port, *self.args, **self.kwargs)
            with ComPort.dev_lock:
                ComPort._ports[self.port] = self
            self.logger.debug('Port %s has been initialized', self.port)

    def read(self, *args, **kwargs):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                return ComPort._ports[self.port]._device.read(*args, **kwargs)
            else:
                return b''

    def write(self, *args, **kwargs):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                return ComPort._ports[self.port]._device.write(*args, **kwargs)
            else:
                return 0

    def reset_input_buffer(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                        ComPort._ports[self.port]._device.reset_input_buffer()
                        return True
                except:
                    return False
            else:
                return True

    def reset_output_buffer(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                        ComPort._ports[self.port]._device.reset_output_buffer()
                        return True
                except:
                    return False
            else:
                return True

    def close(self):
        # self.logger.debug('Enter')
        with ComPort._ports[self.port].lock:
            ComPort._ports[self.port].open_counter -= 1
            if ComPort._ports[self.port].open_counter <= 0:
                result = ComPort._ports[self.port]._device.close()
                ComPort._ports.pop(self.port)
                self.logger.debug('COM port closed %s', result)
                return result
            else:
                return True

    @property
    def ready(self):
        return ComPort._ports[self.port]._device.isOpen()

    @property
    def in_waiting(self):
        with ComPort._ports[self.port].lock:
            if ComPort._ports[self.port].ready:
                try:
                        return ComPort._ports[self.port]._device.in_waiting
                except:
                    return False
            else:
                return True


