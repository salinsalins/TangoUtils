import socket
import time

from _socket import timeout
from serial import PortNotOpenError

from config_logger import config_logger
from log_exception import log_exception


class MoxaTCPComPort:
    DEFAULT_PORT = 4001
    DEFAULT_TIMEOUT = 0.01
    CREATE_TIMEOUT = 5.0

    def __init__(self, host: str, port: int = None, **kwargs):
        self.kwargs = kwargs
        self.logger = kwargs.get('logger', config_logger())
        kwargs['logger'] = self.logger
        if port is None:
            port = MoxaTCPComPort.DEFAULT_PORT
        if ':' in host:
            n = host.find(':')
            self.host = host[:n].strip()
            try:
                self.port = int(host[n + 1:].strip())
            except:
                self.port = int(port)
        else:
            self.host = host.strip()
            self.port = int(port)
        self.pre = f'MOXA {self.host}:{self.port}'
        self.socket = None
        self.error = False
        self.open()
        self.logger.debug(f'{self.pre} Initialized')

    def open(self):
        self.error = False
        try:
            create_timeout = self.kwargs.get('create_timeout', MoxaTCPComPort.CREATE_TIMEOUT)
            # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.socket.connect((self.host, self._port))
            self.socket = socket.create_connection((self.host, self.port), create_timeout)
            timeout = self.kwargs.get('timeout', MoxaTCPComPort.DEFAULT_TIMEOUT)
            self.socket.settimeout(timeout)
        except KeyboardInterrupt:
            raise
        except:
            log_exception(f'{self.pre} Socket open exception')
            self.socket = None
            self.error = True

    def close(self):
        if not self.isOpen():
            return True
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.socket = None
            self.error = False
            self.logger.debug(f'{self.pre} Socket closed')
            return True
        except KeyboardInterrupt:
            raise
        except:
            log_exception(f'{self.pre} Socket close exception')
            self.socket = None
            self.error = True
            return False

    def write(self, cmd):
        if not self.isOpen():
            raise PortNotOpenError()
        try:
            n = self.socket.send(cmd)
            if n == len(cmd):
                self.error = False
            else:
                self.error = True
            return n
        except KeyboardInterrupt:
            raise
        except:
            log_exception(self.logger, f'{self.pre} Write error')
            self.error = True
            raise
            # return -1

    def read(self, n=1):
        if not self.isOpen():
            raise PortNotOpenError()
        try:
            return self.socket.recv(n)
        except KeyboardInterrupt:
            raise
        except timeout:
            return b''
        except:
            log_exception(self.logger, f'{self.pre} Read error')
            self.error = True
            raise
            # return b''

    def isOpen(self):
        return self.socket is not None

    def reset_input_buffer(self):
        b = self.read(1000)
        b1 = b'' + b
        t0 = time.time()
        while len(b) > 0:
            b = self.read(1000)
            b1 += b
            if time.time() - t0 > 5.0:
                self.logger.debug(f"{self.pre} Timeout resetting input buffer")
                # self.error = True
                return False
        # if b1 != b'':
        #     self.logger.debug(f"{self.pre} Input buffer was not empty {b1}")
        return True

    def reset_output_buffer(self):
        return True

    @property
    def in_waiting(self):
        return 1

    @property
    def ready(self):
        if self.isOpen() and not self.error:
            return True
        if self.isOpen():
            pass
