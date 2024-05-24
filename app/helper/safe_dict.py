"""Thread-safe dict"""

import threading


class ThreadSafeDict:
    """Thread-safe dict"""

    def __init__(self):
        self._dict = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        """Set self[key] to value."""

        with self._lock:
            self._dict[key] = value

    def get(self, key, default=None):
        """
        Return the value for key if key is in the dictionary, else default.
        """

        with self._lock:
            return self._dict.get(key, default)

    def delete(self, key):
        """Delete self[key]."""

        with self._lock:
            if key in self._dict:
                del self._dict[key]
