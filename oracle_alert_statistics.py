"""
Oracle Alert Statistics

ORACLE-023.9

Purpose:
- Track Oracle alert performance.
- Count alerts by action and grade.
- Provide dashboard statistics.
"""

from collections import Counter
from datetime import datetime, timezone


class OracleAlertStatistics:

    def __init__(self):
        self.started_at = self._utc_now()

        self.total_alerts = 0

        self.actions = Counter()
        self.grades = Counter()

    def record(self, signal):

        self.total_alerts += 1

        self.actions.update(
            [
                signal.get(
                    "action",
                    "UNKNOWN",
                )
            ]
        )

        self.grades.update(
            [
                signal.get(
                    "grade",
                    "UNKNOWN",
                )
            ]
        )

    def snapshot(self):

        return {
            "started_at": self.started_at,
            "total_alerts": self.total_alerts,
            "actions": dict(self.actions),
            "grades": dict(self.grades),
        }

    def reset(self):

        self.started_at = self._utc_now()

        self.total_alerts = 0

        self.actions.clear()
        self.grades.clear()

    def _utc_now(self):

        return datetime.now(
            timezone.utc
        ).isoformat()


oracle_alert_statistics = OracleAlertStatistics()