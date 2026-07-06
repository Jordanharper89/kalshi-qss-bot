from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "historical_snapshot_engine.py"
TEST = ROOT / "test_oi_157_historical_snapshot_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-157 — Oracle Historical Snapshot Engine

Read-only snapshot engine for validated Oracle historical replay output.

Purpose:
- Convert replay validation output into immutable historical snapshot packets.
- Preserve replay lineage, validation status, institutional metadata, and audit context.
- Prepare snapshot records for downstream receipt and summary engines.

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
class HistoricalSnapshotRecord:
    snapshot_record_id: str
    source_frame_id: str
    source_id: str
    market: str
    snapshot_score: float
    snapshot_tier: str
    snapshot_status: str
    replay_rank: int
    lineage_hash: str
    validation_status: str
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    read_only: bool = True


@dataclass
class OracleHistoricalSnapshotEngine:
    name: str = "oracle_historical_snapshot_engine"
    version: str = "OI-157"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    snapshot_schema_version: str = "historical_snapshot_v1"
    supported_snapshot_domains: List[str] = field(default_factory=lambda: [
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

    def classify_tier(self, score: float, validation_status: str) -> str:
        if validation_status == "failed":
            return "invalid_snapshot"
        if score >= 90:
            return "institutional_snapshot"
        if score >= 75:
            return "validated_snapshot"
        if score >= 60:
            return "review_snapshot"
        return "low_signal_snapshot"

    def classify_status(self, score: float, validation_status: str) -> str:
        if validation_status == "failed":
            return "snapshot_blocked_by_validation"
        if validation_status == "validated_with_warnings":
            return "snapshot_ready_with_warnings"
        if score >= 90:
            return "executive_snapshot_ready"
        if score >= 75:
            return "snapshot_ready"
        if score >= 60:
            return "snapshot_review_required"
        return "insufficient_snapshot_signal"

    def build_record(self, frame: Dict[str, Any], validation_status: str) -> HistoricalSnapshotRecord:
        frame = _safe_dict(frame)
        score = round(_num(frame.get("replay_score")), 2)
        source_frame_id = str(frame.get("replay_frame_id") or _hash(frame, 12))
        source_id = str(frame.get("source_id") or "unknown-source")
        market = str(frame.get("market") or "UNKNOWN").upper()

        lineage_payload = {
            "source_frame_id": source_frame_id,
            "source_id": source_id,
            "market": market,
            "score": score,
            "replay_rank": frame.get("replay_rank"),
            "lineage": frame.get("lineage_hash"),
            "validation_status": validation_status,
        }

        return HistoricalSnapshotRecord(
            snapshot_record_id=_hash(lineage_payload),
            source_frame_id=source_frame_id,
            source_id=source_id,
            market=market,
            snapshot_score=score,
            snapshot_tier=self.classify_tier(score, validation_status),
            snapshot_status=self.classify_status(score, validation_status),
            replay_rank=int(_num(frame.get("replay_rank"), 0)),
            lineage_hash=_hash(lineage_payload),
            validation_status=validation_status,
            execution_allowed=False,
            execution_owner=self.execution_owner,
            read_only=True,
        )

    def create_snapshot(self, replay: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        replay = _safe_dict(replay)
        validation = _safe_dict(validation)
        frames = _safe_list(replay.get("frames"))

        validation_status = str(validation.get("validation_status") or "unknown_validation")
        records = [self.build_record(frame, validation_status) for frame in frames]
        records.sort(key=lambda r: (r.replay_rank, -r.snapshot_score))

        market_counts: Dict[str, int] = {}
        tier_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for record in records:
            market_counts[record.market] = market_counts.get(record.market, 0) + 1
            tier_counts[record.snapshot_tier] = tier_counts.get(record.snapshot_tier, 0) + 1
            status_counts[record.snapshot_status] = status_counts.get(record.snapshot_status, 0) + 1

        top = records[0] if records else None

        snapshot_payload = {
            "source_replay_id": replay.get("replay_id"),
            "source_validation_id": validation.get("validation_id"),
            "validation_status": validation_status,
            "record_count": len(records),
            "records": [record.__dict__ for record in records],
        }
        snapshot_id = _hash(snapshot_payload)

        if validation_status == "failed":
            snapshot_status = "snapshot_created_invalid_validation"
        elif records:
            snapshot_status = "snapshot_created"
        else:
            snapshot_status = "empty_snapshot"

        return {
            "module": self.name,
            "version": self.version,
            "snapshot_schema_version": self.snapshot_schema_version,
            "snapshot_id": snapshot_id,
            "snapshot_status": snapshot_status,
            "created_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "supported_snapshot_domains": list(self.supported_snapshot_domains),
            "source_replay_id": replay.get("replay_id"),
            "source_validation_id": validation.get("validation_id"),
            "source_validation_status": validation_status,
            "source_issue_count": validation.get("issue_count", 0),
            "record_count": len(records),
            "market_counts": market_counts,
            "tier_counts": tier_counts,
            "status_counts": status_counts,
            "top_market": top.market if top else None,
            "top_snapshot_tier": top.snapshot_tier if top else None,
            "summary": {
                "headline": (
                    f"Historical snapshot created; top snapshot market is {top.market}."
                    if top else
                    "Historical snapshot created; no snapshot records available."
                ),
                "snapshot_id": snapshot_id,
                "source_replay_id": replay.get("replay_id"),
                "source_validation_id": validation.get("validation_id"),
                "source_validation_status": validation_status,
                "record_count": len(records),
                "top_market": top.market if top else None,
                "top_snapshot_tier": top.snapshot_tier if top else None,
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "records": [record.__dict__ for record in records],
        }

    def explain_snapshot_record(self, snapshot: Dict[str, Any], source_id: str) -> Dict[str, Any]:
        snapshot = _safe_dict(snapshot)
        records = _safe_list(snapshot.get("records"))

        for record in records:
            record = _safe_dict(record)
            if str(record.get("source_id")) == str(source_id):
                return {
                    "module": self.name,
                    "version": self.version,
                    "found": True,
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "source_id": source_id,
                    "explanation": (
                        f"{record.get('market')} snapshot record preserved at score "
                        f"{record.get('snapshot_score')} with status {record.get('snapshot_status')}. "
                        "Oracle snapshot is read-only; Q Series owns execution."
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
            "snapshot_id": snapshot.get("snapshot_id"),
            "source_id": source_id,
            "explanation": "No historical snapshot record found for requested source_id.",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": self.execution_owner,
        }


oracle_historical_snapshot_engine = OracleHistoricalSnapshotEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.historical_snapshot_engine import (
    oracle_historical_snapshot_engine,
)


def sample_replay():
    return {
        "replay_id": "replay-001",
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "frame_count": 2,
        "frames": [
            {
                "replay_frame_id": "frame-001",
                "replay_rank": 1,
                "source_id": "crypto-alpha",
                "source_type": "memory_index_record",
                "market": "CRYPTO",
                "replay_score": 96.0,
                "replay_tier": "institutional_replay",
                "replay_status": "executive_replay_ready",
                "lineage_hash": "abc123",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
            {
                "replay_frame_id": "frame-002",
                "replay_rank": 2,
                "source_id": "stocks-beta",
                "source_type": "memory_index_record",
                "market": "STOCKS",
                "replay_score": 78.0,
                "replay_tier": "validated_replay",
                "replay_status": "validated_replay_ready",
                "lineage_hash": "def456",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": "Q Series",
            },
        ],
    }


def sample_validation(status="validated"):
    return {
        "validation_id": "val-001",
        "source_replay_id": "replay-001",
        "validation_status": status,
        "issue_count": 0,
        "critical_count": 0,
        "warning_count": 0,
        "read_only": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
    }


def test_snapshot_created_from_validated_replay():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated"),
    )

    assert snapshot["read_only"] is True
    assert snapshot["execution_allowed"] is False
    assert snapshot["execution_owner"] == "Q Series"
    assert snapshot["snapshot_status"] == "snapshot_created"
    assert snapshot["record_count"] == 2
    assert snapshot["top_market"] == "CRYPTO"
    assert snapshot["records"][0]["source_id"] == "crypto-alpha"
    assert snapshot["records"][0]["snapshot_tier"] == "institutional_snapshot"


def test_snapshot_with_validation_warnings():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated_with_warnings"),
    )

    assert snapshot["source_validation_status"] == "validated_with_warnings"
    assert snapshot["records"][0]["snapshot_status"] == "snapshot_ready_with_warnings"
    assert snapshot["records"][1]["snapshot_status"] == "snapshot_ready_with_warnings"


def test_failed_validation_blocks_snapshot_tier():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("failed"),
    )

    assert snapshot["snapshot_status"] == "snapshot_created_invalid_validation"
    assert snapshot["records"][0]["snapshot_tier"] == "invalid_snapshot"
    assert snapshot["records"][0]["snapshot_status"] == "snapshot_blocked_by_validation"


def test_explain_snapshot_record():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        sample_replay(),
        sample_validation("validated"),
    )

    explanation = oracle_historical_snapshot_engine.explain_snapshot_record(snapshot, "crypto-alpha")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["record"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_snapshot():
    snapshot = oracle_historical_snapshot_engine.create_snapshot(
        {"replay_id": "empty", "frames": []},
        sample_validation("validated"),
    )

    assert snapshot["snapshot_status"] == "empty_snapshot"
    assert snapshot["record_count"] == 0
    assert snapshot["records"] == []
    assert snapshot["summary"]["read_only"] is True


if __name__ == "__main__":
    test_snapshot_created_from_validated_replay()
    test_snapshot_with_validation_warnings()
    test_failed_validation_blocks_snapshot_tier()
    test_explain_snapshot_record()
    test_empty_snapshot()
    print("[PASS] OI-157 Oracle Historical Snapshot Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .historical_snapshot_engine import oracle_historical_snapshot_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-157 INSTALLER")
    print(" Oracle Historical Snapshot Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-157 installed")
    print("\nRun:")
    print("py test_oi_157_historical_snapshot_engine.py")


if __name__ == "__main__":
    main()