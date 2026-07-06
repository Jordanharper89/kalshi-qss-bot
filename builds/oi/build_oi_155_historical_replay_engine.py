from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "historical_replay_engine.py"
TEST = ROOT / "test_oi_155_historical_replay_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-155 — Oracle Historical Replay Engine

Read-only historical replay engine for Oracle Intelligence.

Purpose:
- Replay historical Oracle memory/index records in deterministic order.
- Preserve institutional lineage, explainability, and replayability.
- Produce replay frames for later validation and snapshot modules.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class HistoricalReplayFrame:
    replay_frame_id: str
    replay_rank: int
    source_id: str
    source_type: str
    market: str
    replay_score: float
    replay_tier: str
    replay_status: str
    replay_reason: str
    lineage_hash: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleHistoricalReplayEngine:
    name: str = "oracle_historical_replay_engine"
    version: str = "OI-155"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    replay_schema_version: str = "historical_replay_v1"
    supported_replay_domains: List[str] = field(default_factory=lambda: [
        "PREDICTION_MARKETS",
        "CRYPTO",
        "STOCKS",
        "ETFS",
        "FUTURES",
        "COMMODITIES",
        "FOREX",
        "MACROECONOMICS",
        "WEATHER",
        "NEWS",
        "ALTERNATIVE_DATA",
    ])

    def classify_tier(self, score: float) -> str:
        if score >= 90:
            return "institutional_replay"
        if score >= 75:
            return "validated_replay"
        if score >= 60:
            return "review_replay"
        return "low_signal_replay"

    def classify_status(self, score: float) -> str:
        if score >= 90:
            return "executive_replay_ready"
        if score >= 75:
            return "validated_replay_ready"
        if score >= 60:
            return "replay_review_required"
        return "insufficient_replay_signal"

    def _extract_records(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        source = _safe_dict(source)

        if isinstance(source.get("records"), list):
            return _safe_list(source.get("records"))

        if isinstance(source.get("entries"), list):
            return _safe_list(source.get("entries"))

        tiles = _safe_dict(source.get("tiles"))
        if isinstance(tiles.get("top_entries"), list):
            return _safe_list(tiles.get("top_entries"))

        return []

    def _score(self, record: Dict[str, Any]) -> float:
        return round(max(
            _num(record.get("replay_score")),
            _num(record.get("index_score")),
            _num(record.get("historical_score")),
            _num(record.get("ledger_score")),
            _num(record.get("recall_score")),
            _num(record.get("confidence_score")),
            _num(record.get("receipt_score")),
        ), 2)

    def _source_id(self, record: Dict[str, Any]) -> str:
        return str(
            record.get("source_id")
            or record.get("memory_index_id")
            or record.get("manifest_entry_id")
            or record.get("ledger_entry_id")
            or record.get("ledger_id")
            or record.get("recall_id")
            or _hash(record, 12)
        )

    def build_frame(self, record: Dict[str, Any], rank: int) -> HistoricalReplayFrame:
        record = _safe_dict(record)
        source_id = self._source_id(record)
        source_type = str(record.get("source_type") or record.get("record_type") or "historical_replay_record")
        market = str(record.get("market") or record.get("domain") or "UNKNOWN").upper()
        score = self._score(record)

        lineage_payload = {
            "source_id": source_id,
            "source_type": source_type,
            "market": market,
            "score": score,
            "rank": rank,
            "lineage": record.get("lineage_hash") or record.get("memory_index_id"),
        }

        return HistoricalReplayFrame(
            replay_frame_id=_hash(lineage_payload),
            replay_rank=rank,
            source_id=source_id,
            source_type=source_type,
            market=market,
            replay_score=score,
            replay_tier=self.classify_tier(score),
            replay_status=self.classify_status(score),
            replay_reason=(
                f"{market} historical record replayed at score {score}. "
                "Oracle replay is read-only; Q Series owns execution."
            ),
            lineage_hash=_hash(lineage_payload),
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def replay(self, source: Dict[str, Any], replay_mode: str = "score_desc") -> Dict[str, Any]:
        source = _safe_dict(source)
        records = self._extract_records(source)

        if replay_mode == "score_asc":
            ordered = sorted(records, key=lambda r: self._score(_safe_dict(r)))
        elif replay_mode == "source_order":
            ordered = list(records)
        else:
            ordered = sorted(records, key=lambda r: self._score(_safe_dict(r)), reverse=True)

        frames = [self.build_frame(record, idx + 1) for idx, record in enumerate(ordered)]

        market_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for frame in frames:
            market_counts[frame.market] = market_counts.get(frame.market, 0) + 1
            tier_counts[frame.replay_tier] = tier_counts.get(frame.replay_tier, 0) + 1
            status_counts[frame.replay_status] = status_counts.get(frame.replay_status, 0) + 1

        top = frames[0] if frames else None
        replay_id = _hash({
            "source_memory_index_batch_id": source.get("memory_index_batch_id"),
            "source_manifest_id": source.get("manifest_id"),
            "mode": replay_mode,
            "frames": [frame.__dict__ for frame in frames],
        })

        return {
            "module": self.name,
            "version": self.version,
            "replay_schema_version": self.replay_schema_version,
            "replay_id": replay_id,
            "replay_status": "replay_complete" if frames else "empty_replay",
            "replay_mode": replay_mode,
            "generated_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_replay_domains": list(self.supported_replay_domains),
            "source_memory_index_batch_id": source.get("memory_index_batch_id"),
            "source_manifest_id": source.get("manifest_id"),
            "source_dashboard_id": source.get("dashboard_id"),
            "frame_count": len(frames),
            "market_counts": market_counts,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "top_market": top.market if top else None,
            "top_replay_tier": top.replay_tier if top else None,
            "summary": {
                "headline": (
                    f"Historical replay complete; top replay market is {top.market}."
                    if top else
                    "Historical replay complete; no frames available."
                ),
                "replay_id": replay_id,
                "frame_count": len(frames),
                "top_market": top.market if top else None,
                "top_replay_tier": top.replay_tier if top else None,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
                "read_only": True,
            },
            "frames": [frame.__dict__ for frame in frames],
        }

    def explain_frame(self, replay: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        replay = _safe_dict(replay)
        frames = _safe_list(replay.get("frames"))

        for frame in frames:
            frame = _safe_dict(frame)
            if str(frame.get("source_id")) == str(source_id):
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "source_id": source_id,
                    "explanation": frame.get("replay_reason"),
                    "frame": frame,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "source_id": source_id,
            "explanation": "No replay frame found for requested source_id.",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_historical_replay_engine = OracleHistoricalReplayEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.historical_replay_engine import (
    oracle_historical_replay_engine,
)


def test_replay_builds_read_only_frames_from_memory_index():
    memory_index = {
        "memory_index_batch_id": "idx-001",
        "records": [
            {
                "source_id": "stocks-low",
                "source_type": "memory_index_record",
                "market": "STOCKS",
                "index_score": 79.0,
                "memory_tier": "validated_memory_index",
            },
            {
                "source_id": "crypto-high",
                "source_type": "memory_index_record",
                "market": "CRYPTO",
                "index_score": 96.0,
                "memory_tier": "institutional_memory_index",
            },
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index)

    assert replay["read_only"] is True
    assert replay["execution_allowed"] is False
    assert replay["execution_owner"] == "Q Series"
    assert replay["replay_status"] == "replay_complete"
    assert replay["frame_count"] == 2
    assert replay["frames"][0]["source_id"] == "crypto-high"
    assert replay["frames"][0]["read_only"] is True
    assert replay["frames"][0]["execution_allowed"] is False
    assert replay["top_market"] == "CRYPTO"


def test_replay_source_order_mode():
    memory_index = {
        "memory_index_batch_id": "idx-002",
        "records": [
            {"source_id": "first", "market": "WEATHER", "index_score": 60},
            {"source_id": "second", "market": "CRYPTO", "index_score": 99},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index, replay_mode="source_order")

    assert replay["replay_mode"] == "source_order"
    assert replay["frames"][0]["source_id"] == "first"
    assert replay["frames"][1]["source_id"] == "second"


def test_replay_score_asc_mode():
    memory_index = {
        "memory_index_batch_id": "idx-003",
        "records": [
            {"source_id": "high", "market": "CRYPTO", "index_score": 95},
            {"source_id": "low", "market": "FOREX", "index_score": 65},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index, replay_mode="score_asc")

    assert replay["frames"][0]["source_id"] == "low"
    assert replay["frames"][1]["source_id"] == "high"


def test_explain_frame():
    memory_index = {
        "memory_index_batch_id": "idx-004",
        "records": [
            {"source_id": "crypto-alpha", "market": "CRYPTO", "index_score": 94},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index)
    explanation = oracle_historical_replay_engine.explain_frame(replay, "crypto-alpha")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["frame"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_replay():
    replay = oracle_historical_replay_engine.replay({"memory_index_batch_id": "empty", "records": []})

    assert replay["replay_status"] == "empty_replay"
    assert replay["frame_count"] == 0
    assert replay["frames"] == []
    assert replay["summary"]["read_only"] is True


if __name__ == "__main__":
    test_replay_builds_read_only_frames_from_memory_index()
    test_replay_source_order_mode()
    test_replay_score_asc_mode()
    test_explain_frame()
    test_empty_replay()
    print("[PASS] OI-155 Oracle Historical Replay Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .historical_replay_engine import oracle_historical_replay_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-155 INSTALLER")
    print(" Oracle Historical Replay Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-155 installed")
    print("\nRun:")
    print("py test_oi_155_historical_replay_engine.py")


if __name__ == "__main__":
    main()