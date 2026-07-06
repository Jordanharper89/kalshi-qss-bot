from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
MOD = PKG / "alpha_integration_test_engine.py"
TEST = ROOT / "test_oi_160_alpha_integration_test_engine.py"
INIT = PKG / "__init__.py"

MODULE = r'''"""
OI-160 — Oracle Alpha Integration Test Engine

Read-only alpha integration test engine for Oracle Historical Intelligence.

Purpose:
- Run institutional integration checks across replay, validation, snapshot,
  receipt, and historical summary outputs.
- Confirm Oracle remains read-only and execution ownership remains Q Series.
- Produce alpha readiness reports before future institutional expansion.

Oracle never executes trades, manages positions, or submits orders.
Execution ownership remains with Q Series.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _stable_text(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}:{_stable_text(value[k])}" for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _hash(value: Any, size: int = 24) -> str:
    return sha256(_stable_text(value).encode("utf-8")).hexdigest()[:size]


@dataclass
class AlphaIntegrationIssue:
    source: str
    severity: str
    code: str
    message: str


@dataclass
class OracleAlphaIntegrationTestEngine:
    name: str = "oracle_alpha_integration_test_engine"
    version: str = "OI-160"
    read_only: bool = True
    execution_allowed: bool = False
    execution_owner: str = "Q Series"
    integration_schema_version: str = "alpha_integration_test_v1"

    def _check_read_only_contract(self, source_name: str, packet: Dict[str, Any]) -> List[AlphaIntegrationIssue]:
        packet = _safe_dict(packet)
        issues: List[AlphaIntegrationIssue] = []

        if packet.get("read_only") is not True:
            issues.append(AlphaIntegrationIssue(
                source=source_name,
                severity="critical",
                code="read_only_contract_failed",
                message=f"{source_name} is not marked read_only=True.",
            ))

        if packet.get("execution_allowed") is not False:
            issues.append(AlphaIntegrationIssue(
                source=source_name,
                severity="critical",
                code="execution_contract_failed",
                message=f"{source_name} allows execution. Oracle must remain read-only.",
            ))

        if packet.get("execution_owner") != "Q Series":
            issues.append(AlphaIntegrationIssue(
                source=source_name,
                severity="critical",
                code="execution_owner_contract_failed",
                message=f"{source_name} execution_owner must be Q Series.",
            ))

        return issues

    def _check_linkage(self, packets: Dict[str, Dict[str, Any]]) -> List[AlphaIntegrationIssue]:
        replay = _safe_dict(packets.get("replay"))
        validation = _safe_dict(packets.get("validation"))
        snapshot = _safe_dict(packets.get("snapshot"))
        receipt = _safe_dict(packets.get("receipt"))
        summary = _safe_dict(packets.get("summary"))

        issues: List[AlphaIntegrationIssue] = []

        replay_id = replay.get("replay_id")
        validation_replay_id = validation.get("source_replay_id")
        snapshot_replay_id = snapshot.get("source_replay_id")
        snapshot_validation_id = snapshot.get("source_validation_id")
        receipt_snapshot_id = receipt.get("source_snapshot_id")
        summary_receipt_id = summary.get("source_receipt_id")
        summary_snapshot_id = summary.get("source_snapshot_id")

        if replay_id and validation_replay_id and replay_id != validation_replay_id:
            issues.append(AlphaIntegrationIssue(
                source="validation",
                severity="critical",
                code="replay_validation_link_mismatch",
                message="Validation source_replay_id does not match replay replay_id.",
            ))

        if replay_id and snapshot_replay_id and replay_id != snapshot_replay_id:
            issues.append(AlphaIntegrationIssue(
                source="snapshot",
                severity="critical",
                code="snapshot_replay_link_mismatch",
                message="Snapshot source_replay_id does not match replay replay_id.",
            ))

        if validation.get("validation_id") and snapshot_validation_id and validation.get("validation_id") != snapshot_validation_id:
            issues.append(AlphaIntegrationIssue(
                source="snapshot",
                severity="critical",
                code="snapshot_validation_link_mismatch",
                message="Snapshot source_validation_id does not match validation validation_id.",
            ))

        if snapshot.get("snapshot_id") and receipt_snapshot_id and snapshot.get("snapshot_id") != receipt_snapshot_id:
            issues.append(AlphaIntegrationIssue(
                source="receipt",
                severity="critical",
                code="receipt_snapshot_link_mismatch",
                message="Receipt source_snapshot_id does not match snapshot snapshot_id.",
            ))

        if receipt.get("receipt_id") and summary_receipt_id and receipt.get("receipt_id") != summary_receipt_id:
            issues.append(AlphaIntegrationIssue(
                source="summary",
                severity="critical",
                code="summary_receipt_link_mismatch",
                message="Summary source_receipt_id does not match receipt receipt_id.",
            ))

        if snapshot.get("snapshot_id") and summary_snapshot_id and snapshot.get("snapshot_id") != summary_snapshot_id:
            issues.append(AlphaIntegrationIssue(
                source="summary",
                severity="warning",
                code="summary_snapshot_link_mismatch",
                message="Summary source_snapshot_id does not match snapshot snapshot_id.",
            ))

        return issues

    def _check_counts(self, packets: Dict[str, Dict[str, Any]]) -> List[AlphaIntegrationIssue]:
        replay = _safe_dict(packets.get("replay"))
        validation = _safe_dict(packets.get("validation"))
        snapshot = _safe_dict(packets.get("snapshot"))
        receipt = _safe_dict(packets.get("receipt"))
        summary = _safe_dict(packets.get("summary"))

        issues: List[AlphaIntegrationIssue] = []

        replay_frames = len(_safe_list(replay.get("frames")))
        snapshot_records = len(_safe_list(snapshot.get("records")))
        receipt_records = len(_safe_list(receipt.get("records")))
        summary_points = len(_safe_list(summary.get("points")))

        if replay.get("frame_count") is not None and int(replay.get("frame_count") or 0) != replay_frames:
            issues.append(AlphaIntegrationIssue(
                source="replay",
                severity="warning",
                code="replay_frame_count_mismatch",
                message="Replay frame_count does not match actual frame length.",
            ))

        if snapshot.get("record_count") is not None and int(snapshot.get("record_count") or 0) != snapshot_records:
            issues.append(AlphaIntegrationIssue(
                source="snapshot",
                severity="warning",
                code="snapshot_record_count_mismatch",
                message="Snapshot record_count does not match actual record length.",
            ))

        if receipt.get("record_count") is not None and int(receipt.get("record_count") or 0) != receipt_records:
            issues.append(AlphaIntegrationIssue(
                source="receipt",
                severity="warning",
                code="receipt_record_count_mismatch",
                message="Receipt record_count does not match actual record length.",
            ))

        if summary.get("point_count") is not None and int(summary.get("point_count") or 0) != summary_points:
            issues.append(AlphaIntegrationIssue(
                source="summary",
                severity="warning",
                code="summary_point_count_mismatch",
                message="Summary point_count does not match actual point length.",
            ))

        if snapshot_records and replay_frames and snapshot_records != replay_frames:
            issues.append(AlphaIntegrationIssue(
                source="snapshot",
                severity="warning",
                code="snapshot_replay_count_gap",
                message="Snapshot record count differs from replay frame count.",
            ))

        if receipt_records and snapshot_records and receipt_records != snapshot_records:
            issues.append(AlphaIntegrationIssue(
                source="receipt",
                severity="warning",
                code="receipt_snapshot_count_gap",
                message="Receipt record count differs from snapshot record count.",
            ))

        if summary_points and receipt_records and summary_points != receipt_records:
            issues.append(AlphaIntegrationIssue(
                source="summary",
                severity="warning",
                code="summary_receipt_count_gap",
                message="Summary point count differs from receipt record count.",
            ))

        return issues

    def run_alpha_test(self, packets: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        packets = _safe_dict(packets)

        required_packets = ["replay", "validation", "snapshot", "receipt", "summary"]
        issues: List[AlphaIntegrationIssue] = []

        for packet_name in required_packets:
            if packet_name not in packets:
                issues.append(AlphaIntegrationIssue(
                    source=packet_name,
                    severity="critical",
                    code="missing_required_packet",
                    message=f"Missing required alpha integration packet: {packet_name}",
                ))

        for packet_name in required_packets:
            if packet_name in packets:
                issues.extend(self._check_read_only_contract(packet_name, _safe_dict(packets.get(packet_name))))

        issues.extend(self._check_linkage(packets))
        issues.extend(self._check_counts(packets))

        critical_count = sum(1 for issue in issues if issue.severity == "critical")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")

        if critical_count:
            alpha_status = "alpha_integration_failed"
        elif warning_count:
            alpha_status = "alpha_integration_ready_with_warnings"
        else:
            alpha_status = "alpha_integration_ready"

        alpha_id = _hash({
            "packets": {
                key: _safe_dict(value).get(f"{key}_id")
                for key, value in packets.items()
            },
            "issues": [issue.__dict__ for issue in issues],
            "status": alpha_status,
        })

        return {
            "module": self.name,
            "version": self.version,
            "integration_schema_version": self.integration_schema_version,
            "alpha_integration_id": alpha_id,
            "alpha_status": alpha_status,
            "tested_at": _utc_now(),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_owner": self.execution_owner,
            "universal_market_model_ready": True,
            "required_packets": required_packets,
            "packet_count": len([p for p in required_packets if p in packets]),
            "issue_count": len(issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "executive_summary": {
                "headline": (
                    "Oracle historical intelligence alpha integration is ready."
                    if alpha_status == "alpha_integration_ready"
                    else f"Oracle alpha integration status: {alpha_status}."
                ),
                "alpha_integration_id": alpha_id,
                "alpha_status": alpha_status,
                "packet_count": len([p for p in required_packets if p in packets]),
                "issue_count": len(issues),
                "critical_count": critical_count,
                "warning_count": warning_count,
                "operator_note": "Oracle remains read-only. Q Series owns execution.",
                "read_only": True,
                "execution_allowed": False,
                "execution_owner": self.execution_owner,
            },
            "issues": [issue.__dict__ for issue in issues],
        }


oracle_alpha_integration_test_engine = OracleAlphaIntegrationTestEngine()
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.alpha_integration_test_engine import (
    oracle_alpha_integration_test_engine,
)


def sample_packets():
    return {
        "replay": {
            "replay_id": "replay-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "frame_count": 1,
            "frames": [{"replay_frame_id": "frame-001"}],
        },
        "validation": {
            "validation_id": "val-001",
            "source_replay_id": "replay-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
        },
        "snapshot": {
            "snapshot_id": "snap-001",
            "source_replay_id": "replay-001",
            "source_validation_id": "val-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "record_count": 1,
            "records": [{"snapshot_record_id": "snap-rec-001"}],
        },
        "receipt": {
            "receipt_id": "receipt-001",
            "source_snapshot_id": "snap-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "record_count": 1,
            "records": [{"receipt_record_id": "receipt-rec-001"}],
        },
        "summary": {
            "historical_summary_id": "summary-001",
            "source_receipt_id": "receipt-001",
            "source_snapshot_id": "snap-001",
            "read_only": True,
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "point_count": 1,
            "points": [{"summary_point_id": "summary-point-001"}],
        },
    }


def test_alpha_integration_ready():
    report = oracle_alpha_integration_test_engine.run_alpha_test(sample_packets())

    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["alpha_status"] == "alpha_integration_ready"
    assert report["issue_count"] == 0
    assert report["packet_count"] == 5


def test_missing_packet_fails():
    packets = sample_packets()
    del packets["summary"]

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert report["critical_count"] == 1
    assert any(issue["code"] == "missing_required_packet" for issue in report["issues"])


def test_execution_violation_fails():
    packets = sample_packets()
    packets["replay"]["execution_allowed"] = True

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert any(issue["code"] == "execution_contract_failed" for issue in report["issues"])


def test_link_mismatch_fails():
    packets = sample_packets()
    packets["snapshot"]["source_validation_id"] = "wrong-val"

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_failed"
    assert any(issue["code"] == "snapshot_validation_link_mismatch" for issue in report["issues"])


def test_count_warning():
    packets = sample_packets()
    packets["summary"]["point_count"] = 2

    report = oracle_alpha_integration_test_engine.run_alpha_test(packets)

    assert report["alpha_status"] == "alpha_integration_ready_with_warnings"
    assert report["warning_count"] == 1
    assert any(issue["code"] == "summary_point_count_mismatch" for issue in report["issues"])


if __name__ == "__main__":
    test_alpha_integration_ready()
    test_missing_packet_fails()
    test_execution_violation_fails()
    test_link_mismatch_fails()
    test_count_warning()
    print("[PASS] OI-160 Oracle Alpha Integration Test Engine")
'''

def update_init():
    INIT.parent.mkdir(parents=True, exist_ok=True)
    content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    line = "from .alpha_integration_test_engine import oracle_alpha_integration_test_engine\n"
    if line not in content:
        content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OI-160 INSTALLER")
    print(" Oracle Alpha Integration Test Engine")
    print("=" * 40)

    PKG.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MODULE, encoding="utf-8")
    TEST.write_text(TEST_CODE, encoding="utf-8")
    update_init()

    print(f"[OK] Wrote {MOD}")
    print(f"[OK] Wrote {TEST}")
    print(f"[OK] Updated {INIT}")
    print("\n[DONE] OI-160 installed")
    print("\nRun:")
    print("py test_oi_160_alpha_integration_test_engine.py")


if __name__ == "__main__":
    main()