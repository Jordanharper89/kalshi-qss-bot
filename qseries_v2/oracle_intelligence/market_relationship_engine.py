
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
class MarketRelationship:
    primary_market_id: str
    related_market_id: str
    relationship_type: str
    strength: float
    sample_count: int
    details: Dict[str, Any]
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRelationshipEngine:
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
                CREATE TABLE IF NOT EXISTS market_relationship_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    market_id TEXT NOT NULL,
                    group_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    liquidity REAL NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_relationship_samples_market
                ON market_relationship_samples(market_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_relationship_samples_group
                ON market_relationship_samples(group_id)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record_market_sample(
        self,
        market_id: str,
        group_id: str,
        price: float,
        liquidity: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not market_id:
            raise ValueError("market_id is required")
        if not group_id:
            raise ValueError("group_id is required")

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO market_relationship_samples(
                    market_id, group_id, price, liquidity, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    market_id,
                    group_id,
                    float(price),
                    float(liquidity),
                    json.dumps(metadata or {}, sort_keys=True),
                    self.now_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_group_samples(self, group_id: str) -> Dict[str, List[float]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT market_id, price
                FROM market_relationship_samples
                WHERE group_id = ?
                ORDER BY id ASC
                """,
                (group_id,),
            ).fetchall()
        finally:
            conn.close()

        grouped: Dict[str, List[float]] = {}
        for row in rows:
            grouped.setdefault(row["market_id"], []).append(float(row["price"]))

        return grouped

    def _relationship_strength(self, first: List[float], second: List[float]) -> float:
        size = min(len(first), len(second))
        if size < 2:
            return 0.0

        a = first[-size:]
        b = second[-size:]

        a_moves = [y - x for x, y in zip(a, a[1:])]
        b_moves = [y - x for x, y in zip(b, b[1:])]

        if not a_moves or not b_moves:
            return 0.0

        same_direction = 0
        opposite_direction = 0

        for left, right in zip(a_moves, b_moves):
            if left == 0 or right == 0:
                continue
            if (left > 0 and right > 0) or (left < 0 and right < 0):
                same_direction += 1
            else:
                opposite_direction += 1

        total = same_direction + opposite_direction
        if total == 0:
            return 0.0

        return abs(same_direction - opposite_direction) / total

    def detect_relationships(self, group_id: str) -> List[MarketRelationship]:
        samples = self.load_group_samples(group_id)
        market_ids = sorted(samples.keys())
        detected_at = self.now_iso()

        relationships: List[MarketRelationship] = []

        for i, primary in enumerate(market_ids):
            for related in market_ids[i + 1:]:
                first = samples[primary]
                second = samples[related]
                size = min(len(first), len(second))

                if size < 3:
                    continue

                strength = self._relationship_strength(first, second)

                first_delta = first[-1] - first[0]
                second_delta = second[-1] - second[0]

                if first_delta == 0 or second_delta == 0:
                    relationship_type = "neutral"
                elif (first_delta > 0 and second_delta > 0) or (first_delta < 0 and second_delta < 0):
                    relationship_type = "positive_correlation"
                else:
                    relationship_type = "inverse_correlation"

                relationships.append(
                    MarketRelationship(
                        primary_market_id=primary,
                        related_market_id=related,
                        relationship_type=relationship_type,
                        strength=float(strength),
                        sample_count=size,
                        details={
                            "primary_first": first[0],
                            "primary_last": first[-1],
                            "related_first": second[0],
                            "related_last": second[-1],
                            "primary_avg": float(mean(first)),
                            "related_avg": float(mean(second)),
                            "group_id": group_id,
                        },
                        detected_at=detected_at,
                    )
                )

        return relationships

    def strongest_relationship(self, group_id: str) -> Optional[MarketRelationship]:
        relationships = self.detect_relationships(group_id)
        if not relationships:
            return None
        return sorted(relationships, key=lambda item: item.strength, reverse=True)[0]

    def analyze_group(self, group_id: str) -> Dict[str, Any]:
        relationships = self.detect_relationships(group_id)
        strongest = self.strongest_relationship(group_id)

        return {
            "status": "ok",
            "group_id": group_id,
            "relationship_count": len(relationships),
            "relationships": [item.to_dict() for item in relationships],
            "strongest_relationship": strongest.to_dict() if strongest else None,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "engine": "market_relationship_engine",
            "db_path": str(self.db_path),
            "uses_runtime_paths": self.db_path == RuntimePaths.qseries_history_db(),
        }


def create_market_relationship_engine(
    db_path: Optional[Path] = None,
) -> MarketRelationshipEngine:
    return MarketRelationshipEngine(db_path=db_path)


market_relationship_engine = create_market_relationship_engine
oracle_market_relationship_engine = create_market_relationship_engine
oracle_relationship_engine = create_market_relationship_engine


__all__ = [
    "MarketRelationship",
    "MarketRelationshipEngine",
    "create_market_relationship_engine",
    "market_relationship_engine",
    "oracle_market_relationship_engine",
    "oracle_relationship_engine",
]
