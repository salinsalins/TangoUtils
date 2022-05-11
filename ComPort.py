import serial
from threading import RLock, Lock

from Moxa import MoxaTCPComPort
from config_logger import config_logger


class ComPort:
    _devices = {}
    dev_lock = Lock()

    def __new__(cls, port, *args, **kwargs):
        with ComPort.dev_lock:
            if port in cls._devices:
                return cls._devices[port]
        return object.__new__(cls)

    def __init__(self, port: str, *args, emulated=None, **kwargs):
        port = port.strip()
        # use existed device
        with ComPort.dev_lock:
            if port in ComPort._devices:
                ComPort._devices[port].logger.debug('Using existent COM port')
                return
        self.lock = RLock()
        with self.lock:
            self.logger = kwargs.get('logger', config_logger())
            self.emulated = emulated
            self.port = port
            self.args = args
            self.kwargs = kwargs
            # address for RS485 devices
            self.current_addr = -1
            # initialize real device
            if self.port.startswith('FAKE') or self.port.startswith('EMULATED'):
                if self.emulated is None:
                    self._device = None
                    self.logger.error('Emulated port class not defined %s', self.port)
                else:
                    self._device = self.emulated(self.port, *self.args, **self.kwargs)
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
                ComPort._devices[self.port] = self
            self.logger.debug('Port %s has been initialized', self.port)

    def read(self, *args, **kwargs):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                return ComPort._devices[self.port]._device.read(*args, **kwargs)
            else:
                return b''

    def write(self, *args, **kwargs):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                return ComPort._devices[self.port]._device.write(*args, **kwargs)
            else:
                return 0

    def reset_input_buffer(self):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                try:
                        ComPort._devices[self.port]._device.reset_input_buffer()
                        return True
                except:
                    return False
            else:
                return True

    def reset_output_buffer(self):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                try:
                        ComPort._devices[self.port]._device.reset_output_buffer()
                        return True
                except:
                    return False
            else:
                return True

    def close(self):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                return ComPort._devices[self.port]._device.close()
            else:
                return True

    @property
    def ready(self):
        return ComPort._devices[self.port]._device.isOpen()

    @property
    def in_waiting(self):
        with ComPort._devices[self.port].lock:
            if ComPort._devices[self.port].ready:
                try:
                        return ComPort._devices[self.port]._device.in_waiting
                except:
                    return False
            else:
                return True


