from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "market_relationship_engine.py"
TEST = ROOT / "test_ops_017_market_relationship_runtime_path_migration.py"

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
'''

test_code = r'''
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.market_relationship_engine import (
    MarketRelationshipEngine,
    create_market_relationship_engine,
    market_relationship_engine,
    oracle_market_relationship_engine,
    oracle_relationship_engine,
)


def test_ops_017_market_relationship_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_market_relationship_engine()

        assert isinstance(engine, MarketRelationshipEngine)
        assert market_relationship_engine is create_market_relationship_engine
        assert oracle_market_relationship_engine is create_market_relationship_engine
        assert oracle_relationship_engine is create_market_relationship_engine

        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        for price in [40, 42, 44, 46]:
            engine.record_market_sample("KXTEST-A", "GROUP-1", price=price, liquidity=1000)

        for price in [20, 21, 22, 23]:
            engine.record_market_sample("KXTEST-B", "GROUP-1", price=price, liquidity=800)

        for price in [70, 68, 66, 64]:
            engine.record_market_sample("KXTEST-C", "GROUP-1", price=price, liquidity=700)

        samples = engine.load_group_samples("GROUP-1")
        assert sorted(samples.keys()) == ["KXTEST-A", "KXTEST-B", "KXTEST-C"]
        assert samples["KXTEST-A"] == [40.0, 42.0, 44.0, 46.0]

        relationships = engine.detect_relationships("GROUP-1")
        assert len(relationships) == 3

        types = {item.relationship_type for item in relationships}
        assert "positive_correlation" in types
        assert "inverse_correlation" in types

        strongest = engine.strongest_relationship("GROUP-1")
        assert strongest is not None
        assert strongest.strength >= 0.0

        analysis = engine.analyze_group("GROUP-1")
        assert analysis["status"] == "ok"
        assert analysis["relationship_count"] == 3
        assert analysis["strongest_relationship"] is not None

        empty = engine.analyze_group("EMPTY")
        assert empty["status"] == "ok"
        assert empty["relationship_count"] == 0
        assert empty["strongest_relationship"] is None

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-017 Market Relationship Runtime Path Migration")
        print(health)

        del samples
        del relationships
        del strongest
        del analysis
        del empty
        del health
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
    test_ops_017_market_relationship_runtime_path_migration()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .market_relationship_engine import "
    "MarketRelationship, MarketRelationshipEngine, "
    "create_market_relationship_engine, market_relationship_engine, "
    "oracle_market_relationship_engine, oracle_relationship_engine\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" OPS-017 INSTALLER")
print(" Market Relationship Runtime Path Migration")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] OPS-017 installed")
print("")
print("Run:")
print("py test_ops_017_market_relationship_runtime_path_migration.py")