from abc import ABC, abstractmethod
from datetime import datetime


class BaseService(ABC):
    def __init__(self, name: str):
        self.name = name
        self.running = False
        self.started_at = None

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def restart(self):
        self.stop()
        self.start()

    def status(self):
        return {
            "service": self.name,
            "running": self.running,
            "started_at": self.started_at,
        }

    def health(self):
        return "running" if self.running else "stopped"

    def diagnostics(self):
        return {
            "service": self.name,
            "running": self.running,
            "started_at": self.started_at,
            "health": self.health(),
        }

    def mark_started(self):
        self.running = True
        self.started_at = datetime.utcnow()

    def mark_stopped(self):
        self.running = False