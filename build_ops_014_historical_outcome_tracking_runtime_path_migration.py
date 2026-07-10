from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "historical_outcome_tracking_engine.py"
TEST = ROOT / "test_ops_014_historical_outcome_tracking_runtime_path_migration.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


@dataclass(frozen=True)
class HistoricalOutcomeRecord:
    market_id: str
    prediction: str
    outcome: str
    correct: bool
    confidence: float
    metadata: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalOutcomeTrackingEngine:
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
                CREATE TABLE IF NOT EXISTS historical_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    correct INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_historical_outcomes_market
                ON historical_outcomes(market_id)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record_outcome(
        self,
        market_id: str,
        prediction: str,
        outcome: str,
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HistoricalOutcomeRecord:
        if not market_id:
            raise ValueError("market_id is required")
        if not prediction:
            raise ValueError("prediction is required")
        if not outcome:
            raise ValueError("outcome is required")

        correct = prediction.strip().lower() == outcome.strip().lower()
        created_at = self.now_iso()
        metadata = metadata or {}

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO historical_outcomes(
                    market_id, prediction, outcome, correct, confidence, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    market_id,
                    prediction,
                    outcome,
                    1 if correct else 0,
                    float(confidence),
                    json.dumps(metadata, sort_keys=True),
                    created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return HistoricalOutcomeRecord(
            market_id=market_id,
            prediction=prediction,
            outcome=outcome,
            correct=correct,
            confidence=float(confidence),
            metadata=metadata,
            created_at=created_at,
        )

    def list_outcomes(self, market_id: Optional[str] = None, limit: int = 100) -> List[HistoricalOutcomeRecord]:
        query = """
            SELECT market_id, prediction, outcome, correct, confidence, metadata_json, created_at
            FROM historical_outcomes
            WHERE 1 = 1
        """
        params: List[Any] = []

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit))

        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
            return [
                HistoricalOutcomeRecord(
                    market_id=row["market_id"],
                    prediction=row["prediction"],
                    outcome=row["outcome"],
                    correct=bool(row["correct"]),
                    confidence=float(row["confidence"]),
                    metadata=json.loads(row["metadata_json"]),
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def accuracy(self, market_id: Optional[str] = None) -> Dict[str, Any]:
        query = "SELECT COUNT(*) AS total, SUM(correct) AS wins FROM historical_outcomes WHERE 1 = 1"
        params: List[Any] = []

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)

        conn = self._connect()
        try:
            row = conn.execute(query, params).fetchone()
        finally:
            conn.close()

        total = int(row["total"] or 0)
        wins = int(row["wins"] or 0)
        losses = total - wins

        return {
            "market_id": market_id,
            "total": total,
            "wins": wins,
            "losses": losses,
            "accuracy": float(wins / total) if total else 0.0,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "historical_outcome_tracking_engine",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
            "accuracy": self.accuracy(),
        }


def create_historical_outcome_tracking_engine(
    db_path: Optional[Path] = None,
) -> HistoricalOutcomeTrackingEngine:
    return HistoricalOutcomeTrackingEngine(db_path=db_path)


historical_outcome_tracking_engine = create_historical_outcome_tracking_engine
oracle_historical_outcome_tracking_engine = create_historical_outcome_tracking_engine


__all__ = [
    "HistoricalOutcomeRecord",
    "HistoricalOutcomeTrackingEngine",
    "create_historical_outcome_tracking_engine",
    "historical_outcome_tracking_engine",
    "oracle_historical_outcome_tracking_engine",
]
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.historical_outcome_tracking_engine import (
    HistoricalOutcomeTrackingEngine,
    create_historical_outcome_tracking_engine,
    historical_outcome_tracking_engine,
    oracle_historical_outcome_tracking_engine,
)


def test_ops_014_historical_outcome_tracking_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_historical_outcome_tracking_engine()

        assert isinstance(engine, HistoricalOutcomeTrackingEngine)
        assert historical_outcome_tracking_engine is create_historical_outcome_tracking_engine
        assert oracle_historical_outcome_tracking_engine is create_historical_outcome_tracking_engine
        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        rec1 = engine.record_outcome(
            market_id="KXTEST-001",
            prediction="YES",
            outcome="YES",
            confidence=0.72,
            metadata={"grade": "A"},
        )

        rec2 = engine.record_outcome(
            market_id="KXTEST-001",
            prediction="NO",
            outcome="YES",
            confidence=0.55,
            metadata={"grade": "B"},
        )

        assert rec1.correct is True
        assert rec2.correct is False

        rows = engine.list_outcomes("KXTEST-001")
        assert len(rows) == 2

        acc = engine.accuracy("KXTEST-001")
        assert acc["total"] == 2
        assert acc["wins"] == 1
        assert acc["losses"] == 1
        assert acc["accuracy"] == 0.5

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-014 Historical Outcome Tracking Runtime Path Migration")
        print(health)

        del rows
        del acc
        del health
        del rec1
        del rec2
        del engine
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_014_historical_outcome_tracking_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .historical_outcome_tracking_engine import "
    "HistoricalOutcomeRecord, HistoricalOutcomeTrackingEngine, "
    "create_historical_outcome_tracking_engine, historical_outcome_tracking_engine, "
    "oracle_historical_outcome_tracking_engine\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-014 INSTALLER")
print(" Historical Outcome Tracking Runtime Path Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-014 installed")
print("")
print("Run:")
print("py test_ops_014_historical_outcome_tracking_runtime_path_migration.py")