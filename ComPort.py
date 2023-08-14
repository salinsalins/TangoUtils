import logging
import sys

from serial import SerialException

if '../TangoUtils' not in sys.path: sys.path.append('../TangoUtils')

import inspect
import time

import serial
import serial.tools.list_ports
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
                if isinstance(p.device, EmptyComPort):
                    # _v = p.open_counter
                    p.create_port()
                    time.sleep(0.05)
                    # p.open_counter = _v
                p.open_counter += 1
                for i in range(10):
                    time.sleep(0.05)
                    # p.logger.debug(f'{p.port} Ready: {p.ready}')
                    if p.ready:
                        break
                if p.ready:
                    p.logger.debug(f'{p.port} Using existing port')
                else:
                    p.logger.info(f'{p.port} Existing port is not ready')
                return
            # create new device
            self.port = port
            self.logger = kwargs.pop('logger', config_logger())
            self.emulated = kwargs.pop('emulated', None)
            self.suspend_delay = kwargs.pop('suspend_delay', 5.0)
            self.args = args
            self.kwargs = kwargs
            self.lock = RLock()
            self.open_counter = 0
            self.current_addr = -1  # current address for RS485 devices
            self.used_addr = []     # used addresses list for RS485 devices
            self.suspend_to = 0.0
            self.device = None
            # create new port and add it to list
            self.create_port()
            self.open_counter = 1
            ComPort._ports[self.port] = self
            if self.ready:
                self.logger.debug(f'{self.port} has been initialized')
            else:
                self.logger.info(f'{self.port} New port is not ready')

    def __del__(self):
        # self.open_counter = 1
        self.close()
        # ComPort._ports.pop(self.port, None)

    def create_port(self):
        with self.lock:
            # self.open_counter = 1
            self.suspend_to = 0.0
            try:
                # create port device
                if self.port.startswith('FAKE') or self.port.startswith('EMULATED'):
                    if self.emulated is None:
                        self.logger.info(f'{self.port} Emulated port class is not defined')
                        self.device = EmptyComPort()
                    self.device = self.emulated(self.port, *self.args, **self.kwargs)
                elif (self.port.startswith('COM')
                      or self.port.startswith('tty')
                      or self.port.startswith('/dev')
                      or self.port.startswith('cua')):
                    if 'timeout' not in self.kwargs:
                        self.kwargs['timeout'] = 0.0
                    if 'write_timeout' not in self.kwargs:
                        self.kwargs['write_timeout'] = 0.0
                    ports = serial.tools.list_ports.comports()
                    self.device = None
                    for p in ports:
                        if p.device == self.port:
                            self.device = serial.Serial(self.port, *self.args, **self.kwargs)
                            break
                    if self.device is None:
                        self.logger.info('%s port does not exist', self.port)
                        self.device = EmptyComPort()
                else:
                    self.kwargs['logger'] = self.logger
                    self.device = MoxaTCPComPort(self.port, *self.args, **self.kwargs)
            except KeyboardInterrupt:
                raise
            except:
                log_exception(self.logger, f'{self.port} Error creating port, using EmptyComPort')
                self.device = EmptyComPort()
            if not self.device.isOpen():
                self.device.open()
            if not self.device.isOpen():
                self.suspend()

    def close(self):
        try:
            with self.lock:
                # if not self.device.isOpen():
                #     self.open_counter = 1
                self.open_counter -= 1
                if self.open_counter <= 0:
                    self.open_counter = 0
                    self.device.close()
                    # ComPort._ports.pop(self.port)
                    if self.device.isOpen():
                        self.logger.debug(f'{self.port} was not closed')
                        return False
                    self.logger.debug(f'{self.port} has been closed')
                else:
                    self.logger.debug(f'{self.port} Skipped port close request')
                return True
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger, f'{self.port} Port close exception')
            return False

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
            log_exception(self.logger, f'{self.port} Read exception')
            self.suspend()

    def write(self, *args, **kwargs):
        try:
            with self.lock:
                if self.ready:
                    return self.device.write(*args, **kwargs)
                else:
                    return 0
        except SerialException:
            log_exception(self.logger, level=logging.INFO, no_info=True)
            self.suspend()
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger, f'{self.port} Write exception')
            self.suspend()

    def reset_input_buffer(self):
        with self.lock:
            if self.ready:
                try:
                    self.device.reset_input_buffer()
                    return True
                except KeyboardInterrupt:
                    raise
                except:
                    self.suspend()
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
                    self.suspend()
                    return False
            else:
                return True

    @property
    def ready(self):
        with self.lock:
            if time.time() < self.suspend_to:
                # self.logger.debug(f'{self.port} operations suspended')
                return False
            if self.suspend_to <= 0.0:
                return True
            # suspension expires
            self.suspend_to = 0.0
            # if self.device.isOpen():
            #     return True
            with ComPort._lock:
                try:
                    if isinstance(self.device, EmptyComPort):
                        self.create_port()
                    else:
                        self.device.close()
                        self.device.open()
                    if self.device.isOpen():
                        self.logger.debug(f'{self.port} reopened')
                        return True
                    self.suspend()
                    self.logger.debug(f'{self.port} reopen failed')
                    return False
                except KeyboardInterrupt:
                    raise
                except:
                    log_exception(self.logger, f'{self.port} ready exception')
                    self.suspend()
                    return False

    def suspend(self):
        if self.suspend_to > 0.0:
            return
        self.suspend_to = time.time() + self.suspend_delay
        self.logger.debug(f'{self.port} Suspended for {self.suspend_delay} s')

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

    @property
    def ready(self):
        return False
