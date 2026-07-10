from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "ops" / "historical_data_store.py"
TEST = ROOT / "test_ops_007_historical_data_store_runtime_path_migration.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
"""
OPS-007 Historical Data Store Runtime Path Migration

Migrates Q Series historical data persistence to the canonical OPS-004
RuntimePaths contract.

Database location:
    RuntimePaths.qseries_history_db()

No hard-coded qseries_v2/data database paths are allowed here.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


@dataclass(frozen=True)
class HistoricalDataRecord:
    source: str
    market_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalDataStore:
    """
    Canonical Q Series historical data store.

    Stores replayable historical market/event payloads.

    This store is persistence-only. It does not execute trades.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        ensure_runtime_layout()
        self.db_path = Path(db_path) if db_path else RuntimePaths.qseries_history_db()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS historical_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historical_events_market
                ON historical_events(market_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historical_events_source
                ON historical_events(source)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historical_events_type
                ON historical_events(event_type)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def append_event(
        self,
        source: str,
        market_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> HistoricalDataRecord:
        if not source or not isinstance(source, str):
            raise ValueError("source must be a non-empty string")
        if not market_id or not isinstance(market_id, str):
            raise ValueError("market_id must be a non-empty string")
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

        created_at = self.now_iso()
        payload_json = json.dumps(payload, sort_keys=True)

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO historical_events(source, market_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source, market_id, event_type, payload_json, created_at),
            )
            conn.commit()
        finally:
            conn.close()

        return HistoricalDataRecord(
            source=source,
            market_id=market_id,
            event_type=event_type,
            payload=payload,
            created_at=created_at,
        )

    def record(
        self,
        source: str,
        market_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> HistoricalDataRecord:
        return self.append_event(
            source=source,
            market_id=market_id,
            event_type=event_type,
            payload=payload,
        )

    def list_events(
        self,
        market_id: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[HistoricalDataRecord]:
        query = """
            SELECT source, market_id, event_type, payload_json, created_at
            FROM historical_events
            WHERE 1 = 1
        """
        params: List[Any] = []

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        if source:
            query += " AND source = ?"
            params.append(source)

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit))

        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
            return [
                HistoricalDataRecord(
                    source=row["source"],
                    market_id=row["market_id"],
                    event_type=row["event_type"],
                    payload=json.loads(row["payload_json"]),
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def latest_for_market(self, market_id: str) -> Optional[HistoricalDataRecord]:
        events = self.list_events(market_id=market_id, limit=1)
        return events[0] if events else None

    def sources(self) -> List[str]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT source
                FROM historical_events
                ORDER BY source ASC
                """
            ).fetchall()
            return [row["source"] for row in rows]
        finally:
            conn.close()

    def event_types(self) -> List[str]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT event_type
                FROM historical_events
                ORDER BY event_type ASC
                """
            ).fetchall()
            return [row["event_type"] for row in rows]
        finally:
            conn.close()

    def count(
        self,
        market_id: Optional[str] = None,
        source: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> int:
        query = "SELECT COUNT(*) AS total FROM historical_events WHERE 1 = 1"
        params: List[Any] = []

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        if source:
            query += " AND source = ?"
            params.append(source)

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        conn = self._connect()
        try:
            row = conn.execute(query, params).fetchone()
            return int(row["total"])
        finally:
            conn.close()

    def clear(self) -> int:
        conn = self._connect()
        try:
            cur = conn.execute("DELETE FROM historical_events")
            conn.commit()
            return int(cur.rowcount)
        finally:
            conn.close()

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "store": "historical_data_store",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
            "record_count": self.count(),
            "sources": self.sources(),
            "event_types": self.event_types(),
        }


def create_historical_data_store(db_path: Optional[Path] = None) -> HistoricalDataStore:
    return HistoricalDataStore(db_path=db_path)


historical_data_store = create_historical_data_store


__all__ = [
    "HistoricalDataRecord",
    "HistoricalDataStore",
    "create_historical_data_store",
    "historical_data_store",
]
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.historical_data_store import (
    HistoricalDataRecord,
    HistoricalDataStore,
    create_historical_data_store,
    historical_data_store,
)


def test_ops_007_historical_data_store_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        store = create_historical_data_store()

        assert isinstance(store, HistoricalDataStore)
        assert historical_data_store is create_historical_data_store
        assert store.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(store.db_path).replace("\\", "/")

        rec1 = store.append_event(
            source="oracle",
            market_id="KXTEST-001",
            event_type="snapshot",
            payload={"price": 42, "liquidity": 1000},
        )

        assert isinstance(rec1, HistoricalDataRecord)
        assert rec1.source == "oracle"
        assert rec1.market_id == "KXTEST-001"
        assert rec1.event_type == "snapshot"
        assert rec1.payload["price"] == 42

        rec2 = store.record(
            source="adapter",
            market_id="KXTEST-001",
            event_type="book_update",
            payload={"bid": 41, "ask": 43},
        )

        assert rec2.source == "adapter"
        assert rec2.event_type == "book_update"

        store.append_event(
            source="oracle",
            market_id="KXTEST-002",
            event_type="snapshot",
            payload={"price": 55},
        )

        assert store.count() == 3
        assert store.count(market_id="KXTEST-001") == 2
        assert store.count(source="oracle") == 2
        assert store.count(event_type="snapshot") == 2

        market_events = store.list_events(market_id="KXTEST-001", limit=10)
        assert len(market_events) == 2

        latest = store.latest_for_market("KXTEST-001")
        assert latest is not None
        assert latest.market_id == "KXTEST-001"

        assert store.sources() == ["adapter", "oracle"]
        assert store.event_types() == ["book_update", "snapshot"]

        health = store.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["record_count"] == 3

        cleared = store.clear()
        assert cleared == 3
        assert store.count() == 0

        print("[PASS] OPS-007 Historical Data Store Runtime Path Migration")
        print(health)

        del market_events
        del latest
        del rec1
        del rec2
        del health
        del store
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_007_historical_data_store_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "ops" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .historical_data_store import "
    "HistoricalDataRecord, HistoricalDataStore, "
    "create_historical_data_store, historical_data_store\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-007 INSTALLER")
print(" Historical Data Store Runtime Path Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-007 installed")
print("")
print("Run:")
print("py test_ops_007_historical_data_store_runtime_path_migration.py")