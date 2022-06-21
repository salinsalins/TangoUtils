import socket

from config_logger import config_logger
from log_exception import log_exception


class MoxaTCPComPort:
    def __init__(self, host, port=4001, **kwargs):
        if ':' in host:
            n = host.find(':')
            self.host = host[:n].strip()
            try:
                self._port = int(host[n + 1:].strip())
            except:
                self._port = port
        else:
            self.host = host
            self._port = port
        # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.connect((self.host, self._port))
        self.logger = kwargs.pop('logger', config_logger())
        self.socket = socket.create_connection((self.host, self._port), 5.0)  # 5 s timeout
        self.socket.settimeout(0.01)

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
        return True

    def reset_output_buffer(self):
        return True

    @property
    def in_waiting(self):
        return 1
