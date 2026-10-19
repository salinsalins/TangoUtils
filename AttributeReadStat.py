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
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QLabel, QLineEdit, QMainWindow, QSpinBox, QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PySide6.QtCore import QCoreApplication, QTimer, QObject, QThread, Signal, Slot
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from shiboken6 import Shiboken 

from config_logger import config_logger

import tango

from log_exception import log_exception

APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1.2'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
PLOT_TIMER_PERIOD = 2000  # ms
TANGO_HOST = 'localhost:10000'
ATTRIBUTE_NAME = "sys/tg_test/1/double_scalar"
TIMER_PERIOD = 150 #[ms]
DUTY_LOAD = 0.5
ARRAY_SIZE = 5000
BINS = 100

# 1. Создаем класс-рабочий (Worker), наследуясь от QObject
class TaskWorker(QObject):
    # Сигналы для связи с главным потоком (UI)
    progress_changed = Signal(int)    # Передает процент выполнения (0-100)
    task_finished = Signal(str)       # Передает результат по окончании
    # Сигнал для отправки массива (списка) обратно в UI
    # array_ready = Signal(list)

    def __init__(self, data: list, attribute = ATTRIBUTE_NAME):
        super().__init__()
        self._is_running = True
        self.y = data
        self.n = len(data)
        self.i = 0
        self.full = False
        self.atribute_name = attribute.split('/')[-1]
        self.device_name = attribute.replace('/' + self.atribute_name, '')
        print(self.device_name, self.atribute_name)
        try:
            self.dp = tango.DeviceProxy(self.device_name)
        except KeyboardInterrupt:
            raise
        except:
            # print('ERROR creating device proxy')
            log_exception('ERROR creating device proxy')
        # self.tmin = 1e100
        # self.tmax = -1.0
        self.error_count = 0
        self.timer_period = TIMER_PERIOD
        self.load = DUTY_LOAD
        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(self.timer_period)

    @Slot(int)
    def config_changed(self, period):
        """Вызывается в произвольный момент по сигналу из UI"""
        print('Reseived', period)

    @Slot()
    def run_task(self):
        print("Фоновое вычисление началось...")
        return

    def stop(self):
        self._is_running = False

    def timer_handler(self):
        start_time = time.perf_counter()
        while True:
            t0 = time.perf_counter()
            try:
                result = self.dp.read_attribute(self.atribute_name)
            except KeyboardInterrupt:
                raise
            except:
                dt = (time.perf_counter() - t0) * 1000.0 
                print('ERROR reading after', dt)
                log_exception('ERROR attribute reading')
                self.error_count += 1
            dt = (time.perf_counter() - t0) * 1000.0 
            self.y[self.i] = dt
            self.i += 1
            if dt > self.timer_period / 5:
                print('Long reading time', dt)
            if self.i >= self.n:
                # Отправляем сигнал в UI с текущим прогрессом
                # self.progress_changed.emit(self.i)
                self.i = 0
                self.full = True
                print('Array iz full')
            if (time.perf_counter() - start_time) > (self.load * self.timer_period / 1000.):
                print(self.i)
                return 

class MainWindow(QMainWindow):
    # Сигнал-запрос к воркеру
    change_config = Signal(int)

    def __init__(self):
        super().__init__()
        self.array_size = ARRAY_SIZE
        self.y_data = [-1.0] * self.array_size
        self.prev_y = self.y_data.copy()
        self.attribute_name = ATTRIBUTE_NAME

        self.logger = config_logger(level=logging.DEBUG)

        self.setWindowTitle("Matplotlib inside PyQt5 QMainWindow")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.button = QPushButton("Generate Random Plot")
        self.button.clicked.connect(self.plot_data)
        
        self.attribute = QLineEdit(self.attribute_name)
        self.attribute.returnPressed.connect(self.attribute_submit)    
        
        self.period = QSpinBox()
        self.period.setRange(1, TIMER_PERIOD * 10)
        self.period.setValue(TIMER_PERIOD)
        self.period.setSingleStep(TIMER_PERIOD // 10)
        self.period.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.period.editingFinished.connect(self.period_submit)
        # self.period.valueChanged.connect(self.period_submit)

        self.array = QSpinBox()
        self.array.setRange(10, ARRAY_SIZE * 10)
        self.array.setValue(ARRAY_SIZE)
        self.array.setSingleStep(ARRAY_SIZE // 10)
        self.array.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        # self.period.editingFinished.connect(self.period_submit)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("Array Size:"))
        layout2.addWidget(self.array)
        layout2.addWidget(QLabel("Timer Period [ms]:"))
        layout2.addWidget(self.period)
        layout2.addWidget(QLabel("Attribute Name:"))
        layout2.addWidget(self.attribute)
        layout.addLayout(layout2)

        # Initial plot
        self.plot_data(self.y_data)

        # Defile and start timer callback task
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_handler)
        # start timer
        self.timer.start(PLOT_TIMER_PERIOD)

        # Шаг А: Создаем поток и рабочего
        self.my_thread = QThread()
        self.worker = TaskWorker(self.y_data, self.attribute_name)

        # Шаг Б: Переносим рабочего в фоновый поток (Важнейший шаг!)
        self.worker.moveToThread(self.my_thread)

        # Шаг В: Связываем сигналы и слоты
        self.my_thread.started.connect(self.worker.run_task) # При старте потока запускаем задачу
        self.change_config.connect(self.worker.config_changed)
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

    
    def attribute_submit(self):
        # Получаем текст из поля
        user_text = self.attribute.text()
        print(f"Пользователь ввел: {user_text}")
    
    def period_submit(self):
        # Получаем текст из поля
        number = self.period.value()
        print(f"Пользователь ввел: {number}")
        self.change_config.emit(number)
    
    def filter_outliers_iqr(self, data, low=25, high=75, range=1.5):
        data = np.array(data)
        data = data[data > 0.0] 
        if len(data) <= 0:
            return [0.0]
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

        num_bins = BINS
        self.figure.suptitle(f'Histogram of Read Timing for {self.attribute_name}')

        # Create an axis and plot data
        # ax = self.figure.add_subplot(111)
        ax = self.figure.add_subplot(121)
        plot_data = self.filter_outliers_iqr(self.y_data)
        # n, bins, patches = ax.hist(self.prev_y, num_bins)
        n, bins, patches = ax.hist(plot_data, num_bins)
        # self.prev_y = plot_data
        ax.set_xlabel('Read time (ms)')
        ax.set_ylabel('Number of Counts')
        ax.set_title('Lower 75%')
        # ax.legend(labels=['Previous', 'Curernt'])
        ax.grid(True)

        x_min, x_max = ax.get_xlim()
        plot_data2 = np.array(self.y_data)
        plot_data2 = plot_data2[plot_data2 > (x_max * 2.1)]
        if len(plot_data2) > 1:
            ax2 = self.figure.add_subplot(122)
            n, bins, patches = ax2.hist(plot_data2, num_bins)
            ax2.set_xlabel('Read time (ms)')
            ax2.set_title(f'Longer Reads')
            ax2.grid(True)

        # CRITICAL: Redraw the canvas to apply changes
        self.canvas.draw()
        
    # @Slot(int)
    # def update_progress(self, value):
    #     self.progress_bar.setValue(value)

    # @Slot(str)
    # def on_task_finished(self, result_message):
    #     self.label.setText(result_message)
    #     self.btn_start.setEnabled(True)

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
    if 'TANGO_HOST' not in os.environ:
        os.environ['TANGO_HOST'] = TANGO_HOST
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
