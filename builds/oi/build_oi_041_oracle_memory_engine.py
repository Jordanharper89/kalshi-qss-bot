from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "oracle_memory_engine.py"
TEST = ROOT / "test_oi_041_oracle_memory_engine.py"
INIT = OI_DIR / "__init__.py"

engine_code = r'''"""
OI-041 Oracle Memory Engine

Read-only long-term market memory layer.

Purpose:
- Maintain structured Oracle memory categories.
- Convert live/historical intelligence into reusable memory records.
- Support future modules asking:
  "Have I seen this before?"
  "What happened next?"
  "How reliable was Oracle in this environment?"

Oracle remains read-only.
Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


MEMORY_TYPES = {
    "market",
    "pattern",
    "regime",
    "correlation",
    "forecast",
    "outcome",
    "strategy",
    "seasonal_event",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


@dataclass
class OracleMemoryRecord:
    memory_id: str
    memory_type: str
    market_ticker: Optional[str]
    title: str
    summary: str
    confidence: float
    importance: float
    created_at: str
    updated_at: str
    tags: List[str]
    source_module: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleMemoryEngine:
    """
    In-memory Oracle memory index.

    This engine is intentionally read-only from an execution perspective.
    It stores intelligence memory only; it never places, modifies, or cancels trades.
    """

    module_name = "oi_041_oracle_memory_engine"

    def __init__(self) -> None:
        self._records: Dict[str, OracleMemoryRecord] = {}
        self._type_index: Dict[str, List[str]] = {t: [] for t in MEMORY_TYPES}
        self._ticker_index: Dict[str, List[str]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "memory_records": len(self._records),
            "memory_types": sorted(MEMORY_TYPES),
            "by_type": {k: len(v) for k, v in self._type_index.items()},
        }

    def remember(
        self,
        memory_type: str,
        title: str,
        summary: str,
        payload: Optional[Dict[str, Any]] = None,
        market_ticker: Optional[str] = None,
        confidence: float = 50.0,
        importance: float = 50.0,
        tags: Optional[List[str]] = None,
        source_module: str = "oracle",
    ) -> Dict[str, Any]:
        if memory_type not in MEMORY_TYPES:
            raise ValueError(f"Unsupported memory_type: {memory_type}")

        payload = payload or {}
        tags = tags or []

        key_payload = {
            "memory_type": memory_type,
            "market_ticker": market_ticker,
            "title": title,
            "summary": summary,
            "payload": payload,
            "source_module": source_module,
        }
        memory_id = f"mem_{_stable_hash(key_payload)}"
        now = _utc_now()

        if memory_id in self._records:
            record = self._records[memory_id]
            record.updated_at = now
            record.confidence = max(record.confidence, float(confidence))
            record.importance = max(record.importance, float(importance))
            record.tags = sorted(set(record.tags + tags))
            record.payload.update(payload)
        else:
            record = OracleMemoryRecord(
                memory_id=memory_id,
                memory_type=memory_type,
                market_ticker=market_ticker,
                title=title,
                summary=summary,
                confidence=float(confidence),
                importance=float(importance),
                created_at=now,
                updated_at=now,
                tags=sorted(set(tags)),
                source_module=source_module,
                payload=payload,
            )
            self._records[memory_id] = record
            self._type_index[memory_type].append(memory_id)

            if market_ticker:
                self._ticker_index.setdefault(market_ticker, []).append(memory_id)

        return record.to_dict()

    def recall(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        records = list(self._records.values())

        if memory_type:
            records = [r for r in records if r.memory_type == memory_type]

        if market_ticker:
            records = [r for r in records if r.market_ticker == market_ticker]

        if tag:
            records = [r for r in records if tag in r.tags]

        records.sort(key=lambda r: (r.importance, r.confidence, r.updated_at), reverse=True)
        return [r.to_dict() for r in records[:limit]]

    def remember_market_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        ticker = snapshot.get("ticker") or snapshot.get("market_ticker")
        title = f"Market memory: {ticker or 'unknown'}"

        return self.remember(
            memory_type="market",
            market_ticker=ticker,
            title=title,
            summary="Stored market behavior snapshot for future similarity comparisons.",
            confidence=snapshot.get("confidence", 50.0),
            importance=snapshot.get("importance", 50.0),
            tags=["market_snapshot"],
            source_module="oi_041",
            payload=snapshot,
        )

    def remember_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        ticker = pattern.get("ticker") or pattern.get("market_ticker")
        name = pattern.get("pattern_name") or pattern.get("name") or "unnamed_pattern"

        return self.remember(
            memory_type="pattern",
            market_ticker=ticker,
            title=f"Pattern memory: {name}",
            summary="Stored historical pattern recurrence for future setup matching.",
            confidence=pattern.get("confidence", 50.0),
            importance=pattern.get("importance", 60.0),
            tags=["pattern_memory", name],
            source_module="oi_041",
            payload=pattern,
        )

    def remember_forecast_result(self, forecast: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
        ticker = forecast.get("ticker") or forecast.get("market_ticker") or outcome.get("ticker")

        payload = {
            "forecast": forecast,
            "outcome": outcome,
            "forecast_horizon": forecast.get("horizon"),
            "forecast_value": forecast.get("forecast_value"),
            "actual_value": outcome.get("actual_value"),
        }

        return self.remember(
            memory_type="forecast",
            market_ticker=ticker,
            title=f"Forecast memory: {ticker or 'unknown'}",
            summary="Stored forecast versus outcome for calibration and reliability learning.",
            confidence=forecast.get("confidence", 50.0),
            importance=70.0,
            tags=["forecast_memory", "calibration"],
            source_module="oi_041",
            payload=payload,
        )

    def similarity_probe(self, query: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        Lightweight deterministic similarity probe.

        Future builds can replace this with vector search or SQLite-backed scoring.
        """
        query_terms = set(str(v).lower() for v in query.values() if v is not None)
        scored = []

        for record in self._records.values():
            haystack = json.dumps(record.to_dict(), default=str).lower()
            score = sum(1 for term in query_terms if term and term in haystack)
            if score:
                scored.append((score, record))

        scored.sort(key=lambda x: (x[0], x[1].importance, x[1].confidence), reverse=True)

        return {
            "query": query,
            "matches": [r.to_dict() for _, r in scored[:limit]],
            "match_count": len(scored),
        }


oracle_memory_engine = OracleMemoryEngine()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_memory_engine import oracle_memory_engine


def test_oi_041_oracle_memory_engine():
    status = oracle_memory_engine.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    market = oracle_memory_engine.remember_market_snapshot({
        "ticker": "TEST-MARKET",
        "price": 42,
        "volume": 1000,
        "confidence": 72,
        "importance": 65,
    })

    assert market["memory_type"] == "market"
    assert market["market_ticker"] == "TEST-MARKET"

    pattern = oracle_memory_engine.remember_pattern({
        "ticker": "TEST-MARKET",
        "pattern_name": "late_reaction",
        "confidence": 81,
    })

    assert pattern["memory_type"] == "pattern"

    forecast = oracle_memory_engine.remember_forecast_result(
        {"ticker": "TEST-MARKET", "horizon": "30m", "forecast_value": 58, "confidence": 77},
        {"ticker": "TEST-MARKET", "actual_value": 61},
    )

    assert forecast["memory_type"] == "forecast"

    recalled = oracle_memory_engine.recall(market_ticker="TEST-MARKET")
    assert len(recalled) >= 3

    probe = oracle_memory_engine.similarity_probe({"ticker": "TEST-MARKET", "pattern": "late_reaction"})
    assert probe["match_count"] >= 1

    print("[PASS] OI-041 Oracle Memory Engine")
    print(oracle_memory_engine.status())


if __name__ == "__main__":
    test_oi_041_oracle_memory_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

export_line = "from .oracle_memory_engine import oracle_memory_engine, OracleMemoryEngine, OracleMemoryRecord\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-041 INSTALLER")
print(" Oracle Memory Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-041 installed")
print()
print("Run:")
print("python test_oi_041_oracle_memory_engine.py")