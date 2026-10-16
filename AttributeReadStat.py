# coding: utf-8
"""
Created on Oct 15, 2026

@author: sanin
"""

import sys
import os
import logging
import time
import numpy as np
import matplotlib.pyplot as plt
# Вместо PyQt5 используем PySide6
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PySide6.QtCore import QTimer, QObject, QThread, Signal, Slot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from shiboken6 import Shiboken 

from config_logger import config_logger

import tango

APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1.0'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
TIMER_PERIOD = 2000  # ms

# 1. Создаем класс-рабочий (Worker), наследуясь от QObject
class TaskWorker(QObject):
    # Сигналы для связи с главным потоком (UI)
    progress_changed = Signal(int)    # Передает процент выполнения (0-100)
    task_finished = Signal(str)       # Передает результат по окончании
    # Сигнал для отправки массива (списка) обратно в UI
    # array_ready = Signal(list)

    def __init__(self, data: list, device = "sys/tg_test/1", attribute = "double_scalar"):
        super().__init__()
        self._is_running = True
        self.y = data
        self.device = device
        self.atribute = attribute
        self.dp = tango.DeviceProxy(device)
        self.n = len(data)
        self.tmin = 1e60
        self.tmax = -1.0
        self.error_count = 0

    # @Slot()
    # def send_current_array(self):
    #     """Вызывается в произвольный момент по сигналу из UI"""
    #     print('sending data')
    #     #self.array_ready.emit(self.y)

    @Slot()
    def run_task(self):
        print("Фоновое вычисление началось...")
        i = 0
        full = False
        while True:
            t0 = time.perf_counter()
            result = self.dp.read_attribute(self.atribute)
            dt = (time.perf_counter() - t0) * 1000.0 
            # x = i * 2.0 * np.pi / self.n
            # dt = np.sin(x) + 0.05 * np.random.random()
            # v = result.value
            self.y[i] = dt
            i += 1
            if i >= self.n:
                # Отправляем сигнал в UI с текущим прогрессом
                self.progress_changed.emit(i)
                i = 0
                if not full: print('array is full')
                full = True
            self.tmin = min(self.tmin, dt)
            self.tmax = max(self.tmax, dt)
            if not self._is_running:
                break

        if self._is_running:
            self.task_finished.emit("Вычисления успешно завершены!")
        else:
            self.task_finished.emit("Задача была прервана пользователем.")

    def stop(self):
        self._is_running = False

class MainWindow(QMainWindow):
    # Сигнал-запрос к воркеру
    # request_array = Signal()

    def __init__(self):
        super().__init__()
        self.y_data = [0] * 5000
        self.device = "sys/tg_test/1"
        self.attribute = "double_scalar"

        self.logger = config_logger(level=logging.DEBUG)

        self.setWindowTitle("Matplotlib inside PyQt5 QMainWindow")
        self.resize(800, 600)

        # 1. Create the main central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout2 = QHBoxLayout()
        layout2.addWidget(QPushButton("Button 1"))
        layout2.addWidget(QPushButton("Button 2"))

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
        layout.addLayout(layout2)

        # Initial plot
        self.plot_data(self.y_data)

        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(TIMER_PERIOD)

        # Шаг А: Создаем поток и рабочего
        self.my_thread = QThread()
        self.worker = TaskWorker(self.y_data, self.device, self.attribute)

        # Шаг Б: Переносим рабочего в фоновый поток (Важнейший шаг!)
        self.worker.moveToThread(self.my_thread)

        # Шаг В: Связываем сигналы и слоты
        self.my_thread.started.connect(self.worker.run_task) # При старте потока запускаем задачу
        #self.worker.progress_changed.connect(self.update_progress) # Ловим прогресс
        #self.worker.task_finished.connect(self.on_task_finished)   # Ловим финиш

        # Шаг Г: Правильное удаление объектов из памяти после завершения
        self.worker.task_finished.connect(self.my_thread.quit)
        self.worker.task_finished.connect(self.worker.deleteLater)
        self.my_thread.finished.connect(self.my_thread.deleteLater)

        # Связываем сигналы запроса и ответа
        # self.request_array.connect(self.worker.send_current_array)
        # self.worker.array_ready.connect(self.plot_data)
        
        # Шаг Д: Запускаем поток
        self.my_thread.start()

    def filter_outliers_iqr(self, data, low=25, high=75, range=1.5):
        data = np.array(data)
        
        # 1. Находим 25-й и 75-й процентили
        q25 = np.percentile(data, low)
        q75 = np.percentile(data, high)
        
        # 2. Вычисляем межквартильный размах (ширину основного ядра данных)
        iqr = q75 - q25
        
        # 3. Определяем границы (классический коэффициент — 1.5)
        lower_bound = q25 - (range * iqr)
        upper_bound = q75 + (range * iqr)
        
        # 4. Оставляем только те данные, которые попали в границы
        return data[(data >= lower_bound) & (data <= upper_bound)]

    def plot_data(self, data):
        # Clear the old plot before drawing a new one
        self.figure.clear()

        # Create an axis and plot data
        ax = self.figure.add_subplot(111)
        num_bins = 100
        plot_data = self.filter_outliers_iqr(self.y_data, low=0)
        n, bins, patches = ax.hist(plot_data, num_bins, density=True)
        
        # x = np.linspace(0, 10, 100)
        # y = np.sin(x) + np.random.normal(0, 0.1, 100)
        # x = np.linspace(0, 1, len(self.y_data))
        # y = self.y_data
        
        ax.set_xlabel('Read time (ms)')
        ax.set_ylabel('Probability density')
        ax.set_title(f'Histogram of Read Timing for {self.device}/{self.attribute}')
        # ax.plot(x, y, label="Sin Waves with Noise", color="darkcyan")
        # ax.set_title("Dynamic Data Visualization")
        # ax.set_xlabel("X Axis")
        # ax.set_ylabel("Y Axis")
        # ax.legend()
        ax.grid(True)

        # CRITICAL: Redraw the canvas to apply changes
        self.canvas.draw()
        
    @Slot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @Slot(str)
    def on_task_finished(self, result_message):
        self.label.setText(result_message)
        self.btn_start.setEnabled(True)

    def closeEvent(self, event):
        # 1. Проверяем, существуют ли атрибуты в Python
        if hasattr(self, 'worker') and hasattr(self, 'thread'):
            # 2. Проверяем, живы ли еще реальные C++ объекты внутри Qt
            if Shiboken.isValid(self.thread) and Shiboken.isValid(self.worker):
                # 3. Только если они живы И поток все еще работает, останавливаем его
                # if self.thread.isRunning():
                self.worker.stop()
                self.my_thread.quit()
                self.my_thread.wait()
        event.accept()
 
    def timer_handler(self):
        self.plot_data(self.y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())






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

