
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
class HistoricalPattern:
    market_id: str
    pattern_type: str
    confidence: float
    sample_count: int
    details: Dict[str, Any]
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalPatternRecognitionEngine:
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
            conn.commit()
        finally:
            conn.close()

    def record_price_sample(
        self,
        market_id: str,
        price: float,
        liquidity: float = 0.0,
        source: str = "oracle",
    ) -> None:
        payload = {"price": float(price), "liquidity": float(liquidity)}

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO historical_events(source, market_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source,
                    market_id,
                    "pattern_price_sample",
                    json.dumps(payload, sort_keys=True),
                    self.now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_price_series(self, market_id: str, limit: int = 250) -> List[float]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT payload_json
                FROM historical_events
                WHERE market_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (market_id, int(limit)),
            ).fetchall()
        finally:
            conn.close()

        prices: List[float] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if "price" in payload:
                prices.append(float(payload["price"]))

        return prices

    def detect_patterns(self, market_id: str) -> List[HistoricalPattern]:
        prices = self.load_price_series(market_id)
        detected_at = self.now_iso()

        if len(prices) < 3:
            return []

        patterns: List[HistoricalPattern] = []

        first = prices[0]
        last = prices[-1]
        avg = float(mean(prices))
        high = max(prices)
        low = min(prices)

        upward_steps = sum(1 for a, b in zip(prices, prices[1:]) if b > a)
        downward_steps = sum(1 for a, b in zip(prices, prices[1:]) if b < a)
        total_steps = max(len(prices) - 1, 1)

        if last > first and upward_steps / total_steps >= 0.6:
            patterns.append(
                HistoricalPattern(
                    market_id=market_id,
                    pattern_type="uptrend",
                    confidence=float(upward_steps / total_steps),
                    sample_count=len(prices),
                    details={"first": first, "last": last, "average": avg},
                    detected_at=detected_at,
                )
            )

        if last < first and downward_steps / total_steps >= 0.6:
            patterns.append(
                HistoricalPattern(
                    market_id=market_id,
                    pattern_type="downtrend",
                    confidence=float(downward_steps / total_steps),
                    sample_count=len(prices),
                    details={"first": first, "last": last, "average": avg},
                    detected_at=detected_at,
                )
            )

        price_range = high - low
        if avg and price_range / avg <= 0.05:
            patterns.append(
                HistoricalPattern(
                    market_id=market_id,
                    pattern_type="range_bound",
                    confidence=float(max(0.0, 1.0 - (price_range / avg))),
                    sample_count=len(prices),
                    details={"high": high, "low": low, "average": avg, "range": price_range},
                    detected_at=detected_at,
                )
            )

        if len(prices) >= 4:
            midpoint = len(prices) // 2
            early_avg = float(mean(prices[:midpoint]))
            late_avg = float(mean(prices[midpoint:]))
            if early_avg and abs(late_avg - early_avg) / early_avg >= 0.10:
                patterns.append(
                    HistoricalPattern(
                        market_id=market_id,
                        pattern_type="regime_shift",
                        confidence=float(min(1.0, abs(late_avg - early_avg) / early_avg)),
                        sample_count=len(prices),
                        details={"early_avg": early_avg, "late_avg": late_avg},
                        detected_at=detected_at,
                    )
                )

        return patterns

    def strongest_pattern(self, market_id: str) -> Optional[HistoricalPattern]:
        patterns = self.detect_patterns(market_id)
        if not patterns:
            return None
        return sorted(patterns, key=lambda item: item.confidence, reverse=True)[0]

    def analyze_market(self, market_id: str) -> Dict[str, Any]:
        patterns = self.detect_patterns(market_id)
        strongest = self.strongest_pattern(market_id)

        return {
            "status": "ok",
            "market_id": market_id,
            "pattern_count": len(patterns),
            "patterns": [pattern.to_dict() for pattern in patterns],
            "strongest_pattern": strongest.to_dict() if strongest else None,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "historical_pattern_recognition_engine",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
        }


def create_historical_pattern_recognition_engine(
    db_path: Optional[Path] = None,
) -> HistoricalPatternRecognitionEngine:
    return HistoricalPatternRecognitionEngine(db_path=db_path)


historical_pattern_recognition_engine = create_historical_pattern_recognition_engine
oracle_pattern_recognition_engine = create_historical_pattern_recognition_engine
oracle_historical_pattern_recognition_engine = create_historical_pattern_recognition_engine
oracle_pattern_engine = create_historical_pattern_recognition_engine


__all__ = [
    "HistoricalPattern",
    "HistoricalPatternRecognitionEngine",
    "create_historical_pattern_recognition_engine",
    "historical_pattern_recognition_engine",
    "oracle_pattern_recognition_engine",
    "oracle_historical_pattern_recognition_engine",
    "oracle_pattern_engine",
]
