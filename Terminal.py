# coding: utf-8
import sys;

from serial import SEVENBITS, PARITY_EVEN, EIGHTBITS

from ComPort import ComPort

sys.path.append('')
from datetime import datetime
import os.path
import time

import serial
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from PyQt5.QtCore import QTimer, QSize, QPoint
import PyQt5.QtGui as QtGui

from QtUtils import restore_settings, save_settings
from config_logger import config_logger
from log_exception import log_exception

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'Terminal'
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '0.1'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Globals
TIMER_PERIOD = 300  # ms


class MainWindow(QMainWindow):
    def __init__(self):
        # Initialization of the superclass
        super().__init__()
        # logging config
        self.logger = config_logger()
        # members definition
        self.port = None
        self.baud = 9600
        self.connected = False
        # Load the Qt UI
        uic.loadUi(UI_FILE, self)
        # Default main window parameters
        self.resize(QSize(480, 640))  # size
        self.move(QPoint(50, 50))  # position
        self.setWindowTitle(APPLICATION_NAME)  # title
        # Welcome message
        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')
        #
        restore_settings(self, file_name=CONFIG_FILE,
                         widgets=(self.lineEdit, self.comboBox, self.lineEdit_3, self.lineEdit_5, self.lineEdit_6))
        v = self.lineEdit_3.text()
        ve = v.encode()
        h = ''
        for i in ve:
            h += hex(i)[2:] + ' '
        self.lineEdit_4.setText(h)
        #
        # self.port = str(self.lineEdit.text())
        # self.baud = int(self.lineEdit_2.text())
        # self.com = serial.Serial(self.port, baudrate=self.baud, timeout=0)
        self.connect_port()
        # Connect signals with slots
        self.lineEdit_3.editingFinished.connect(self.send_changed)
        self.lineEdit_4.editingFinished.connect(self.hex_changed)
        self.pushButton.clicked.connect(self.button_clicked)
        self.pushButton_2.clicked.connect(self.connect_port)
        self.pushButton_3.clicked.connect(self.disconnect_port)
        # Defile callback task and start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        self.timer.start(TIMER_PERIOD)
        self.logger.info('\n---------- Config Finished -----------\n')

    def connect_port(self):
        bauds = ['4800', '9600', '19200', '38400', '57600', '115200']
        try:
            self.com.close()
        except:
            pass
        try:
            self.port = str(self.lineEdit.text())
            i = self.comboBox.currentIndex()
            if i < len(bauds):
                self.baud = int(bauds[self.comboBox.currentIndex()])
            else:
                self.baud = self.comboBox.itemText(i)
            param = str(self.lineEdit_6.text())
            params = param.split(' ')
            kwargs = {}
            for p in params:
                p1 = p.strip().split('=')
                if len(p1) == 2:
                    key = p1[0].strip()
                    val = p1[1].strip()
                    if '"' in val or "'" in val:
                        val = val.replace('"', '').replace("'",'')
                    else:
                        val = int(val)
                    kwargs[key] = val
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 0
            # self.com = ComPort(self.port, baudrate=self.baud, timeout=0)
            self.com = ComPort(self.port, baudrate=int(self.baud), **kwargs)
            self.connected = self.com.ready
            if self.com.ready:
                self.plainTextEdit_2.appendPlainText('%s Port %s connected successfully' % (dts(), self.port))
            else:
                self.plainTextEdit_2.setPlainText('Port %s connection error' % self.port)
        except:
            log_exception(self.logger)
            self.plainTextEdit_2.setPlainText('Port %s connection error' % self.port)

    def disconnect_port(self):
        try:
            self.connected = False
            self.com.close()
            self.plainTextEdit_2.appendPlainText('%s Port %s has been disconnected' % (dts(), self.port))
        except:
            log_exception(self.logger)
            self.plainTextEdit_2.setPlainText('Port %s disconnection error' % self.port)

    def hex_from_str(self, v):
        h = ''
        for i in v:
            h += hex(i)[2:] + ' '
        return h

    def str_from_hex(self, v):
        vs = v.split(' ')
        h = ''
        for i in vs:
            v = i.strip()
            if v != '':
                h += chr(int(v, 16))
        return h

    def send_changed(self):
        v = self.lineEdit_3.text()
        ve = v.encode()
        h = ''
        for i in ve:
            h += hex(i)[2:] + ' '
        self.lineEdit_4.setText(h)
        # stat = self.com.write(ve)
        # self.logger.debug('%s of %s bytes written', stat, len(ve))

    def button_clicked(self):
        if not self.connected:
            return
        v = self.lineEdit_3.text().encode()
        s = self.str_from_hex(self.lineEdit_5.text()).encode()
        t = v + s
        stat = self.com.write(t)
        dt = dts()
        if stat == len(t):
            msg = dt + ' %s bytes written: %s' % (stat, t)
            self.logger.debug(msg)
        else:
            msg = dt + ' %s of %s bytes written from %s' % (stat, len(t), t)
            self.logger.debug(msg)
        self.plainTextEdit_2.appendPlainText(msg)

    def hex_changed(self):
        v = self.lineEdit_4.text()
        vs = v.split(' ')
        h = ''
        for i in vs:
            v = i.strip()
            if v != '':
                h += chr(int(v, 16))
        self.lineEdit_3.setText(h)
        # stat = self.com.write(h.encode())
        # self.logger.debug('%s of %s bytes written', stat, len(h))

    def on_quit(self):
        self.com.close()
        # Save global settings
        save_settings(self, file_name=CONFIG_FILE,
                      widgets=(self.lineEdit, self.comboBox, self.lineEdit_3, self.lineEdit_5, self.lineEdit_6))

    def timer_handler(self):
        try:
            if not self.connected:
                # self.logger.debug('Port disconnected')
                # self.plainTextEdit_2.setPlainText('Port %s connection error' % self.port)
                return
            result = b''
            r = self.com.read(1)
            while r:
                result += r
                r = self.com.read(1)
            if len(result) > 0:
                self.logger.debug('received %s bytes: %s', len(result), str(result))
                dt = dts()
                self.plainTextEdit_2.appendPlainText('%s received %s bytes: %s' % (dt, len(result), result))
                self.plainTextEdit.appendPlainText('\n%s received %s bytes:' % (dt, len(result)))
                self.plainTextEdit.appendPlainText(str(result))
                h = ''
                for i in result:
                    h += hex(i) + ' '
                self.plainTextEdit.appendPlainText(h)
        except:
            log_exception(self.logger)


def dts():
    # return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return datetime.today().strftime('%H:%M:%S.%f')[:-3]


if __name__ == '__main__':
    # Create the GUI application
    app = QApplication(sys.argv)
    # Instantiate the main window
    dmw = MainWindow()
    app.aboutToQuit.connect(dmw.on_quit)
    # Show it
    dmw.show()
    # Start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(app.exec_())
