"""
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
