import threading
from collections import UserList

class ThreadSafeList(UserList):
    def __init__(self, initlist=None):
        super().__init__(initlist)
        # Использование RLock защищает от дедлоков при взаимных вызовах методов
        self._lock = threading.RLock()

    # --- Методы чтения (переопределяем для защиты от изменения другими потоками) ---

    def __getitem__(self, i):
        with self._lock:
            return super().__getitem__(i)

    def __len__(self):
        with self._lock:
            return super().__len__()

    def __contains__(self, item):
        with self._lock:
            return super().__contains__(item)

    # --- Методы модификации (мутации) ---

    def append(self, item):
        with self._lock:
            super().append(item)

    def insert(self, i, item):
        with self._lock:
            super().insert(i, item)

    def pop(self, i=-1):
        with self._lock:
            return super().pop(i)

    def remove(self, item):
        with self._lock:
            super().remove(item)

    def clear(self):
        with self._lock:
            super().clear()

    def __setitem__(self, i, item):
        with self._lock:
            super().__setitem__(i, item)

    def __delitem__(self, i):
        with self._lock:
            super().__delitem__(i)

    # --- Потокобезопасные составные операции ---

    def pop_if_not_empty(self):
        """Атомарная проверка длины и извлечение элемента."""
        with self._lock:
            if len(self.data) > 0:
                return super().pop()
            return None
