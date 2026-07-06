"""
Oracle State Store

ORACLE-021.7

Purpose:
- Persist Oracle runtime state.
- Save/load metrics and session state.
- JSON-based storage.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict


class OracleStateStore:
    def __init__(self, state_file: str = "oracle_state.json"):
        self.state_file = Path(state_file)

    def save(self, state: Dict[str, Any]) -> None:
        payload = {
            "saved_at": self._utc_now(),
            "state": state,
        }

        self.state_file.write_text(
            json.dumps(payload, indent=4),
            encoding="utf-8",
        )

    def load(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}

        try:
            payload = json.loads(
                self.state_file.read_text(encoding="utf-8")
            )

            return payload.get("state", {})

        except Exception:
            return {}

    def exists(self) -> bool:
        return self.state_file.exists()

    def delete(self) -> None:
        if self.state_file.exists():
            self.state_file.unlink()

    def _utc_now(self) -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()