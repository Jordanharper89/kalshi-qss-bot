"""
Oracle Health Monitor

ORACLE-021.5

Purpose:
- Monitor Oracle services.
- Report health.
- Detect failures.
- No Telegram logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict


class OracleHealthMonitor:

    def __init__(
        self,
        session_manager: Any,
        scheduler: Any,
    ):
        self.session_manager = session_manager
        self.scheduler = scheduler

    def report(self) -> Dict:

        session = self.session_manager.get_status()
        scheduler = self.scheduler.status()

        return {
            "timestamp": self._utc_now(),

            "oracle_state": session.get("status"),

            "scheduler_running": scheduler.get("running"),

            "scheduler_interval": scheduler.get("interval_seconds"),

            "cycles_completed": scheduler.get("cycles_completed"),

            "last_cycle": scheduler.get("last_cycle"),

            "last_started": session.get("last_started_at"),

            "last_finished": session.get("last_finished_at"),

            "last_error": session.get("last_error"),

            "healthy": self._healthy(
                session,
                scheduler,
            ),
        }

    def _healthy(
        self,
        session,
        scheduler,
    ):

        if not scheduler.get("running"):
            return False

        if session.get("status") == "ERROR":
            return False

        return True

    def _utc_now(self):
        return datetime.now(
            timezone.utc
        ).isoformat()