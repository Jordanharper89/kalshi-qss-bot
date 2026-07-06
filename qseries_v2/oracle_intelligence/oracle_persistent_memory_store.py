"""
OI-042 Oracle Persistent Memory Store

SQLite-backed long-term Oracle memory persistence.

Read-only trading rule:
- This module stores intelligence memory only.
- It never places, modifies, cancels, or recommends execution.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_DB_PATH = Path("qseries_v2") / "data" / "oracle_memory.sqlite3"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OraclePersistentMemoryStore:
    module_name = "oi_042_oracle_persistent_memory_store"

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS oracle_memory (
                    memory_id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    market_ticker TEXT,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    importance REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    source_module TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_oracle_memory_type ON oracle_memory(memory_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_oracle_memory_ticker ON oracle_memory(market_ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_oracle_memory_updated ON oracle_memory(updated_at)")
            conn.commit()

    def status(self) -> Dict[str, Any]:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM oracle_memory").fetchone()[0]

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "db_path": str(self.db_path),
            "memory_records": count,
        }

    def upsert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        now = _utc_now()

        created_at = record.get("created_at") or now
        updated_at = record.get("updated_at") or now

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO oracle_memory (
                    memory_id,
                    memory_type,
                    market_ticker,
                    title,
                    summary,
                    confidence,
                    importance,
                    created_at,
                    updated_at,
                    tags_json,
                    source_module,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    market_ticker=excluded.market_ticker,
                    title=excluded.title,
                    summary=excluded.summary,
                    confidence=MAX(oracle_memory.confidence, excluded.confidence),
                    importance=MAX(oracle_memory.importance, excluded.importance),
                    updated_at=excluded.updated_at,
                    tags_json=excluded.tags_json,
                    source_module=excluded.source_module,
                    payload_json=excluded.payload_json
            """, (
                record["memory_id"],
                record["memory_type"],
                record.get("market_ticker"),
                record["title"],
                record["summary"],
                float(record.get("confidence", 50.0)),
                float(record.get("importance", 50.0)),
                created_at,
                updated_at,
                json.dumps(record.get("tags", []), sort_keys=True),
                record.get("source_module", "oracle"),
                json.dumps(record.get("payload", {}), sort_keys=True, default=str),
            ))
            conn.commit()

        return self.get(record["memory_id"]) or record

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT memory_id, memory_type, market_ticker, title, summary,
                       confidence, importance, created_at, updated_at,
                       tags_json, source_module, payload_json
                FROM oracle_memory
                WHERE memory_id=?
            """, (memory_id,)).fetchone()

        return self._row_to_dict(row) if row else None

    def recall(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []

        if memory_type:
            clauses.append("memory_type=?")
            params.append(memory_type)

        if market_ticker:
            clauses.append("market_ticker=?")
            params.append(market_ticker)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT memory_id, memory_type, market_ticker, title, summary,
                       confidence, importance, created_at, updated_at,
                       tags_json, source_module, payload_json
                FROM oracle_memory
                {where}
                ORDER BY importance DESC, confidence DESC, updated_at DESC
                LIMIT ?
            """, (*params, int(limit))).fetchall()

        records = [self._row_to_dict(row) for row in rows]

        if tag:
            records = [r for r in records if tag in r.get("tags", [])]

        return records

    def search_text(self, text: str, limit: int = 25) -> List[Dict[str, Any]]:
        needle = f"%{text.lower()}%"

        with self._connect() as conn:
            rows = conn.execute("""
                SELECT memory_id, memory_type, market_ticker, title, summary,
                       confidence, importance, created_at, updated_at,
                       tags_json, source_module, payload_json
                FROM oracle_memory
                WHERE lower(title) LIKE ?
                   OR lower(summary) LIKE ?
                   OR lower(tags_json) LIKE ?
                   OR lower(payload_json) LIKE ?
                ORDER BY importance DESC, confidence DESC, updated_at DESC
                LIMIT ?
            """, (needle, needle, needle, needle, int(limit))).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row) -> Dict[str, Any]:
        return {
            "memory_id": row[0],
            "memory_type": row[1],
            "market_ticker": row[2],
            "title": row[3],
            "summary": row[4],
            "confidence": row[5],
            "importance": row[6],
            "created_at": row[7],
            "updated_at": row[8],
            "tags": json.loads(row[9] or "[]"),
            "source_module": row[10],
            "payload": json.loads(row[11] or "{}"),
        }


oracle_persistent_memory_store = OraclePersistentMemoryStore()
