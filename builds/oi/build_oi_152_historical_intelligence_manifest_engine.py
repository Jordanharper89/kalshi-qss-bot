from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "historical_intelligence_manifest_engine.py"
TEST = ROOT / "test_oi_152_historical_intelligence_manifest_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
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
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.historical_intelligence_manifest_engine import (
    oracle_historical_intelligence_manifest_engine,
)


def test_manifest_builds_read_only():
    items = [
        {
            "ledger_id": "ledger-001",
            "record_type": "recall_ledger_entry",
            "market": "CRYPTO",
            "ledger_score": 89.92,
            "recall_score": 100.0,
            "receipt_score": 94.0,
            "confidence_score": 91.0,
            "lineage_hash": "abc123",
        }
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["read_only"] is True
    assert manifest["execution_allowed"] is False
    assert manifest["execution_owner"] == "Q Series"
    assert manifest["entry_count"] == 1
    assert manifest["top_market"] == "CRYPTO"
    assert manifest["entries"][0]["read_only"] is True
    assert manifest["entries"][0]["execution_allowed"] is False


def test_manifest_sorts_by_score():
    items = [
        {"source_id": "low", "market": "WEATHER", "historical_score": 62},
        {"source_id": "high", "market": "CRYPTO", "historical_score": 95},
        {"source_id": "mid", "market": "STOCKS", "historical_score": 78},
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["entries"][0]["source_id"] == "high"
    assert manifest["entries"][0]["manifest_tier"] == "institutional_historical_manifest"
    assert manifest["entries"][1]["source_id"] == "mid"
    assert manifest["entries"][2]["source_id"] == "low"


def test_manifest_counts_markets_and_statuses():
    items = [
        {"source_id": "a", "market": "crypto", "historical_score": 95},
        {"source_id": "b", "market": "crypto", "historical_score": 81},
        {"source_id": "c", "market": "forex", "historical_score": 55},
    ]

    manifest = oracle_historical_intelligence_manifest_engine.build_manifest(items)

    assert manifest["market_counts"]["CRYPTO"] == 2
    assert manifest["market_counts"]["FOREX"] == 1
    assert manifest["status_counts"]["executive_ready_manifest"] == 1
    assert manifest["status_counts"]["validated_manifest"] == 1
    assert manifest["status_counts"]["insufficient_manifest_quality"] == 1


def test_empty_manifest():
    manifest = oracle_historical_intelligence_manifest_engine.build_manifest([])

    assert manifest["manifest_status"] == "empty_manifest"
    assert manifest["entry_count"] == 0
    assert manifest["entries"] == []
    assert manifest["summary"]["read_only"] is True


if __name__ == "__main__":
    test_manifest_builds_read_only()
    test_manifest_sorts_by_score()
    test_manifest_counts_markets_and_statuses()
    test_empty_manifest()
    print("[PASS] OI-152 Oracle Historical Intelligence Manifest Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .historical_intelligence_manifest_engine import oracle_historical_intelligence_manifest_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-152 INSTALLER")
    print(" Oracle Historical Intelligence Manifest Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-152 installed")
    print("\nRun:")
    print("py test_oi_152_historical_intelligence_manifest_engine.py")


if __name__ == "__main__":
    main()