"""Thread-safe dict"""

import threading


class ThreadSafeDict:
    """Thread-safe dict"""

    def __init__(self):
        self._dict = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            self._dict[key] = value

    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)

    def delete(self, key):
        with self._lock:
            if key in self._dict:
                del self._dict[key]
