"""
OI-152 — Oracle Historical Intelligence Manifest Engine

Builds a read-only institutional manifest for historical Oracle intelligence.
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
class HistoricalManifestEntry:
    manifest_entry_id: str
    source_id: str
    source_type: str
    market: str
    historical_score: float
    manifest_tier: str
    manifest_status: str
    lineage_hash: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleHistoricalIntelligenceManifestEngine:
    name: str = "oracle_historical_intelligence_manifest_engine"
    version: str = "OI-152"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    supported_domains: List[str] = field(default_factory=lambda: [
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
            return "institutional_historical_manifest"
        if score >= 75:
            return "validated_historical_manifest"
        if score >= 60:
            return "watchlist_historical_manifest"
        return "low_signal_historical_manifest"

    def classify_status(self, score: float) -> str:
        if score >= 90:
            return "executive_ready_manifest"
        if score >= 75:
            return "validated_manifest"
        if score >= 60:
            return "review_required_manifest"
        return "insufficient_manifest_quality"

    def build_entry(self, item: Dict[str, Any]) -> HistoricalManifestEntry:
        source_id = str(
            item.get("ledger_id")
            or item.get("recall_id")
            or item.get("snapshot_id")
            or item.get("case_id")
            or item.get("source_id")
            or _hash(item, 12)
        )
        source_type = str(item.get("source_type") or item.get("record_type") or "historical_intelligence")
        market = str(item.get("market") or item.get("domain") or "UNKNOWN").upper()

        score_parts = [
            _num(item.get("ledger_score")),
            _num(item.get("recall_score")),
            _num(item.get("receipt_score")),
            _num(item.get("confidence_score")),
            _num(item.get("historical_score")),
            _num(item.get("integrity_score")),
        ]
        active_scores = [s for s in score_parts if s > 0]
        historical_score = round(sum(active_scores) / len(active_scores), 2) if active_scores else 0.0

        lineage_payload = {
            "source_id": source_id,
            "source_type": source_type,
            "market": market,
            "historical_score": historical_score,
            "source_lineage": item.get("lineage_hash") or item.get("integrity_hash"),
        }

        return HistoricalManifestEntry(
            manifest_entry_id=_hash(lineage_payload),
            source_id=source_id,
            source_type=source_type,
            market=market,
            historical_score=historical_score,
            manifest_tier=self.classify_tier(historical_score),
            manifest_status=self.classify_status(historical_score),
            lineage_hash=_hash(lineage_payload),
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def build_manifest(self, historical_items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        entries = [self.build_entry(item) for item in historical_items]
        entries.sort(key=lambda e: e.historical_score, reverse=True)

        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        market_counts: Dict[str, int] = {}

        for entry in entries:
            tier_counts[entry.manifest_tier] = tier_counts.get(entry.manifest_tier, 0) + 1
            status_counts[entry.manifest_status] = status_counts.get(entry.manifest_status, 0) + 1
            market_counts[entry.market] = market_counts.get(entry.market, 0) + 1

        top = entries[0] if entries else None
        manifest_id = _hash([entry.__dict__ for entry in entries])

        return {
            "module": self.name,
            "version": self.version,
            "manifest_id": manifest_id,
            "manifest_status": "manifest_built" if entries else "empty_manifest",
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_domains": list(self.supported_domains),
            "entry_count": len(entries),
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "market_counts": market_counts,
            "top_market": top.market if top else None,
            "top_manifest_tier": top.manifest_tier if top else None,
            "summary": {
                "headline": (
                    f"Historical intelligence manifest built; top market is {top.market}."
                    if top else
                    "Historical intelligence manifest is empty."
                ),
                "manifest_id": manifest_id,
                "entry_count": len(entries),
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
                "read_only": True,
            },
            "entries": [entry.__dict__ for entry in entries],
        }


oracle_historical_intelligence_manifest_engine = OracleHistoricalIntelligenceManifestEngine()
