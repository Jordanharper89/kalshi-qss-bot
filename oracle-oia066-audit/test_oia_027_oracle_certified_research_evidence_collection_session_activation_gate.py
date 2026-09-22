from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_manifest_builder import (
    EVIDENCE_ENTRY_AUTHORIZED,
    EVIDENCE_MANIFEST_ISSUED,
    EVIDENCE_MANIFEST_POLICY_ID,
    stable_hash as manifest_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_session_activation_gate import (
    EVIDENCE_ENTRY_ACTIVE,
    EVIDENCE_SESSION_ACTIVE,
    EVIDENCE_SESSION_POLICY_ID,
    CertifiedResearchEvidenceCollectionSessionActivationInvariantError,
    OracleCertifiedResearchEvidenceCollectionSessionActivationGate,
    stable_hash,
)

HASHES = tuple(f"{index:064x}" for index in range(1, 20))


def write_manifest(directory: Path) -> dict:
    entry_body = {
        "evidence_sequence": 1,
        "certification_sequence": 1,
        "readiness_sequence": 1,
        "session_sequence": 1,
        "activation_sequence": 1,
        "claim_sequence": 1,
        "dispatch_sequence": 1,
        "batch_number": 1,
        "batch_position": 1,
        "work_item_id": "work-item-test",
        "worker_id": "oracle-worker-test",
        "dimension": "calibration",
        "key": "market-test",
        "tier": "tier_a",
        "priority_score": "0.900000",
        "research_objective": "Collect bounded evidence.",
        "evidence_scope_id": "evidence-scope-test",
        "authorized_evidence_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": [
            "create_forecast", "create_signal", "create_alert", "handoff_to_qseries",
            "invoke_execution_adapter", "create_market_order", "move_funds", "mutate_portfolio",
        ],
        "completion_requirements": ["evidence_hash_verified"],
        "evidence_status": EVIDENCE_ENTRY_AUTHORIZED,
        "ranking_policy_id": "ranking-policy-test",
        "tier_policy_id": "tier-policy-test",
        "queue_policy_id": "queue-policy-test",
        "work_item_policy_id": "work-item-policy-test",
        "dispatch_policy_id": "dispatch-policy-test",
        "claim_policy_id": "claim-policy-test",
        "activation_policy_id": "activation-policy-test",
        "session_policy_id": "session-policy-test",
        "readiness_policy_id": "readiness-policy-test",
        "certification_policy_id": "certification-policy-test",
        "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
        "source_eligibility_decision_hash": HASHES[0],
        "source_ranking_record_hash": HASHES[1],
        "source_tier_record_hash": HASHES[2],
        "source_queue_record_hash": HASHES[3],
        "source_work_item_hash": HASHES[4],
        "source_dispatch_entry_hash": HASHES[5],
        "source_claim_entry_hash": HASHES[6],
        "source_activation_entry_hash": HASHES[7],
        "source_session_entry_hash": HASHES[8],
        "source_readiness_entry_hash": HASHES[9],
        "source_certification_entry_hash": HASHES[10],
    }
    entry = dict(entry_body)
    entry["evidence_entry_hash"] = manifest_stable_hash(entry_body)
    body = {
        "schema_version": "OIA-026",
        "engine_id": "OIA-026",
        "generated_at": "2026-07-21T08:00:00+00:00",
        "evidence_manifest_id": "oia026-evidence-manifest-test",
        "manifest_status": EVIDENCE_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
        "certification_directory": "runtime/test/certification",
        "evidence_manifest_directory": str(directory),
        "source_certification_id": "oia025-certification-test",
        "source_readiness_id": "oia024-readiness-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "evidence_entry_count": 1,
        "ranking_policy_id": "ranking-policy-test",
        "tier_policy_id": "tier-policy-test",
        "queue_policy_id": "queue-policy-test",
        "work_item_policy_id": "work-item-policy-test",
        "dispatch_policy_id": "dispatch-policy-test",
        "claim_policy_id": "claim-policy-test",
        "activation_policy_id": "activation-policy-test",
        "session_policy_id": "session-policy-test",
        "readiness_policy_id": "readiness-policy-test",
        "certification_policy_id": "certification-policy-test",
        "evidence_manifest_policy_id": EVIDENCE_MANIFEST_POLICY_ID,
        "entries": [entry],
        "source_certification_hash": HASHES[11],
        "source_readiness_hash": HASHES[12],
        "source_session_hash": HASHES[13],
        "source_activation_hash": HASHES[14],
        "source_claim_hash": HASHES[15],
        "source_dispatch_manifest_hash": HASHES[16],
        "source_batch_hash": HASHES[17],
        "read_only_corpus": True,
        "research_execution_allowed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "evidence_manifest_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_manifest_hash"] = manifest_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-027 TEST")
    print(" EVIDENCE COLLECTION SESSION ACTIVATION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        manifest_directory = root / "manifest"
        session_directory = root / "session"
        source = write_manifest(manifest_directory)
        gate = OracleCertifiedResearchEvidenceCollectionSessionActivationGate(
            evidence_manifest_directory=manifest_directory,
            evidence_session_directory=session_directory,
        )
        fixed = datetime(2026, 7, 21, 9, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-027"
        assert first.engine_id == "OIA-027"
        assert first.session_status == EVIDENCE_SESSION_ACTIVE
        assert first.evidence_session_policy_id == EVIDENCE_SESSION_POLICY_ID
        assert first.source_evidence_manifest_hash == source["evidence_manifest_hash"]
        assert first.session_entry_count == 1
        assert first.entries[0].session_status == EVIDENCE_ENTRY_ACTIVE
        assert first.entries[0].source_evidence_entry_hash == source["entries"][0]["evidence_entry_hash"]
        assert first.evidence_collection_allowed is True
        assert first.read_only_corpus is True
        for value in (
            first.research_execution_allowed, first.analytic_conclusion_allowed,
            first.forecast_creation_allowed, first.signals_allowed, first.alerts_allowed,
            first.qseries_handoff_allowed, first.execution_allowed,
            first.trading_recommendations_allowed, first.source_mutation_allowed,
            first.market_order_creation_allowed, first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        ):
            assert value is False
        body = dict(first.to_dict())
        session_hash = body.pop("evidence_session_hash")
        assert session_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("session_entry_hash")
        assert entry_hash == stable_hash(entry_body)
        assert (session_directory / "current.json").exists()
        assert list((session_directory / "sessions").glob("*.json"))
        assert list((session_directory / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((manifest_directory / "current.json").read_text(encoding="utf-8"))
        tampered["entries"][0]["priority_score"] = "0.000000"
        (manifest_directory / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionSessionActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-026 evidence manifest was accepted.")

    print("[PASS] Actual OIA-026 evidence manifest contract consumed")
    print("[PASS] Evidence session and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-026 lineage preserved")
    print("[PASS] Bounded evidence collection session activated")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered evidence manifest rejected")
    print("[PASS] Atomic evidence session artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
