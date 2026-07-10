from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "market_rhythm_analyzer.py"
TEST = ROOT / "test_ops_018_market_rhythm_analyzer_runtime_path_migration.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


@dataclass(frozen=True)
class MarketRhythm:
    market_id: str
    rhythm_type: str
    confidence: float
    sample_count: int
    details: Dict[str, Any]
    analyzed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRhythmAnalyzer:
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
                CREATE TABLE IF NOT EXISTS market_rhythm_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    liquidity REAL NOT NULL,
                    volume REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_rhythm_samples_market
                ON market_rhythm_samples(market_id)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record_market_sample(
        self,
        market_id: str,
        price: float,
        liquidity: float = 0.0,
        volume: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not market_id:
            raise ValueError("market_id is required")

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO market_rhythm_samples(
                    market_id, price, liquidity, volume, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    market_id,
                    float(price),
                    float(liquidity),
                    float(volume),
                    json.dumps(metadata or {}, sort_keys=True),
                    self.now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_samples(self, market_id: str, limit: int = 250) -> List[Dict[str, float]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT price, liquidity, volume
                FROM market_rhythm_samples
                WHERE market_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (market_id, int(limit)),
            ).fetchall()
        finally:
            conn.close()

        return [
            {
                "price": float(row["price"]),
                "liquidity": float(row["liquidity"]),
                "volume": float(row["volume"]),
            }
            for row in rows
        ]

    def analyze_rhythm(self, market_id: str) -> MarketRhythm:
        samples = self.load_samples(market_id)
        analyzed_at = self.now_iso()

        if len(samples) < 3:
            return MarketRhythm(
                market_id=market_id,
                rhythm_type="insufficient_data",
                confidence=0.0,
                sample_count=len(samples),
                details={"reason": "minimum 3 samples required"},
                analyzed_at=analyzed_at,
            )

        prices = [sample["price"] for sample in samples]
        volumes = [sample["volume"] for sample in samples]
        liquidities = [sample["liquidity"] for sample in samples]

        moves = [b - a for a, b in zip(prices, prices[1:])]
        abs_moves = [abs(move) for move in moves]

        avg_move = float(mean(abs_moves)) if abs_moves else 0.0
        avg_price = float(mean(prices)) if prices else 0.0
        avg_volume = float(mean(volumes)) if volumes else 0.0
        avg_liquidity = float(mean(liquidities)) if liquidities else 0.0

        direction_changes = 0
        previous_direction = 0

        for move in moves:
            direction = 1 if move > 0 else -1 if move < 0 else 0
            if previous_direction != 0 and direction != 0 and direction != previous_direction:
                direction_changes += 1
            if direction != 0:
                previous_direction = direction

        rhythm_ratio = direction_changes / max(len(moves), 1)
        move_ratio = avg_move / avg_price if avg_price else 0.0

        if rhythm_ratio >= 0.6 and move_ratio >= 0.02:
            rhythm_type = "choppy_reversal_rhythm"
            confidence = min(1.0, rhythm_ratio + move_ratio)
        elif rhythm_ratio <= 0.25 and prices[-1] > prices[0]:
            rhythm_type = "steady_upward_rhythm"
            confidence = min(1.0, 1.0 - rhythm_ratio)
        elif rhythm_ratio <= 0.25 and prices[-1] < prices[0]:
            rhythm_type = "steady_downward_rhythm"
            confidence = min(1.0, 1.0 - rhythm_ratio)
        elif move_ratio <= 0.015:
            rhythm_type = "quiet_range_rhythm"
            confidence = min(1.0, 1.0 - move_ratio)
        else:
            rhythm_type = "mixed_rhythm"
            confidence = 0.5

        return MarketRhythm(
            market_id=market_id,
            rhythm_type=rhythm_type,
            confidence=float(confidence),
            sample_count=len(samples),
            details={
                "first_price": prices[0],
                "last_price": prices[-1],
                "avg_price": avg_price,
                "avg_move": avg_move,
                "move_ratio": move_ratio,
                "direction_changes": direction_changes,
                "rhythm_ratio": rhythm_ratio,
                "avg_volume": avg_volume,
                "avg_liquidity": avg_liquidity,
            },
            analyzed_at=analyzed_at,
        )

    def analyze_market(self, market_id: str) -> Dict[str, Any]:
        rhythm = self.analyze_rhythm(market_id)
        return {
            "status": "ok",
            "market_id": market_id,
            "rhythm": rhythm.to_dict(),
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "market_rhythm_analyzer",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
        }


def create_market_rhythm_analyzer(db_path: Optional[Path] = None) -> MarketRhythmAnalyzer:
    return MarketRhythmAnalyzer(db_path=db_path)


market_rhythm_analyzer = create_market_rhythm_analyzer
oracle_market_rhythm_analyzer = create_market_rhythm_analyzer
oracle_rhythm_analyzer = create_market_rhythm_analyzer
oracle_rhythm_engine = create_market_rhythm_analyzer


__all__ = [
    "MarketRhythm",
    "MarketRhythmAnalyzer",
    "create_market_rhythm_analyzer",
    "market_rhythm_analyzer",
    "oracle_market_rhythm_analyzer",
    "oracle_rhythm_analyzer",
    "oracle_rhythm_engine",
]
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.market_rhythm_analyzer import (
    MarketRhythmAnalyzer,
    create_market_rhythm_analyzer,
    market_rhythm_analyzer,
    oracle_market_rhythm_analyzer,
    oracle_rhythm_analyzer,
    oracle_rhythm_engine,
)


def test_ops_018_market_rhythm_analyzer_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        analyzer = create_market_rhythm_analyzer()

        assert isinstance(analyzer, MarketRhythmAnalyzer)
        assert market_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_market_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_rhythm_engine is create_market_rhythm_analyzer

        assert analyzer.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(analyzer.db_path).replace("\\", "/")

        missing = analyzer.analyze_rhythm("UNKNOWN")
        assert missing.rhythm_type == "insufficient_data"
        assert missing.sample_count == 0

        for price in [40, 42, 41, 44, 42, 45, 43]:
            analyzer.record_market_sample(
                market_id="KXTEST-RHYTHM",
                price=price,
                liquidity=1000,
                volume=250,
            )

        samples = analyzer.load_samples("KXTEST-RHYTHM")
        assert len(samples) == 7
        assert samples[0]["price"] == 40.0

        rhythm = analyzer.analyze_rhythm("KXTEST-RHYTHM")
        assert rhythm.market_id == "KXTEST-RHYTHM"
        assert rhythm.sample_count == 7
        assert rhythm.confidence >= 0.0
        assert rhythm.rhythm_type in {
            "choppy_reversal_rhythm",
            "steady_upward_rhythm",
            "steady_downward_rhythm",
            "quiet_range_rhythm",
            "mixed_rhythm",
        }

        analysis = analyzer.analyze_market("KXTEST-RHYTHM")
        assert analysis["status"] == "ok"
        assert analysis["rhythm"]["market_id"] == "KXTEST-RHYTHM"

        health = analyzer.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-018 Market Rhythm Analyzer Runtime Path Migration")
        print(health)

        del missing
        del samples
        del rhythm
        del analysis
        del health
        del analyzer
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_018_market_rhythm_analyzer_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .market_rhythm_analyzer import "
    "MarketRhythm, MarketRhythmAnalyzer, create_market_rhythm_analyzer, "
    "market_rhythm_analyzer, oracle_market_rhythm_analyzer, "
    "oracle_rhythm_analyzer, oracle_rhythm_engine\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-018 INSTALLER")
print(" Market Rhythm Analyzer Runtime Path Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-018 installed")
print("")
print("Run:")
print("py test_ops_018_market_rhythm_analyzer_runtime_path_migration.py")