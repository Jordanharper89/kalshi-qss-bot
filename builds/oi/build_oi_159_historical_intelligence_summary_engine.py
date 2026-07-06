from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "historical_intelligence_summary_engine.py"
TEST = ROOT / "test_oi_159_historical_intelligence_summary_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-159 — Oracle Historical Intelligence Summary Engine

Read-only executive summary engine for Oracle historical intelligence receipts.

Purpose:
- Summarize historical snapshot receipts into institutional intelligence packets.
- Preserve snapshot, replay, validation, receipt, market, and tier context.
- Produce executive-ready historical intelligence summaries for alpha integration tests.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


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
class HistoricalSummaryPoint:
    summary_point_id: str
    source_id: str
    market: str
    summary_score: float
    summary_tier: str
    summary_status: str
    receipt_status: str
    receipt_tier: str
    narrative: str
    lineage_hash: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleHistoricalIntelligenceSummaryEngine:
    name: str = "oracle_historical_intelligence_summary_engine"
    version: str = "OI-159"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    summary_schema_version: str = "historical_intelligence_summary_v1"
    supported_summary_domains: List[str] = field(default_factory=lambda: [
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

    def classify_tier(self, score: float, receipt_status: str) -> str:
        if "blocked" in receipt_status or "invalid" in receipt_status:
            return "blocked_historical_summary"
        if score >= 90:
            return "institutional_historical_summary"
        if score >= 75:
            return "validated_historical_summary"
        if score >= 60:
            return "review_historical_summary"
        return "low_signal_historical_summary"

    def classify_status(self, score: float, receipt_status: str) -> str:
        if "blocked" in receipt_status or "invalid" in receipt_status:
            return "summary_blocked_by_receipt"
        if score >= 90:
            return "executive_ready_summary"
        if score >= 75:
            return "validated_summary"
        if score >= 60:
            return "summary_review_required"
        return "insufficient_summary_signal"

    def build_point(self, record: Dict[str, Any]) -> HistoricalSummaryPoint:
        record = _safe_dict(record)

        source_id = str(record.get("source_id") or "unknown-source")
        market = str(record.get("market") or "UNKNOWN").upper()
        score = round(_num(record.get("receipt_score")), 2)
        receipt_status = str(record.get("receipt_status") or "unknown_receipt_status")
        receipt_tier = str(record.get("receipt_tier") or "unknown_receipt_tier")

        tier = self.classify_tier(score, receipt_status)
        status = self.classify_status(score, receipt_status)

        lineage_payload = {
            "source_id": source_id,
            "market": market,
            "score": score,
            "receipt_status": receipt_status,
            "receipt_tier": receipt_tier,
            "lineage": record.get("lineage_hash") or record.get("receipt_record_id"),
        }

        return HistoricalSummaryPoint(
            summary_point_id=_hash(lineage_payload),
            source_id=source_id,
            market=market,
            summary_score=score,
            summary_tier=tier,
            summary_status=status,
            receipt_status=receipt_status,
            receipt_tier=receipt_tier,
            narrative=(
                f"{market} historical intelligence summarized at score {score}. "
                f"Receipt status: {receipt_status}. "
                "Oracle summary is read-only; Q Series owns execution."
            ),
            lineage_hash=_hash(lineage_payload),
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def summarize(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        receipt = _safe_dict(receipt)
        records = _safe_list(receipt.get("records"))

        points = [self.build_point(record) for record in records]
        points.sort(key=lambda p: p.summary_score, reverse=True)

        market_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        total_score = 0.0
        blocked_count = 0

        for point in points:
            market_counts[point.market] = market_counts.get(point.market, 0) + 1
            tier_counts[point.summary_tier] = tier_counts.get(point.summary_tier, 0) + 1
            status_counts[point.summary_status] = status_counts.get(point.summary_status, 0) + 1
            total_score += point.summary_score
            if point.summary_status == "summary_blocked_by_receipt":
                blocked_count += 1

        average_score = round(total_score / len(points), 2) if points else 0.0
        top = points[0] if points else None

        summary_payload = {
            "source_receipt_id": receipt.get("receipt_id"),
            "source_snapshot_id": receipt.get("source_snapshot_id"),
            "receipt_status": receipt.get("receipt_status"),
            "average_score": average_score,
            "blocked_count": blocked_count,
            "points": [point.__dict__ for point in points],
        }
        summary_id = _hash(summary_payload)

        if not points:
            summary_status = "empty_historical_summary"
        elif blocked_count:
            summary_status = "historical_summary_created_with_blocks"
        elif average_score >= 90:
            summary_status = "executive_historical_summary_ready"
        elif average_score >= 75:
            summary_status = "validated_historical_summary_ready"
        else:
            summary_status = "historical_summary_review_required"

        return {
            "module": self.name,
            "version": self.version,
            "summary_schema_version": self.summary_schema_version,
            "historical_summary_id": summary_id,
            "historical_summary_status": summary_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_summary_domains": list(self.supported_summary_domains),
            "source_receipt_id": receipt.get("receipt_id"),
            "source_receipt_status": receipt.get("receipt_status"),
            "source_snapshot_id": receipt.get("source_snapshot_id"),
            "source_validation_status": receipt.get("source_validation_status"),
            "point_count": len(points),
            "blocked_count": blocked_count,
            "average_summary_score": average_score,
            "market_counts": market_counts,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "top_market": top.market if top else None,
            "top_summary_tier": top.summary_tier if top else None,
            "executive_summary": {
                "headline": (
                    f"Historical intelligence summary ready; top market is {top.market}."
                    if top and not blocked_count else
                    f"Historical intelligence summary created with {blocked_count} blocked point(s)."
                    if points else
                    "Historical intelligence summary is empty."
                ),
                "historical_summary_id": summary_id,
                "source_receipt_id": receipt.get("receipt_id"),
                "source_snapshot_id": receipt.get("source_snapshot_id"),
                "point_count": len(points),
                "blocked_count": blocked_count,
                "average_summary_score": average_score,
                "top_market": top.market if top else None,
                "top_summary_tier": top.summary_tier if top else None,
                "operator_note": "Oracle historical summary is intelligence-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "points": [point.__dict__ for point in points],
        }

    def explain_summary_point(self, summary: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        summary = _safe_dict(summary)
        points = _safe_list(summary.get("points"))

        for point in points:
            point = _safe_dict(point)
            if str(point.get("source_id")) == str(source_id):
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "historical_summary_id": summary.get("historical_summary_id"),
                    "source_id": source_id,
                    "explanation": point.get("narrative"),
                    "point": point,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "historical_summary_id": summary.get("historical_summary_id"),
            "source_id": source_id,
            "explanation": "No historical summary point found for requested source_id.",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_historical_intelligence_summary_engine = OracleHistoricalIntelligenceSummaryEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.historical_intelligence_summary_engine import (
    oracle_historical_intelligence_summary_engine,
)


def sample_receipt():
    return {
        "receipt_id": "receipt-001",
        "receipt_status": "snapshot_receipt_confirmed",
        "source_snapshot_id": "snap-001",
        "source_validation_status": "validated",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "records": [
            {
                "receipt_record_id": "rec-001",
                "source_snapshot_record_id": "snap-rec-001",
                "source_id": "crypto-alpha",
                "market": "CRYPTO",
                "receipt_score": 96.0,
                "receipt_tier": "institutional_snapshot_receipt",
                "receipt_status": "confirmed_institutional_receipt",
                "snapshot_status": "executive_snapshot_ready",
                "snapshot_tier": "institutional_snapshot",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "receipt_record_id": "rec-002",
                "source_snapshot_record_id": "snap-rec-002",
                "source_id": "stocks-beta",
                "market": "STOCKS",
                "receipt_score": 78.0,
                "receipt_tier": "validated_snapshot_receipt",
                "receipt_status": "confirmed_receipt",
                "snapshot_status": "snapshot_ready",
                "snapshot_tier": "validated_snapshot",
                "lineage_hash": "def456",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def test_summary_created_from_receipt():
    summary = oracle_historical_intelligence_summary_engine.summarize(sample_receipt())

    assert summary["read_only"] is True
    assert summary["execution_allowed"] is False
    assert summary["execution_owner"] == "Q Series"
    assert summary["point_count"] == 2
    assert summary["top_market"] == "CRYPTO"
    assert summary["points"][0]["source_id"] == "crypto-alpha"
    assert summary["points"][0]["summary_tier"] == "institutional_historical_summary"
    assert summary["average_summary_score"] == 87.0


def test_summary_with_blocked_receipt():
    receipt = sample_receipt()
    receipt["records"][0]["receipt_status"] = "receipt_blocked_by_snapshot"
    receipt["records"][0]["receipt_tier"] = "invalid_snapshot_receipt"

    summary = oracle_historical_intelligence_summary_engine.summarize(receipt)

    assert summary["historical_summary_status"] == "historical_summary_created_with_blocks"
    assert summary["blocked_count"] == 1
    assert summary["points"][0]["summary_tier"] == "blocked_historical_summary"
    assert summary["points"][0]["summary_status"] == "summary_blocked_by_receipt"


def test_explain_summary_point():
    summary = oracle_historical_intelligence_summary_engine.summarize(sample_receipt())

    explanation = oracle_historical_intelligence_summary_engine.explain_summary_point(
        summary,
        "crypto-alpha",
    )

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["point"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_summary():
    summary = oracle_historical_intelligence_summary_engine.summarize({
        "receipt_id": "empty",
        "receipt_status": "empty_snapshot_receipt",
        "records": [],
    })

    assert summary["historical_summary_status"] == "empty_historical_summary"
    assert summary["point_count"] == 0
    assert summary["points"] == []
    assert summary["executive_summary"]["read_only"] is True


if __name__ == "__main__":
    test_summary_created_from_receipt()
    test_summary_with_blocked_receipt()
    test_explain_summary_point()
    test_empty_summary()
    print("[PASS] OI-159 Oracle Historical Intelligence Summary Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .historical_intelligence_summary_engine import oracle_historical_intelligence_summary_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-159 INSTALLER")
    print(" Oracle Historical Intelligence Summary Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-159 installed")
    print("\nRun:")
    print("py test_oi_159_historical_intelligence_summary_engine.py")


if __name__ == "__main__":
    main()