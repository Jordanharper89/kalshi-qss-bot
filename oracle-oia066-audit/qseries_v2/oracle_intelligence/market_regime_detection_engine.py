
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


@dataclass(frozen=True)
class MarketRegime:
    market_id: str
    regime: str
    confidence: float
    sample_count: int
    details: Dict[str, Any]
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRegimeDetectionEngine:
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

    def record_market_sample(
        self,
        market_id: str,
        price: float,
        liquidity: float = 0.0,
        volume: float = 0.0,
        source: str = "oracle",
    ) -> None:
        payload = {
            "price": float(price),
            "liquidity": float(liquidity),
            "volume": float(volume),
        }

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
                    "regime_market_sample",
                    json.dumps(payload, sort_keys=True),
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

        samples: List[Dict[str, float]] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            if "price" in payload:
                samples.append(
                    {
                        "price": float(payload.get("price", 0.0)),
                        "liquidity": float(payload.get("liquidity", 0.0)),
                        "volume": float(payload.get("volume", 0.0)),
                    }
                )

        return samples

    def detect_regime(self, market_id: str) -> MarketRegime:
        samples = self.load_samples(market_id)
        detected_at = self.now_iso()

        if len(samples) < 3:
            return MarketRegime(
                market_id=market_id,
                regime="insufficient_data",
                confidence=0.0,
                sample_count=len(samples),
                details={"reason": "minimum 3 samples required"},
                detected_at=detected_at,
            )

        prices = [sample["price"] for sample in samples]
        liquidities = [sample["liquidity"] for sample in samples]
        volumes = [sample["volume"] for sample in samples]

        first = prices[0]
        last = prices[-1]
        avg_price = float(mean(prices))
        volatility = float(pstdev(prices)) if len(prices) > 1 else 0.0
        volatility_ratio = float(volatility / avg_price) if avg_price else 0.0

        upward_steps = sum(1 for a, b in zip(prices, prices[1:]) if b > a)
        downward_steps = sum(1 for a, b in zip(prices, prices[1:]) if b < a)
        total_steps = max(len(prices) - 1, 1)

        avg_liquidity = float(mean(liquidities)) if liquidities else 0.0
        avg_volume = float(mean(volumes)) if volumes else 0.0

        trend_strength = abs(last - first) / avg_price if avg_price else 0.0

        if volatility_ratio >= 0.12:
            regime = "volatile"
            confidence = min(1.0, volatility_ratio * 4)
        elif last > first and upward_steps / total_steps >= 0.6:
            regime = "bullish_trend"
            confidence = float(max(upward_steps / total_steps, trend_strength))
        elif last < first and downward_steps / total_steps >= 0.6:
            regime = "bearish_trend"
            confidence = float(max(downward_steps / total_steps, trend_strength))
        elif volatility_ratio <= 0.03:
            regime = "stable_range"
            confidence = float(max(0.0, 1.0 - volatility_ratio))
        else:
            regime = "mixed"
            confidence = 0.5

        return MarketRegime(
            market_id=market_id,
            regime=regime,
            confidence=float(min(1.0, confidence)),
            sample_count=len(samples),
            details={
                "first_price": first,
                "last_price": last,
                "avg_price": avg_price,
                "volatility": volatility,
                "volatility_ratio": volatility_ratio,
                "upward_steps": upward_steps,
                "downward_steps": downward_steps,
                "avg_liquidity": avg_liquidity,
                "avg_volume": avg_volume,
            },
            detected_at=detected_at,
        )

    def analyze_market(self, market_id: str) -> Dict[str, Any]:
        regime = self.detect_regime(market_id)
        return {
            "status": "ok",
            "market_id": market_id,
            "regime": regime.to_dict(),
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "market_regime_detection_engine",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
        }


def create_market_regime_detection_engine(
    db_path: Optional[Path] = None,
) -> MarketRegimeDetectionEngine:
    return MarketRegimeDetectionEngine(db_path=db_path)


market_regime_detection_engine = create_market_regime_detection_engine
oracle_regime_detection_engine = create_market_regime_detection_engine
oracle_market_regime_detection_engine = create_market_regime_detection_engine
oracle_regime_engine = create_market_regime_detection_engine


__all__ = [
    "MarketRegime",
    "MarketRegimeDetectionEngine",
    "create_market_regime_detection_engine",
    "market_regime_detection_engine",
    "oracle_regime_detection_engine",
    "oracle_market_regime_detection_engine",
    "oracle_regime_engine",
]
