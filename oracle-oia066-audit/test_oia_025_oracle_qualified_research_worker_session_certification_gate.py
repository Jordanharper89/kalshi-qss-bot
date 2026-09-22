from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import RANKING_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_tier_assignment_gate import TIER_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_queue_admission_gate import QUEUE_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_work_item_materialization_engine import WORK_ITEM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_manifest_builder import DISPATCH_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_dispatch_claim_gate import CLAIM_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_claim_activation_gate import ACTIVATION_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_manifest_builder import SESSION_POLICY_ID
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_readiness_gate import (
    READINESS_POLICY_ID,
    READINESS_VERIFIED,
    ENTRY_READINESS_VERIFIED,
    stable_hash as readiness_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_worker_session_certification_gate import (
    CERTIFICATION_POLICY_ID,
    ENTRY_CERTIFIED,
    SESSION_CERTIFIED,
    OracleQualifiedResearchWorkerSessionCertificationGate,
    QualifiedResearchWorkerSessionCertificationInvariantError,
    stable_hash,
)

HASHES = [f"{number:064x}" for number in range(1, 16)]


def write_readiness(directory: Path) -> dict:
    prohibited = [
        "create_trading_signal",
        "create_trading_recommendation",
        "publish_operator_alert",
        "handoff_to_qseries_execution",
        "create_market_order",
        "move_funds",
        "mutate_portfolio",
        "mutate_source_corpus",
    ]
    entry_body = {
        "readiness_sequence": 1,
        "session_sequence": 1,
        "activation_sequence": 1,
        "claim_sequence": 1,
        "dispatch_sequence": 1,
        "batch_number": 1,
        "batch_position": 1,
        "work_item_id": "oia019-work-item-test",
        "queue_position": 1,
        "source_rank": 1,
        "dimension": "calibration",
        "key": "market.test",
        "tier": "tier_1",
        "priority_score": "0.990000",
        "research_objective": "Evaluate calibration reliability.",
        "required_operations": ["read_canonical_observations", "write_research_evidence"],
        "prohibited_operations": prohibited,
        "completion_requirements": ["evidence_hash_present", "audit_metadata_present"],
        "readiness_status": ENTRY_READINESS_VERIFIED,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "readiness_policy_id": READINESS_POLICY_ID,
        "source_eligibility_decision_hash": HASHES[0],
        "source_ranking_record_hash": HASHES[1],
        "source_tier_record_hash": HASHES[2],
        "source_queue_record_hash": HASHES[3],
        "source_work_item_hash": HASHES[4],
        "source_dispatch_entry_hash": HASHES[5],
        "source_claim_entry_hash": HASHES[6],
        "source_activation_entry_hash": HASHES[7],
        "source_session_entry_hash": HASHES[8],
    }
    entry = dict(entry_body)
    entry["readiness_entry_hash"] = readiness_stable_hash(entry_body)
    body = {
        "schema_version": "OIA-024",
        "engine_id": "OIA-024",
        "generated_at": "2026-07-21T05:00:00+00:00",
        "readiness_id": "oia024-readiness-test",
        "readiness_status": READINESS_VERIFIED,
        "worker_id": "oracle-worker-test",
        "session_directory": "runtime/test/session",
        "readiness_directory": str(directory),
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "readiness_entry_count": 1,
        "ranking_policy_id": RANKING_POLICY_ID,
        "tier_policy_id": TIER_POLICY_ID,
        "queue_policy_id": QUEUE_POLICY_ID,
        "work_item_policy_id": WORK_ITEM_POLICY_ID,
        "dispatch_policy_id": DISPATCH_POLICY_ID,
        "claim_policy_id": CLAIM_POLICY_ID,
        "activation_policy_id": ACTIVATION_POLICY_ID,
        "session_policy_id": SESSION_POLICY_ID,
        "readiness_policy_id": READINESS_POLICY_ID,
        "entries": [entry],
        "source_session_hash": HASHES[9],
        "source_activation_hash": HASHES[10],
        "source_claim_hash": HASHES[11],
        "source_manifest_hash": HASHES[12],
        "source_batch_hash": HASHES[13],
        "read_only_corpus": True,
        "research_execution_allowed": False,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "readiness_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["readiness_hash"] = readiness_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-025 TEST")
    print(" WORKER SESSION CERTIFICATION GATE")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness_directory = root / "readiness"
        certification_directory = root / "certification"
        source = write_readiness(readiness_directory)
        gate = OracleQualifiedResearchWorkerSessionCertificationGate(
            readiness_directory=readiness_directory,
            certification_directory=certification_directory,
        )
        fixed_time = datetime(2026, 7, 21, 6, 0, tzinfo=timezone.utc)
        first = gate.certify(certified_at=fixed_time, persist=True)
        second = gate.certify(certified_at=fixed_time, persist=False)

        assert first == second
        assert first.schema_version == "OIA-025"
        assert first.engine_id == "OIA-025"
        assert first.certification_status == SESSION_CERTIFIED
        assert first.certification_policy_id == CERTIFICATION_POLICY_ID
        assert first.source_readiness_hash == source["readiness_hash"]
        assert first.certification_entry_count == 1
        assert first.entries[0].certification_status == ENTRY_CERTIFIED
        assert first.entries[0].source_readiness_entry_hash == source["entries"][0]["readiness_entry_hash"]
        assert first.read_only_corpus is True
        for value in (
            first.research_execution_allowed,
            first.execution_allowed,
            first.alerts_allowed,
            first.qseries_handoff_allowed,
            first.signals_allowed,
            first.trading_recommendations_allowed,
            first.source_mutation_allowed,
            first.market_order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        ):
            assert value is False
        body = dict(first.to_dict())
        certification_hash = body.pop("certification_hash")
        assert certification_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("certification_entry_hash")
        assert entry_hash == stable_hash(entry_body)
        assert (certification_directory / "current.json").exists()
        assert list((certification_directory / "certifications").glob("*.json"))
        assert list((certification_directory / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((readiness_directory / "current.json").read_text(encoding="utf-8"))
        tampered["entries"][0]["priority_score"] = "0.000000"
        (readiness_directory / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.certify(certified_at=fixed_time, persist=False)
        except QualifiedResearchWorkerSessionCertificationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-024 readiness was accepted.")

    print("[PASS] Actual OIA-024 readiness contract consumed")
    print("[PASS] Certification and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-024 lineage preserved")
    print("[PASS] Tampered readiness rejected")
    print("[PASS] Atomic certification artifacts persisted")
    print("[PASS] Oracle remained read-only")
    print("[PASS] Research execution remained disabled")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
