"""
Oracle Alert History

ORACLE-023.8

Purpose:
- Store recent Oracle alerts.
- Prevent repeated duplicate alerts.
- Provide alert history for Telegram UI.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


class OracleAlertHistory:

    def __init__(
        self,
        file_path="oracle_alert_history.json",
        max_items=250,
    ):
        self.file_path = Path(file_path)
        self.max_items = max_items

    def add(self, alert):

        alerts = self.load()

        payload = {
            "saved_at": self._utc_now(),
            "alert": alert,
        }

        alerts.insert(0, payload)

        alerts = alerts[: self.max_items]

        self.file_path.write_text(
            json.dumps(alerts, indent=4),
            encoding="utf-8",
        )

    def load(self):

        if not self.file_path.exists():
            return []

        try:
            return json.loads(
                self.file_path.read_text(
                    encoding="utf-8",
                )
            )

        except Exception:
            return []

    def latest(self, limit=10):

        return self.load()[:limit]

    def clear(self):

        if self.file_path.exists():
            self.file_path.unlink()

    def _utc_now(self):

        return datetime.now(
            timezone.utc
        ).isoformat()


oracle_alert_history = OracleAlertHistory()