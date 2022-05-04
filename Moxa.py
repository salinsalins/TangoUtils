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
        self.socket.connect((self.host, self.port))

    def close(self):
        self.socket.close()
        return True

    def write(self, cmd):
        self.socket.send(cmd)

    def read(self, n):
        return self.socket.recv(n)

    def isOpen(self):
        return True

    def reset_input_buffer(self):
        return True


