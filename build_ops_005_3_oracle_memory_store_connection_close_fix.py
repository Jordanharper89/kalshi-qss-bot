from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py"
TEST = ROOT / "test_ops_005_oracle_memory_store_runtime_path_migration.py"

code = r'''
"""
OPS-005 Oracle Persistent Memory Store Runtime Path Migration

Migrates Oracle persistent memory storage to the canonical OPS-004
RuntimePaths contract.

Oracle remains read-only intelligence. This store owns persistence access
only and must never execute trades.
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
class OracleMemoryRecord:
    key: str
    namespace: str
    value: Dict[str, Any]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OraclePersistentMemoryStore:
    """
    Canonical Oracle memory persistence store.

    Database location:
        RuntimePaths.oracle_memory_db()

    No hard-coded qseries_v2/data database paths are allowed here.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        ensure_runtime_layout()
        self.db_path = Path(db_path) if db_path else RuntimePaths.oracle_memory_db()
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
                CREATE TABLE IF NOT EXISTS oracle_memory (
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
                CREATE INDEX IF NOT EXISTS idx_oracle_memory_namespace
                ON oracle_memory(namespace)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def upsert(self, key: str, value: Dict[str, Any], namespace: str = "default") -> OracleMemoryRecord:
        if not key or not isinstance(key, str):
            raise ValueError("key must be a non-empty string")
        if not namespace or not isinstance(namespace, str):
            raise ValueError("namespace must be a non-empty string")
        if not isinstance(value, dict):
            raise ValueError("value must be a dictionary")

        now = self.now_iso()
        payload = json.dumps(value, sort_keys=True)
        existing = self.get(key=key, namespace=namespace)

        conn = self._connect()
        try:
            if existing:
                created_at = existing.created_at
                conn.execute(
                    """
                    UPDATE oracle_memory
                    SET value_json = ?, updated_at = ?
                    WHERE namespace = ? AND key = ?
                    """,
                    (payload, now, namespace, key),
                )
            else:
                created_at = now
                conn.execute(
                    """
                    INSERT INTO oracle_memory(namespace, key, value_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (namespace, key, payload, created_at, now),
                )
            conn.commit()
        finally:
            conn.close()

        return OracleMemoryRecord(
            key=key,
            namespace=namespace,
            value=value,
            created_at=created_at,
            updated_at=now,
        )

    def get(self, key: str, namespace: str = "default") -> Optional[OracleMemoryRecord]:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT namespace, key, value_json, created_at, updated_at
                FROM oracle_memory
                WHERE namespace = ? AND key = ?
                """,
                (namespace, key),
            ).fetchone()

            if not row:
                return None

            return OracleMemoryRecord(
                key=row["key"],
                namespace=row["namespace"],
                value=json.loads(row["value_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        finally:
            conn.close()

    def delete(self, key: str, namespace: str = "default") -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                """
                DELETE FROM oracle_memory
                WHERE namespace = ? AND key = ?
                """,
                (namespace, key),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def list_namespace(self, namespace: str = "default") -> List[OracleMemoryRecord]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT namespace, key, value_json, created_at, updated_at
                FROM oracle_memory
                WHERE namespace = ?
                ORDER BY updated_at DESC, key ASC
                """,
                (namespace,),
            ).fetchall()

            return [
                OracleMemoryRecord(
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
                FROM oracle_memory
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
                    "SELECT COUNT(*) AS total FROM oracle_memory WHERE namespace = ?",
                    (namespace,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS total FROM oracle_memory").fetchone()
            return int(row["total"])
        finally:
            conn.close()

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "store": "oracle_persistent_memory_store",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.oracle_memory_db(),
            "record_count": self.count(),
            "namespaces": self.namespaces(),
        }


def create_oracle_persistent_memory_store(
    db_path: Optional[Path] = None,
) -> OraclePersistentMemoryStore:
    return OraclePersistentMemoryStore(db_path=db_path)


oracle_persistent_memory_store = create_oracle_persistent_memory_store


__all__ = [
    "OracleMemoryRecord",
    "OraclePersistentMemoryStore",
    "create_oracle_persistent_memory_store",
    "oracle_persistent_memory_store",
]
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import (
    OraclePersistentMemoryStore,
    create_oracle_persistent_memory_store,
    oracle_persistent_memory_store,
)


def test_ops_005_oracle_memory_store_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        store = create_oracle_persistent_memory_store()

        assert isinstance(store, OraclePersistentMemoryStore)
        assert oracle_persistent_memory_store is create_oracle_persistent_memory_store
        assert store.db_path == RuntimePaths.oracle_memory_db()
        assert "qseries_v2/data" not in str(store.db_path).replace("\\", "/")

        rec1 = store.upsert(
            namespace="signals",
            key="market:test",
            value={"edge": 0.14, "grade": "A"},
        )

        assert rec1.key == "market:test"
        assert rec1.namespace == "signals"
        assert rec1.value["grade"] == "A"

        loaded = store.get(namespace="signals", key="market:test")
        assert loaded is not None
        assert loaded.value["edge"] == 0.14

        rec2 = store.upsert(
            namespace="signals",
            key="market:test",
            value={"edge": 0.19, "grade": "A+"},
        )

        assert rec2.created_at == rec1.created_at
        assert rec2.updated_at >= rec1.updated_at

        loaded2 = store.get(namespace="signals", key="market:test")
        assert loaded2 is not None
        assert loaded2.value["grade"] == "A+"

        store.upsert(namespace="runtime", key="heartbeat", value={"ok": True})

        assert store.count() == 2
        assert store.count("signals") == 1
        assert store.namespaces() == ["runtime", "signals"]

        listed = store.list_namespace("signals")
        assert len(listed) == 1
        assert listed[0].key == "market:test"

        health = store.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["record_count"] == 2

        assert store.delete(namespace="signals", key="market:test") is True
        assert store.get(namespace="signals", key="market:test") is None
        assert store.count() == 1

        print("[PASS] OPS-005 Oracle Memory Store Runtime Path Migration")
        print(health)

        del listed
        del loaded
        del loaded2
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
    test_ops_005_oracle_memory_store_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

print("========================================")
print(" OPS-005.3 INSTALLER")
print(" Oracle Memory Store Connection Close Fix")
print("========================================")
print(f"[OK] Rewrote {TARGET}")
print(f"[OK] Rewrote {TEST}")
print("")
print("[DONE] OPS-005.3 installed")
print("")
print("Run:")
print("py test_ops_005_oracle_memory_store_runtime_path_migration.py")