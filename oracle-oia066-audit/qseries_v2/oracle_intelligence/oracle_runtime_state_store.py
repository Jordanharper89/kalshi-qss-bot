
"""
OPS-006 Oracle Runtime State Store Runtime Path Migration

Migrates Oracle runtime state persistence to the canonical OPS-004
RuntimePaths contract.

Oracle remains read-only intelligence. This store persists runtime state only
and must never execute trades.
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
class OracleRuntimeStateRecord:
    key: str
    namespace: str
    value: Dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleRuntimeStateStore:
    """
    Canonical Oracle runtime state persistence store.

    Database location:
        RuntimePaths.oracle_runtime_state_db()

    No hard-coded qseries_v2/data database paths are allowed here.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        ensure_runtime_layout()
        self.db_path = Path(db_path) if db_path else RuntimePaths.oracle_runtime_state_db()
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
                CREATE TABLE IF NOT EXISTS oracle_runtime_state (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (namespace, key)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_oracle_runtime_state_namespace
                ON oracle_runtime_state(namespace)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def set_state(
        self,
        key: str,
        value: Dict[str, Any],
        namespace: str = "default",
    ) -> OracleRuntimeStateRecord:
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")
        if not namespace or not isinstance(namespace, str):
            raise ValueError("namespace must be a non-empty string")
        if not isinstance(value, dict):
            raise ValueError("value must be a dictionary")

        now = self.now_iso()
        payload = json.dumps(value, sort_keys=True)
        existing = self.get_state(key=key, namespace=namespace)

        conn = self._connect()
        try:
            if existing:
                created_at = existing.created_at
                conn.execute(
                    """
                    UPDATE oracle_runtime_state
                    SET value_json = ?, updated_at = ?
                    WHERE namespace = ? AND key = ?
                    """,
                    (payload, now, namespace, key),
                )
            else:
                created_at = now
                conn.execute(
                    """
                    INSERT INTO oracle_runtime_state(namespace, key, value_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (namespace, key, payload, created_at, now),
                )
            conn.commit()
        finally:
            conn.close()

        return OracleRuntimeStateRecord(
            key=key,
            namespace=namespace,
            value=value,
            created_at=created_at,
            updated_at=now,
        )

    def upsert(
        self,
        key: str,
        value: Dict[str, Any],
        namespace: str = "default",
    ) -> OracleRuntimeStateRecord:
        return self.set_state(key=key, value=value, namespace=namespace)

    def get_state(self, key: str, namespace: str = "default") -> Optional[OracleRuntimeStateRecord]:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT namespace, key, value_json, created_at, updated_at
                FROM oracle_runtime_state
                WHERE namespace = ? AND key = ?
                """,
                (namespace, key),
            ).fetchone()

            if not row:
                return None

            return OracleRuntimeStateRecord(
                key=row["key"],
                namespace=row["namespace"],
                value=json.loads(row["value_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        finally:
            conn.close()

    def get(self, key: str, namespace: str = "default") -> Optional[OracleRuntimeStateRecord]:
        return self.get_state(key=key, namespace=namespace)

    def delete_state(self, key: str, namespace: str = "default") -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                DELETE FROM oracle_runtime_state
                WHERE namespace = ? AND key = ?
                """,
                (namespace, key),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def delete(self, key: str, namespace: str = "default") -> bool:
        return self.delete_state(key=key, namespace=namespace)

    def list_namespace(self, namespace: str = "default") -> List[OracleRuntimeStateRecord]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT namespace, key, value_json, created_at, updated_at
                FROM oracle_runtime_state
                WHERE namespace = ?
                ORDER BY updated_at DESC, key ASC
                """,
                (namespace,),
            ).fetchall()

            return [
                OracleRuntimeStateRecord(
                    key=row["key"],
                    namespace=row["namespace"],
                    value=json.loads(row["value_json"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def namespaces(self) -> List[str]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT namespace
                FROM oracle_runtime_state
                ORDER BY namespace ASC
                """
            ).fetchall()
            return [row["namespace"] for row in rows]
        finally:
            conn.close()

    def count(self, namespace: Optional[str] = None) -> int:
        conn = self._connect()
        try:
            if namespace:
                row = conn.execute(
                    "SELECT COUNT(*) AS total FROM oracle_runtime_state WHERE namespace = ?",
                    (namespace,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS total FROM oracle_runtime_state").fetchone()
            return int(row["total"])
        finally:
            conn.close()

    def clear_namespace(self, namespace: str = "default") -> int:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                DELETE FROM oracle_runtime_state
                WHERE namespace = ?
                """,
                (namespace,),
            )
            conn.commit()
            return int(cur.rowcount)
        finally:
            conn.close()

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "store": "oracle_runtime_state_store",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.oracle_runtime_state_db(),
            "record_count": self.count(),
            "namespaces": self.namespaces(),
        }


def create_oracle_runtime_state_store(
    db_path: Optional[Path] = None,
) -> OracleRuntimeStateStore:
    return OracleRuntimeStateStore(db_path=db_path)


oracle_runtime_state_store = create_oracle_runtime_state_store


__all__ = [
    "OracleRuntimeStateRecord",
    "OracleRuntimeStateStore",
    "create_oracle_runtime_state_store",
    "oracle_runtime_state_store",
]
