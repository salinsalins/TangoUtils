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

APPLICATION_NAME = os.path.basename(__file__).replace('.py', '')
APPLICATION_NAME_SHORT = APPLICATION_NAME
APPLICATION_VERSION = '1.2'
CONFIG_FILE = APPLICATION_NAME_SHORT + '.json'
TIMER_PERIOD = 2000  # ms
TANGO_HOST = 'localhost:10000'
DEVICE_NAME = "sys/tg_test/1"
ATTRIBUTE_NAME = "double_scalar"
TIMER_PERIOD = 50 #[ms]
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

    def __init__(self, data: list, device = DEVICE_NAME, attribute = ATTRIBUTE_NAME):
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
        self.full = False
        self.i = 0
        self.loops = 10
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
        # for i in range(self.loops):
            t0 = time.perf_counter()
            result = self.dp.read_attribute(self.atribute)
            dt = (time.perf_counter() - t0) * 1000.0 
            self.y[self.i] = dt
            self.i += 1
            if self.i >= self.n:
                # Отправляем сигнал в UI с текущим прогрессом
                # self.progress_changed.emit(self.i)
                self.i = 0
                # if not self.full: print('Array is full')
                self.full = True
            self.tmin = min(self.tmin, dt)
            self.tmax = max(self.tmax, dt)
            if (time.perf_counter() - start_time) > (self.load * self.timer_period / 1000.):
                return 

class MainWindow(QMainWindow):
    # Сигнал-запрос к воркеру
    change_config = Signal(int)

    def __init__(self):
        super().__init__()
        self.y_data = [0] * ARRAY_SIZE
        self.prev_y = self.y_data.copy()
        self.device = DEVICE_NAME
        self.attribute = ATTRIBUTE_NAME

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
        
        self.device_name = QLineEdit("sys/tg_test/1")
        self.device_name.returnPressed.connect(self.device_submit)    
        
        self.attribute_name = QLineEdit("double_scalar")
        self.attribute_name.returnPressed.connect(self.attribute_submit)    
        
        self.period = QSpinBox()
        self.period.setRange(1, TIMER_PERIOD * 10)
        self.period.setValue(TIMER_PERIOD)
        self.period.setSingleStep(TIMER_PERIOD // 10)
        self.period.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.period.editingFinished.connect(self.period_submit)
        # self.period.valueChanged.connect(self.period_submit)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("Period [ms]"))
        layout2.addWidget(self.period)
        layout2.addWidget(QLabel("Device Name:"))
        layout2.addWidget(self.device_name)
        layout2.addWidget(QLabel("Attribute Name:"))
        layout2.addWidget(self.attribute_name)
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

    def device_submit(self):
        # Получаем текст из поля
        user_text = self.device_name.text()
        print(f"Пользователь ввел: {user_text}")
    
    def attribute_submit(self):
        # Получаем текст из поля
        user_text = self.device_name.text()
        print(f"Пользователь ввел: {user_text}")
    
    def period_submit(self):
        # Получаем текст из поля
        number = self.period.value()
        print(f"Пользователь ввел: {number}")
        self.change_config.emit(number)
    
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
        num_bins = BINS
        plot_data = self.filter_outliers_iqr(self.y_data)
        n, bins, patches = ax.hist(self.prev_y, num_bins, density=True)
        n, bins, patches = ax.hist(plot_data, num_bins, density=True)
        self.prev_y = plot_data
        
        ax.set_xlabel('Read time (ms)')
        ax.set_ylabel('Probability density')
        ax.set_title(f'Histogram of Read Timing for {self.device}/{self.attribute}')
        ax.legend(labels=['Previous', 'Curernt'])
        ax.grid(True)

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
