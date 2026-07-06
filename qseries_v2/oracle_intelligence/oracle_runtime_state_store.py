"""
OI-069 Oracle Runtime State Store

Purpose:
- Persist Oracle runtime state snapshots.
- Store command center dashboard/status snapshots.
- Support restart recovery and runtime telemetry history.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_DB_PATH = Path("qseries_v2") / "data" / "oracle_runtime_state.sqlite3"


class OracleRuntimeStateStore:
    module_name = "oi_069_oracle_runtime_state_store"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def status(self) -> Dict[str, Any]:
        with self._connect() as conn:
            snapshots = conn.execute("SELECT COUNT(*) FROM runtime_snapshots").fetchone()[0]
            events = conn.execute("SELECT COUNT(*) FROM runtime_events").fetchone()[0]

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "db_path": str(self.db_path),
            "snapshots": snapshots,
            "events": events,
        }

    def save_snapshot(
        self,
        snapshot_type: str,
        payload: Dict[str, Any],
        source_module: str = "oracle",
    ) -> Dict[str, Any]:
        snapshot_id = f"snap_{self._now_compact()}_{snapshot_type}"
        now = self._now()

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO runtime_snapshots (
                    snapshot_id,
                    snapshot_type,
                    source_module,
                    created_at,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                snapshot_id,
                snapshot_type,
                source_module,
                now,
                json.dumps(payload or {}, sort_keys=True, default=str),
            ))
            conn.commit()

        return {
            "status": "ok",
            "read_only": True,
            "snapshot_id": snapshot_id,
            "snapshot_type": snapshot_type,
            "created_at": now,
        }

    def latest_snapshot(self, snapshot_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        params = []
        where = ""

        if snapshot_type:
            where = "WHERE snapshot_type=?"
            params.append(snapshot_type)

        with self._connect() as conn:
            row = conn.execute(f"""
                SELECT snapshot_id, snapshot_type, source_module, created_at, payload_json
                FROM runtime_snapshots
                {where}
                ORDER BY created_at DESC
                LIMIT 1
            """, params).fetchone()

        return self._snapshot_row(row) if row else None

    def list_snapshots(
        self,
        snapshot_type: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        params = []
        where = ""

        if snapshot_type:
            where = "WHERE snapshot_type=?"
            params.append(snapshot_type)

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT snapshot_id, snapshot_type, source_module, created_at, payload_json
                FROM runtime_snapshots
                {where}
                ORDER BY created_at DESC
                LIMIT ?
            """, (*params, int(limit))).fetchall()

        return [self._snapshot_row(row) for row in rows]

    def log_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        source_module: str = "oracle",
    ) -> Dict[str, Any]:
        event_id = f"evt_{self._now_compact()}_{event_type}"
        now = self._now()

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO runtime_events (
                    event_id,
                    event_type,
                    severity,
                    source_module,
                    created_at,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event_type,
                severity,
                source_module,
                now,
                json.dumps(payload or {}, sort_keys=True, default=str),
            ))
            conn.commit()

        return {
            "status": "ok",
            "read_only": True,
            "event_id": event_id,
            "event_type": event_type,
            "severity": severity,
            "created_at": now,
        }

    def list_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []

        if event_type:
            clauses.append("event_type=?")
            params.append(event_type)

        if severity:
            clauses.append("severity=?")
            params.append(severity)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT event_id, event_type, severity, source_module, created_at, payload_json
                FROM runtime_events
                {where}
                ORDER BY created_at DESC
                LIMIT ?
            """, (*params, int(limit))).fetchall()

        return [self._event_row(row) for row in rows]

    def restore_runtime_summary(self) -> Dict[str, Any]:
        latest_dashboard = self.latest_snapshot("command_center_dashboard")
        latest_runtime = self.latest_snapshot("runtime_status")
        recent_events = self.list_events(limit=10)

        return {
            "status": "ok",
            "read_only": True,
            "latest_dashboard": latest_dashboard,
            "latest_runtime": latest_runtime,
            "recent_events": recent_events,
            "restorable": bool(latest_dashboard or latest_runtime),
        }

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runtime_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    snapshot_type TEXT NOT NULL,
                    source_module TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runtime_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source_module TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_snapshots_type ON runtime_snapshots(snapshot_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_snapshots_created ON runtime_snapshots(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_events_type ON runtime_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runtime_events_created ON runtime_events(created_at)")
            conn.commit()

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _snapshot_row(self, row) -> Dict[str, Any]:
        return {
            "snapshot_id": row[0],
            "snapshot_type": row[1],
            "source_module": row[2],
            "created_at": row[3],
            "payload": json.loads(row[4] or "{}"),
        }

    def _event_row(self, row) -> Dict[str, Any]:
        return {
            "event_id": row[0],
            "event_type": row[1],
            "severity": row[2],
            "source_module": row[3],
            "created_at": row[4],
            "payload": json.loads(row[5] or "{}"),
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _now_compact(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


oracle_runtime_state_store = OracleRuntimeStateStore()
