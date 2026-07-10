
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
