from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "oracle" / "database" / "db.py"
TEST = ROOT / "test_ops_012_oracle_database_runtime_path_migration.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
"""
OPS-012 Oracle Database Runtime Path Migration

Migrates oracle/database/db.py to the canonical OPS-004 RuntimePaths contract.

Oracle remains read-only intelligence.
Q Series remains the execution layer.

Database location:
    RuntimePaths.oracle_data_db()
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


def get_db_path() -> Path:
    ensure_runtime_layout()
    return RuntimePaths.oracle_data_db()


DB_PATH = get_db_path()


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def execute(
    sql: str,
    params: Optional[tuple[Any, ...]] = None,
    db_path: Optional[Path] = None,
) -> int:
    conn = connect(db_path=db_path)
    try:
        cursor = conn.execute(sql, params or ())
        conn.commit()
        return int(cursor.rowcount)
    finally:
        conn.close()


def fetch_one(
    sql: str,
    params: Optional[tuple[Any, ...]] = None,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    conn = connect(db_path=db_path)
    try:
        row = conn.execute(sql, params or ()).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(
    sql: str,
    params: Optional[tuple[Any, ...]] = None,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    conn = connect(db_path=db_path)
    try:
        rows = conn.execute(sql, params or ()).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def init_oracle_database(db_path: Optional[Path] = None) -> Path:
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = connect(db_path=path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oracle_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    return path


def health(db_path: Optional[Path] = None) -> Dict[str, Any]:
    path = Path(db_path) if db_path else get_db_path()
    init_oracle_database(db_path=path)

    return {
        "status": "ok",
        "store": "oracle_database",
        "db_path": str(path),
        "uses_runtime_paths": path == RuntimePaths.oracle_data_db(),
    }


__all__ = [
    "DB_PATH",
    "get_db_path",
    "connect",
    "execute",
    "fetch_one",
    "fetch_all",
    "init_oracle_database",
    "health",
]
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from oracle.database import db


def test_ops_012_oracle_database_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        db_path = db.get_db_path()

        assert db_path == RuntimePaths.oracle_data_db()
        assert "qseries_v2/data" not in str(db_path).replace("\\", "/")

        created_path = db.init_oracle_database()
        assert created_path == RuntimePaths.oracle_data_db()
        assert created_path.exists()

        db.execute(
            """
            INSERT OR REPLACE INTO oracle_metadata(key, value)
            VALUES (?, ?)
            """,
            ("runtime_paths", "enabled"),
        )

        row = db.fetch_one(
            """
            SELECT key, value
            FROM oracle_metadata
            WHERE key = ?
            """,
            ("runtime_paths",),
        )

        assert row is not None
        assert row["key"] == "runtime_paths"
        assert row["value"] == "enabled"

        rows = db.fetch_all("SELECT key, value FROM oracle_metadata")
        assert len(rows) == 1

        health = db.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True
        assert health["db_path"] == str(RuntimePaths.oracle_data_db())

        print("[PASS] OPS-012 Oracle Database Runtime Path Migration")
        print(health)

        del rows
        del row
        del health
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_012_oracle_database_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "oracle" / "database" / "__init__.py"
init_path.parent.mkdir(parents=True, exist_ok=True)

if not init_path.exists():
    init_path.write_text("", encoding="utf-8")

print("========================================")
print(" OPS-012 INSTALLER")
print(" Oracle Database Runtime Path Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Checked {init_path}")
print("")
print("[DONE] OPS-012 installed")
print("")
print("Run:")
print("py test_ops_012_oracle_database_runtime_path_migration.py")