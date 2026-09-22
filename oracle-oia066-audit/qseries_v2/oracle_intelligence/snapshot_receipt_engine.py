"""
OI-158 — Oracle Snapshot Receipt Engine

Read-only receipt engine for Oracle Historical Snapshot output.

Purpose:
- Confirm historical snapshot packets with institutional receipt records.
- Preserve snapshot lineage, validation status, receipt status, and audit context.
- Create immutable receipt summaries for downstream historical intelligence summaries.

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
class SnapshotReceiptRecord:
    receipt_record_id: str
    source_snapshot_record_id: str
    source_id: str
    market: str
    receipt_score: float
    receipt_tier: str
    receipt_status: str
    snapshot_status: str
    snapshot_tier: str
    lineage_hash: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleSnapshotReceiptEngine:
    name: str = "oracle_snapshot_receipt_engine"
    version: str = "OI-158"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    receipt_schema_version: str = "snapshot_receipt_v1"
    supported_receipt_domains: List[str] = field(default_factory=lambda: [
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

    def classify_tier(self, score: float, snapshot_status: str) -> str:
        if "blocked" in snapshot_status or "invalid" in snapshot_status:
            return "invalid_snapshot_receipt"
        if score >= 90:
            return "institutional_snapshot_receipt"
        if score >= 75:
            return "validated_snapshot_receipt"
        if score >= 60:
            return "review_snapshot_receipt"
        return "low_signal_snapshot_receipt"

    def classify_status(self, score: float, snapshot_status: str) -> str:
        if "blocked" in snapshot_status or "invalid" in snapshot_status:
            return "receipt_blocked_by_snapshot"
        if score >= 90:
            return "confirmed_institutional_receipt"
        if score >= 75:
            return "confirmed_receipt"
        if score >= 60:
            return "receipt_review_required"
        return "insufficient_receipt_signal"

    def build_receipt_record(self, record: Dict[str, Any]) -> SnapshotReceiptRecord:
        record = _safe_dict(record)

        source_snapshot_record_id = str(record.get("snapshot_record_id") or _hash(record, 12))
        source_id = str(record.get("source_id") or "unknown-source")
        market = str(record.get("market") or "UNKNOWN").upper()
        score = round(_num(record.get("snapshot_score")), 2)
        snapshot_status = str(record.get("snapshot_status") or "unknown_snapshot_status")
        snapshot_tier = str(record.get("snapshot_tier") or "unknown_snapshot_tier")

        lineage_payload = {
            "source_snapshot_record_id": source_snapshot_record_id,
            "source_id": source_id,
            "market": market,
            "score": score,
            "snapshot_status": snapshot_status,
            "snapshot_tier": snapshot_tier,
            "lineage": record.get("lineage_hash"),
        }

        return SnapshotReceiptRecord(
            receipt_record_id=_hash(lineage_payload),
            source_snapshot_record_id=source_snapshot_record_id,
            source_id=source_id,
            market=market,
            receipt_score=score,
            receipt_tier=self.classify_tier(score, snapshot_status),
            receipt_status=self.classify_status(score, snapshot_status),
            snapshot_status=snapshot_status,
            snapshot_tier=snapshot_tier,
            lineage_hash=_hash(lineage_payload),
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def create_receipt(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = _safe_dict(snapshot)
        records = _safe_list(snapshot.get("records"))

        receipt_records = [self.build_receipt_record(record) for record in records]
        receipt_records.sort(key=lambda r: r.receipt_score, reverse=True)

        market_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for record in receipt_records:
            market_counts[record.market] = market_counts.get(record.market, 0) + 1
            tier_counts[record.receipt_tier] = tier_counts.get(record.receipt_tier, 0) + 1
            status_counts[record.receipt_status] = status_counts.get(record.receipt_status, 0) + 1

        top = receipt_records[0] if receipt_records else None

        blocked_count = sum(
            1 for record in receipt_records
            if record.receipt_status == "receipt_blocked_by_snapshot"
        )

        receipt_payload = {
            "source_snapshot_id": snapshot.get("snapshot_id"),
            "source_snapshot_status": snapshot.get("snapshot_status"),
            "record_count": len(receipt_records),
            "blocked_count": blocked_count,
            "records": [record.__dict__ for record in receipt_records],
        }
        receipt_id = _hash(receipt_payload)

        if not receipt_records:
            receipt_status = "empty_snapshot_receipt"
        elif blocked_count:
            receipt_status = "snapshot_receipt_created_with_blocks"
        else:
            receipt_status = "snapshot_receipt_confirmed"

        return {
            "module": self.name,
            "version": self.version,
            "receipt_schema_version": self.receipt_schema_version,
            "receipt_id": receipt_id,
            "receipt_status": receipt_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_receipt_domains": list(self.supported_receipt_domains),
            "source_snapshot_id": snapshot.get("snapshot_id"),
            "source_snapshot_status": snapshot.get("snapshot_status"),
            "source_validation_status": snapshot.get("source_validation_status"),
            "record_count": len(receipt_records),
            "blocked_count": blocked_count,
            "market_counts": market_counts,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "top_market": top.market if top else None,
            "top_receipt_tier": top.receipt_tier if top else None,
            "summary": {
                "headline": (
                    f"Snapshot receipt confirmed; top receipt market is {top.market}."
                    if top and not blocked_count else
                    f"Snapshot receipt created with {blocked_count} blocked record(s)."
                    if receipt_records else
                    "Snapshot receipt is empty."
                ),
                "receipt_id": receipt_id,
                "source_snapshot_id": snapshot.get("snapshot_id"),
                "record_count": len(receipt_records),
                "blocked_count": blocked_count,
                "top_market": top.market if top else None,
                "top_receipt_tier": top.receipt_tier if top else None,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in receipt_records],
        }

    def explain_receipt_record(self, receipt: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        receipt = _safe_dict(receipt)
        records = _safe_list(receipt.get("records"))

        for record in records:
            record = _safe_dict(record)
            if str(record.get("source_id")) == str(source_id):
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "receipt_id": receipt.get("receipt_id"),
                    "source_id": source_id,
                    "explanation": (
                        f"{record.get('market')} snapshot receipt confirmed at score "
                        f"{record.get('receipt_score')} with status {record.get('receipt_status')}. "
                        "Oracle receipt is read-only; Q Series owns execution."
                    ),
                    "record": record,
                    "read_only": True,
                    "execution_allowed": False,
                    "execution_owner": self.execution_owner,
                }

        return {
            "module": self.name,
            "version": self.version,
            "found": False,
            "receipt_id": receipt.get("receipt_id"),
            "source_id": source_id,
            "explanation": "No snapshot receipt record found for requested source_id.",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_snapshot_receipt_engine = OracleSnapshotReceiptEngine()
