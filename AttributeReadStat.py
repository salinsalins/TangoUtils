# coding: utf-8
import sys
import numpy as np
import matplotlib.pyplot as plt
# Вместо PyQt5 используем PySide6
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matplotlib inside PyQt5 QMainWindow")
        self.resize(800, 600)

        # 1. Create the main central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # 2. Create the Matplotlib Figure and Canvas
        self.figure = plt.figure() # Or use: self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        
        # 3. (Optional) Create the Matplotlib Navigation Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # 4. Create a UI element (e.g., a button to trigger plot updates)
        self.button = QPushButton("Generate Random Plot")
        self.button.clicked.connect(self.plot_data)

        # 5. Add all widgets to the layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)

        # Initial plot
        self.plot_data()

    def plot_data(self):
        # Clear the old plot before drawing a new one
        self.figure.clear()

        # Create an axis and plot data
        ax = self.figure.add_subplot(111)
        
        x = np.linspace(0, 10, 100)
        y = np.sin(x) + np.random.normal(0, 0.1, 100)
        
        ax.plot(x, y, label="Sin Waves with Noise", color="darkcyan")
        ax.set_title("Dynamic Data Visualization")
        ax.set_xlabel("X Axis")
        ax.set_ylabel("Y Axis")
        ax.legend()
        ax.grid(True)

        # CRITICAL: Redraw the canvas to apply changes
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


import time
import tango
"""
Created on Oct 15, 2026

@author: sanin
"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5 import uic
from PyQt5.QtCore import QTimer

from TangoWidgets.TangoWidget import TangoWidget
from TangoWidgets.TangoLED import TangoLED
from TangoWidgets.TangoLabel import TangoLabel
from TangoWidgets.TangoAbstractSpinBox import TangoAbstractSpinBox
from TangoWidgets.TangoPushButton import TangoPushButton
from TangoWidgets.TangoAttribute import TangoAttribute
from TangoWidgets.Utils import *

from config_logger import config_logger

APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1.0'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
UI_FILE = APPLICATION_NAME_SHORT + '.ui'

# Globals
TIMER_PERIOD = 500  # ms


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        # Initialization of the superclass
        super(MainWindow, self).__init__(parent)
        # logging config
        self.logger = config_logger(level=logging.DEBUG)
        # members definition
        self.n = 0
        self.elapsed = 0.0
        # Load the UI
        uic.loadUi(UI_FILE, self)
        # main window parameters
        self.resize(QSize(480, 640))                 # size
        self.move(QPoint(50, 50))                    # position
        self.setWindowTitle(APPLICATION_NAME)        # title
        self.setWindowIcon(QtGui.QIcon('icon.png'))  # icon

        print(APPLICATION_NAME + ' version ' + APPLICATION_VERSION + ' started')

        restore_settings(self, file_name=CONFIG_FILE)

        # read attributes TangoWidgets list
        self.rdwdgts = (
            # lauda
            TangoLED(self.config.get('pump', 'binp/nbi/lauda/6230_7'), self.pushButton_34),  # Pump On
            TangoLED(self.config.get('valve_state', 'binp/nbi/lauda/6230_0'), self.pushButton_31),  # Valve
            TangoLabel(self.config.get('return', 'binp/nbi/lauda/1012'), self.label_23),       # Return
        )
        # writable attributes TangoWidgets list
        self.wtwdgts = (
            # lauda
            TangoAbstractSpinBox(self.config.get('setpoint', 'binp/nbi/lauda/6200'), self.spinBox_4, False),  # SetPoint
            TangoPushButton(self.config.get('valve', 'binp/nbi/lauda/6210_3'), self.pushButton_4, False),  # Valve
            TangoPushButton(self.config.get('run', 'binp/nbi/lauda/6210_1'), self.pushButton_3, False),  # Run
            TangoPushButton(self.config.get('enable', 'binp/nbi/lauda/6210_0'), self.pushButton_6, False),  # Enable
            TangoPushButton(self.config.get('reset', 'binp/nbi/lauda/6210_2'), self.pushButton_9, False),  # Reset
        )
        #
        TangoWidget.RECONNECT_TIMEOUT = 5.0
        # Connect signals with slots
        self.pushButton_3.clicked.connect(self.lauda_pump_on_callback)
        self.spinBox_4.valueChanged.connect(self.setpoint_valueChanged)
        # lauda device
        try:
            self.lauda = self.pushButton_3.tango_widget.attribute.device_proxy
        except:
            self.lauda = None
        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(TIMER_PERIOD)

    def setpoint_valueChanged(self):
        self.lauda.write_attribute(self.config.get('remote', '1100'), self.spinBox_4.value())

    def lauda_pump_on_callback(self, value):
        if value:
            # reset
            self.pushButton_9.tango_widget.pressed()
            self.pushButton_9.tango_widget.released()
            # enable
            self.pushButton_6.setChecked(True)
            self.pushButton_6.tango_widget.clicked()

    def onQuit(self) :
        # Save global settings
        save_settings(self, file_name=CONFIG_FILE)
        self.timer.stop()
        
    def timer_handler(self):
        t0 = time.time()
        if len(self.rdwdgts) <= 0 and len(self.wtwdgts) <= 0:
            return
        self.elapsed = 0.0
        count = 0
        while time.time() - t0 < TIMER_PERIOD/2000.0:
            if self.n < len(self.rdwdgts) and self.rdwdgts[self.n].widget.isVisible():
                self.rdwdgts[self.n].update()
            if self.n < len(self.wtwdgts) and self.wtwdgts[self.n].widget.isVisible():
                self.wtwdgts[self.n].update(decorate_only=True)
            self.n += 1
            if self.n >= max(len(self.rdwdgts), len(self.wtwdgts)):
                self.n = 0
            count += 1
            if count == max(len(self.rdwdgts), len(self.wtwdgts)):
                self.elapsed = time.time() - self.elapsed
                return

if __name__ == "__main__":
    # test tango attribute read speed
    device_name = "sys/tg_test/1"
    attr_name = "double_scalar"

    dp = tango.DeviceProxy(device_name)

    # timing benchmarks
    print('Timing benchmarks')

    from matplotlib import pyplot as plt
    import numpy as np

    N = 5000
    y = np.zeros(N)
    z = []
    n = 0
    t = 0.0
    tmin = 1e60
    tmax = -1.0
    error_count = 0

    for i in range(N):
        t0 = time.perf_counter()
        result = dp.read_attribute(attr_name)
        dt = (time.perf_counter() - t0) * 1000.0
        v = result.value
        y[i] = dt
        z.append(v)
        t += dt
        n += 1
        tmin = min(tmin, dt)
        tmax = max(tmax, dt)

    if error_count > 0:
        print('\n Total errors: %s' % error_count)
    else:
        print('\n No errors!')

    print(f'\rRead: {attr_name} Timing: tmin: {tmin} tmax: {tmax} avg: {t/n} ms')

    # plot data
    #x = np.arange(N)
    #fig, ax = plt.subplots()
    #ax.plot(x, y)
    #ax.set(xlabel='N', ylabel='time (ms)',
    #       title='Read timings')
    #ax.grid()
    ## fig.savefig("test.png")
    #plt.show()

    # the histogram of the data
    num_bins = 100
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(y, num_bins, density=True)
    ax.set_xlabel('time (ms)')
    ax.set_ylabel('Probability density')
    ax.set_title(f'Histogram of Read Timing for {attr_name}')
    # ax.set_title(r'Histogram of Read timing: $\mu=100$, $\sigma=15$')
    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    # Create the GUI application
    app = QApplication(sys.argv)
    # Instantiate the main window
    dmw = MainWindow()
    app.aboutToQuit.connect(dmw.onQuit)
    # Show it
    dmw.show()
    # Start the Qt main loop execution, exiting from this script
    # with the same return code of Qt application
    sys.exit(app.exec_())

