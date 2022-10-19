import socket

from config_logger import config_logger
from log_exception import log_exception


class MoxaTCPComPort:
    DEFAULT_TIMEOUT = 0.01
    CREATE_TIMEOUT = 5.0

    def __init__(self, host: str, port: int = 4001, **kwargs):
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
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.connect((self.host, self._port))
        self.logger = kwargs.pop('logger', config_logger())
        create_timeout = kwargs.get('create_timeout', MoxaTCPComPort.CREATE_TIMEOUT)
        self.socket = socket.create_connection((self.host, self.port), create_timeout)
        timeout = kwargs.get('timeout', MoxaTCPComPort.DEFAULT_TIMEOUT)
        self.socket.settimeout(timeout)

    def close(self):
        self.socket.close()
        return True

    def write(self, cmd):
        try:
            return self.socket.send(cmd)
        except:
            log_exception(self.logger)
            return -1

    def read(self, n=1):
        try:
            return self.socket.recv(n)
        except:
            return b''

    def isOpen(self):
        return True

    def reset_input_buffer(self):
        b = b'0'
        b1 = b''
        while len(b) > 0:
            b = self.read(1000)
            b1 += b
            if b1 != b'':
                self.logger.error(f"Input buffer is not empty: {b1}")
        if b1 != b'':
            self.logger.error(f"Input buffer is not empty: {b1}")
        return True

    def reset_output_buffer(self):
        return True

    @property
    def in_waiting(self):
        return 1
