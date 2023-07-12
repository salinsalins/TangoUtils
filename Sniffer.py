# coding: utf-8
import sys
from datetime import datetime
import serial

QT_API = 'pyside6'

import qtpy
from qtpy import uic
from qtpy.QtCore import QTimer, QSize, QPoint
from qtpy.QtWidgets import QApplication, QMainWindow

from QtUtils import restore_settings, save_settings

sys.path.append('')
from config_logger import config_logger
from log_exception import log_exception

ORGANIZATION_NAME = 'BINP'
APPLICATION_NAME = 'Sniffer'
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '0.1'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Globals
TIMER_PERIOD = 50  # ms


def hex_from_str(v):
    h = ''
    for i in v:
        h += hex(i) + ' '
    return h


def str_from_hex(v):
    vs = v.split(' ')
    h = ''
    for i in vs:
        v = i.strip()
        if v != '':
            h += chr(int(v, 16))
    return h


def dec_from_str(v):
    h = ''
    for i in v:
        h += str(i) + ' '
    return h


def str_from_dec(v):
    vs = v.split(' ')
    h = ''
    for i in vs:
        v = i.strip()
        if v != '':
            h += chr(int(v, 10))
    return h


class MainWindow(QMainWindow):
    def __init__(self):
        # Initialization of the superclass
        super().__init__()
        # logging config
        self.logger = config_logger()
        # members definition
        self.com1 = None
        self.cts1 = None
        self.rts1 = None
        self.com2 = None
        self.cts2 = None
        self.rts2 = None
        self.connected = False
        self.not_conn_show = False
        # Load the Qt UI
        uic.loadUi(UI_FILE, self)
        # Default main window parameters
        self.resize(QSize(480, 640))                 # size
        self.move(QPoint(50, 50))                    # position
        self.setWindowTitle(APPLICATION_NAME)        # title
        # Welcome message
        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')
        #
        restore_settings(self, file_name=CONFIG_FILE, widgets=(self.lineEdit, self.lineEdit_2,
                                                               self.lineEdit_3, self.lineEdit_4))
        self.connect_ports()
        if self.com1 is not None:
            self.cts1 = self.com1.cts
            self.rts1 = self.com1.rts
        if self.com2 is not None:
            self.cts2 = self.com2.cts
            self.rts2 = self.com2.rts
        # Connect signals with slots
        self.pushButton.clicked.connect(self.clear_button_clicked)
        self.pushButton_2.clicked.connect(self.connect_ports)
        self.last_index = self.comboBox.currentIndex()
        self.comboBox.currentIndexChanged.connect(self.combobox_index_changed)
        # Defile callback task and start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        self.timer.start(TIMER_PERIOD)
        self.logger.info('\n---------- Config Finished -----------\n')

    def connect_ports(self):
        try:
            self.com1.close()
            self.com2.close()
        except:
            pass
        port = ''
        try:
            port = str(self.lineEdit.text())
            param = str(self.lineEdit_2.text())
            params = param.split(' ')
            kwargs = {}
            for p in params:
                p1 = p.strip().split('=')
                kwargs[p1[0].strip()] = p1[1].strip()
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 0
            self.com1 = serial.Serial(port, **kwargs)
            # self.com1.ctsrts = True
            #
            self.logger.debug(f'Port {port} connected')
            port = str(self.lineEdit_3.text())
            param = str(self.lineEdit_4.text())
            params = param.split(' ')
            kwargs = {}
            for p in params:
                p1 = p.strip().split('=')
                kwargs[p1[0].strip()] = p1[1].strip()
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 0
            self.com2 = serial.Serial(port, **kwargs)
            # self.com2.ctsrts = True
            self.connected = True
            self.logger.debug(f'Port {port} connected')
            self.plainTextEdit_2.appendPlainText(f'{dts()} Ports connected successfully')
            self.logger.debug(f'Ports connected successfully')
        except:
            log_exception(self.logger, 'Port %s connection error' % port)
            self.plainTextEdit_2.appendPlainText(f'{dts()} Port %s connection error' % port)

    def clear_button_clicked(self):
        self.plainTextEdit_2.setPlainText('')

    def on_quit(self) :
        # Save global settings
        save_settings(self, file_name=CONFIG_FILE, widgets=(self.lineEdit, self.lineEdit_2,
                                                            self.lineEdit_3, self.lineEdit_4))

    def read_port(self, port):
        result = b''
        r = port.read(1)
        while r:
            result += r
            r = port.read(1)
        return result

    def timer_handler(self):
        if not self.connected:
            if not self.not_conn_show:
                self.plainTextEdit_2.appendPlainText(f'{dts()} Not connected, waiting')
                self.not_conn_show = True
            return
        self.not_conn_show = False
        v = self.com1.cts
        if self.cts1 != v:
            self.logger.debug('CTS1 %s -> %s', self.cts1, v)
            self.cts1 = v
            # self.com2.rts = v
        v = self.com1.rts
        if self.rts1 != v:
            self.logger.debug('RTS1 %s -> %s',self.rts1, v)
            self.rts1 = v
        result = self.read_port(self.com1)
        dt = dts()
        if len(result) > 0:
            m = self.com2.write(result)
            self.logger.debug('Port1 received %s bytes: %s %s', len(result), result, hex_from_str(result))
            if self.pushButton_3.isChecked():
                n = self.comboBox.currentIndex()
                r = ''
                if n == 0:
                    r = str(result)
                elif n == 1:
                    r = hex_from_str(result)
                elif n == 2:
                    r = dec_from_str(result)
                self.plainTextEdit_2.appendPlainText('%s 1>2 %s' % (dt, r))
        # COM2
        v = self.com2.cts
        if self.cts2 != v:
            self.logger.debug('CTS2 %s -> %s', self.cts2, v)
            self.cts2 = v
            # self.com1.rts = v
        v = self.com2.rts
        if self.rts2 != v:
            self.logger.debug('RTS2 %s -> %s',self.rts2, v)
            self.rts2 = v
        result = self.read_port(self.com2)
        dt = dts()
        if len(result) > 0:
            m = self.com1.write(result)
            self.logger.debug('Port2 received %s bytes: %s %s', len(result), result, hex_from_str(result))
            if self.pushButton_3.isChecked():
                n = self.comboBox.currentIndex()
                r = ''
                if n == 0:
                    r = str(result)
                elif n == 1:
                    r = hex_from_str(result)
                elif n == 2:
                    r = dec_from_str(result)
                self.plainTextEdit_2.appendPlainText('%s 2>1 %s' % (dt, r))

    def combobox_index_changed(self, n):
        try:
            n = self.comboBox.currentIndex()
            txt = self.plainTextEdit_2.toPlainText()
            self.plainTextEdit_2.setPlainText('')
            lines = txt.split('\n')
            for line in lines:
                i1 = line.find('1>2')
                i2 = line.find('2>1')
                if i1 > 0 or i2 > 0:
                    head = line[:i1+1+i2+4]
                    tail = line[i1+1+i2+4:]
                    result = ''
                    if self.last_index == 0:
                        result = tail[2:-1].encode()
                    elif self.last_index == 1:
                        result = str_from_hex(tail).encode()
                    elif self.last_index == 2:
                        result = str_from_dec(tail).encode()
                    if n == 0:
                        r = str(result)
                    elif n == 1:
                        r = hex_from_str(result)
                    elif n == 2:
                        r = dec_from_str(result)
                    else:
                        r = ''
                    self.plainTextEdit_2.appendPlainText('%s%s' % (head, r))
                else:
                    self.plainTextEdit_2.appendPlainText(line)
        except:
            log_exception(self)
        self.last_index = n


def dts():
    #return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]


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
    status = app.exec_()
    sys.exit(status)
