import socket


class MoxaTCPComPort:
    def __init__(self, host, port=4001, **kwargs):
        if ':' in host:
            n = host.find(':')
            self.host = host[:n].strip()
            try:
                self.port = int(host[n + 1:].strip())
            except:
                self.port = port
        else:
            self.host = host
            self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.connect((self.host, self.port))
        self.socket.create_connection((self.host, self.port), 5.0) # 5 s timeout
        self.socket.settimeout(0.0)

    def close(self):
        self.socket.close()
        return True

    def write(self, cmd):
        return self.socket.send(cmd)

    def read(self, n=1):
        return self.socket.recv(n)

    def isOpen(self):
        return True

    def reset_input_buffer(self):
        return True

    def reset_output_buffer(self):
        return True

    @property
    def in_waiting(self):
        return 1



