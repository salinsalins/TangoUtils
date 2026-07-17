import threading
from collections import UserDict


class ThreadSafeDict(UserDict):
    """A dictionary implementation safe for multithreaded access."""

    def __init__(self, other=None, /, **kwargs):
        self._lock = threading.RLock()
        super().__init__()
        if other is not None or kwargs:
            self.update(other, **kwargs)

    def __getitem__(self, key):
        with self._lock:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        with self._lock:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        with self._lock:
            super().__delitem__(key)

    def __contains__(self, key):
        with self._lock:
            return super().__contains__(key)

    def __len__(self):
        with self._lock:
            return super().__len__()

    def pop(self, key, default=None):
        with self._lock:
            return self.data.pop(key, default)

    def clear(self):
        with self._lock:
            super().clear()

    def update(self, other=None, /, **kwargs):
        with self._lock:
            if other is not None:
                super().update(other, **kwargs)
            else:
                super().update(**kwargs)

    def copy(self):
        with self._lock:
            return self.data.copy()
