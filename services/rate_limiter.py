import threading
import time


class RateLimiter:
    """
    Thread-safe rate limiter.

    Example:

        limiter = RateLimiter(5)

        limiter.acquire()

    Allows 5 requests per second.
    """

    def __init__(self, requests_per_second=5):
        self.requests_per_second = max(1, requests_per_second)
        self.min_interval = 1.0 / self.requests_per_second

        self._lock = threading.Lock()
        self._last_request = 0.0

        self.total_requests = 0
        self.total_wait_time = 0.0

    def acquire(self):
        with self._lock:

            now = time.monotonic()
            elapsed = now - self._last_request

            if elapsed < self.min_interval:
                wait = self.min_interval - elapsed
                time.sleep(wait)
                self.total_wait_time += wait

            self._last_request = time.monotonic()
            self.total_requests += 1

    def reset(self):
        with self._lock:
            self._last_request = 0.0
            self.total_requests = 0
            self.total_wait_time = 0.0

    def diagnostics(self):
        with self._lock:
            return {
                "requests_per_second": self.requests_per_second,
                "requests": self.total_requests,
                "wait_time": round(self.total_wait_time, 3),
            }