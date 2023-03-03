import inspect

import serial
from threading import RLock, Lock

from Moxa import MoxaTCPComPort
from config_logger import config_logger
from log_exception import log_exception


class ComPort:
    _ports = {}
    _lock = Lock()

    def __new__(cls, port: str, *args, **kwargs):
        port = port.strip()
        if port.upper().startswith('COM'):
            port = port.upper()
        with ComPort._lock:
            if port in ComPort._ports:
                return ComPort._ports[port]
        return super().__new__(cls)

    def __init__(self, port: str, *args, **kwargs):
        port = port.strip()
        if port.upper().startswith('COM'):
            port = port.upper()
        # use existing device
        with ComPort._lock:
            if port in ComPort._ports:
                p = ComPort._ports[port]
                p.logger.debug(f'Using existing COM port {port}')
                if not p.ready:
                    p.device.close()
                    p.device.open()
                p.open_counter += 1
                if not p.ready:
                    p.logger.error(f'Existing COM port {port} is not ready')
                return
            # create new port and add it to list
            self.lock = RLock()
            self.logger = kwargs.pop('logger', config_logger())
            self.emulated = kwargs.pop('emulated', None)
            self.open_counter = 0
            self.port = port
            self.args = args
            self.kwargs = kwargs
            # address for RS485 devices
            self.current_addr = -1
            self.device = None
            self.create_port()
            ComPort._ports[self.port] = self
            if self.ready:
                self.logger.debug(f'{self.port} has been initialized')
            else:
                self.logger.warning(f'{self.port} is not ready')

    def __del__(self):
        self.close()

    def create_port(self):
        with self.lock:
            try:
                # create port device
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
                if not self.device.isOpen():
                    self.device.open()
                self.open_counter = 1
            except KeyboardInterrupt:
                raise
            except:
                log_exception(self.logger)
                self.device = EmptyComPort()

    def close(self):
        with ComPort._lock:
            if self.port in ComPort._ports:
                with self.lock:
                    self.open_counter -= 1
                    if self.open_counter <= 0:
                        result = self.device.close()
                        # ComPort._ports.pop(self.port)
                        self.logger.debug(f'COM port {self.port} closed {result}')
                        return result
                    else:
                        self.logger.debug(f'Skipped COM port {self.port} close request')
                        return True

    def read(self, *args, **kwargs):
        try:
            with self.lock:
                if self.ready:
                    return self.device.read(*args, **kwargs)
                else:
                    return b''
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger)
            # self.close()
            # self.device = EmptyComPort()

    def write(self, *args, **kwargs):
        try:
            with self.lock:
                if self.ready:
                    return self.device.write(*args, **kwargs)
                else:
                    return 0
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger)

    def reset_input_buffer(self):
        with self.lock:
            if self.ready:
                try:
                    self.device.reset_input_buffer()
                    return True
                except KeyboardInterrupt:
                    raise
                except:
                    return False
            else:
                return True

    def reset_output_buffer(self):
        with self.lock:
            if self.ready:
                try:
                    self.device.reset_output_buffer()
                    return True
                except KeyboardInterrupt:
                    raise
                except:
                    return False
            else:
                return True

    @property
    def ready(self):
        return self.device.isOpen()

    @property
    def in_waiting(self):
        with self.lock:
            if self.ready:
                try:
                    return self.device.in_waiting
                except KeyboardInterrupt:
                    raise
                except:
                    return 0
            else:
                return 0


class EmptyComPort:
    """Always not ready, reads nothing, writes 0 bytes"""
    @property
    def in_waiting(self):
        return 0

    def open(self):
        return True

    def isOpen(self):
        return False

    def close(self):
        return True

    def reset_output_buffer(self):
        return True

    def reset_input_buffer(self):
        return True

    def write(self, *args, **kwargs):
        return 0

    def read(self, *args, **kwargs):
        return b''
