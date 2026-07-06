"""
Oracle Scheduler

ORACLE-021.4

Purpose:
- Run Oracle continuously in the background.
- Prevent overlapping research cycles.
- Start/Stop scheduler.
- Execute Oracle Session Manager automatically.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict


class OracleScheduler:
    def __init__(
        self,
        oracle_session_manager: Any,
        interval_seconds: int = 180,
    ):
        self.oracle = oracle_session_manager
        self.interval_seconds = interval_seconds

        self._thread = None
        self._running = False

        self.cycles_completed = 0
        self.last_cycle = None

    def start(self):
        if self._running:
            return False

        self._running = True

        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )

        self._thread.start()

        return True

    def stop(self):
        self._running = False

    def is_running(self):
        return self._running

    def status(self) -> Dict:
        return {
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "cycles_completed": self.cycles_completed,
            "last_cycle": self.last_cycle,
        }

    def _loop(self):
        while self._running:

            try:
                self.oracle.run_once()

                self.cycles_completed += 1
                self.last_cycle = datetime.now(
                    timezone.utc
                ).isoformat()

            except Exception:
                pass

            time.sleep(self.interval_seconds)