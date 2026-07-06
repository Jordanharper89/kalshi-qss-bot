from threading import RLock


class ServiceRegistry:
    """
    Global registry for platform services.
    """

    def __init__(self):
        self._services = {}
        self._lock = RLock()

    def register(self, name, service):
        with self._lock:
            self._services[name] = service

    def unregister(self, name):
        with self._lock:
            self._services.pop(name, None)

    def get(self, name):
        with self._lock:
            return self._services.get(name)

    def all(self):
        with self._lock:
            return dict(self._services)

    def start_all(self):
        with self._lock:
            for service in self._services.values():
                if not service.running:
                    service.start()

    def stop_all(self):
        with self._lock:
            for service in self._services.values():
                if service.running:
                    service.stop()

    def diagnostics(self):
        report = {}

        with self._lock:
            for name, service in self._services.items():
                report[name] = service.diagnostics()

        return report


registry = ServiceRegistry()