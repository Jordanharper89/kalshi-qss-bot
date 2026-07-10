
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from qseries_v2.ops.runtime_paths import RuntimePaths, ensure_runtime_layout


@dataclass(frozen=True)
class HistoricalMarketBaseline:
    market_id: str
    sample_count: int
    avg_price: float
    min_price: float
    max_price: float
    avg_liquidity: float
    sources: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalMarketBaselineEngine:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        ensure_runtime_layout()
        self.db_path = Path(db_path) if db_path else RuntimePaths.qseries_history_db()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

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

    def record_sample(
        self,
        market_id: str,
        price: float,
        liquidity: float = 0.0,
        source: str = "oracle",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = {"price": float(price), "liquidity": float(liquidity)}
        if extra:
            payload.update(extra)

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO historical_events(source, market_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (source, market_id, "market_sample", json.dumps(payload, sort_keys=True)),
            )
            conn.commit()
        finally:
            conn.close()

    def build_baseline(self, market_id: str) -> Optional[HistoricalMarketBaseline]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT source, payload_json
                FROM historical_events
                WHERE market_id = ?
                ORDER BY id ASC
                """,
                (market_id,),
            ).fetchall()
        finally:
            conn.close()

        prices: List[float] = []
        liquidities: List[float] = []
        sources = set()

        for row in rows:
            payload = json.loads(row["payload_json"])
            if "price" in payload:
                prices.append(float(payload["price"]))
            if "liquidity" in payload:
                liquidities.append(float(payload["liquidity"]))
            sources.add(row["source"])

        if not prices:
            return None

        return HistoricalMarketBaseline(
            market_id=market_id,
            sample_count=len(prices),
            avg_price=float(mean(prices)),
            min_price=float(min(prices)),
            max_price=float(max(prices)),
            avg_liquidity=float(mean(liquidities)) if liquidities else 0.0,
            sources=sorted(sources),
        )

    def compare_to_baseline(self, market_id: str, current_price: float) -> Dict[str, Any]:
        baseline = self.build_baseline(market_id)

        if baseline is None:
            return {
                "status": "no_baseline",
                "market_id": market_id,
                "current_price": float(current_price),
            }

        delta = float(current_price) - baseline.avg_price

        return {
            "status": "ok",
            "market_id": market_id,
            "current_price": float(current_price),
            "baseline": baseline.to_dict(),
            "delta": delta,
            "above_baseline": delta > 0,
            "below_baseline": delta < 0,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "historical_market_baseline_engine",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
        }


def create_historical_market_baseline_engine(
    db_path: Optional[Path] = None,
) -> HistoricalMarketBaselineEngine:
    return HistoricalMarketBaselineEngine(db_path=db_path)


historical_market_baseline_engine = create_historical_market_baseline_engine
oracle_market_baseline_engine = create_historical_market_baseline_engine


__all__ = [
    "HistoricalMarketBaseline",
    "HistoricalMarketBaselineEngine",
    "create_historical_market_baseline_engine",
    "historical_market_baseline_engine",
    "oracle_market_baseline_engine",
]
