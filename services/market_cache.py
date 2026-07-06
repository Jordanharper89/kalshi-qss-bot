from datetime import datetime, timedelta
from threading import RLock


class MarketCache:
    """
    Thread-safe market data cache.
    """

    def __init__(self, ttl_seconds=10):
        self.ttl_seconds = ttl_seconds
        self._data = {}
        self._lock = RLock()
        self.hits = 0
        self.misses = 0
        self.sets = 0

    def set(self, ticker, value):
        ticker = str(ticker).upper()

        with self._lock:
            self._data[ticker] = {
                "value": value,
                "updated_at": datetime.utcnow(),
            }
            self.sets += 1

    def get(self, ticker):
        ticker = str(ticker).upper()

        with self._lock:
            item = self._data.get(ticker)

            if not item:
                self.misses += 1
                return None

            if self.is_expired_item(item):
                self.misses += 1
                return None

            self.hits += 1
            return item["value"]

    def get_stale(self, ticker):
        ticker = str(ticker).upper()

        with self._lock:
            item = self._data.get(ticker)
            return item["value"] if item else None

    def is_expired_item(self, item):
        updated_at = item.get("updated_at")
        if not updated_at:
            return True

        return datetime.utcnow() - updated_at > timedelta(seconds=self.ttl_seconds)

    def remove(self, ticker):
        ticker = str(ticker).upper()

        with self._lock:
            self._data.pop(ticker, None)

    def clear(self):
        with self._lock:
            self._data.clear()

    def keys(self):
        with self._lock:
            return list(self._data.keys())

    def size(self):
        with self._lock:
            return len(self._data)

    def diagnostics(self):
        with self._lock:
            return {
                "cache_size": len(self._data),
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "sets": self.sets,
            }