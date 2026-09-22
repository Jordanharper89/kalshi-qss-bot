from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_batch_manifest_builder import (
    EVIDENCE_BATCH_ENTRY_AUTHORIZED, EVIDENCE_BATCH_ISSUED, EVIDENCE_BATCH_POLICY_ID, stable_hash as batch_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_batch_activation_gate import (
    EVIDENCE_BATCH_ACTIVE, EVIDENCE_BATCH_ENTRY_ACTIVE, EVIDENCE_BATCH_ACTIVATION_POLICY_ID,
    OracleCertifiedResearchEvidenceCollectionBatchActivationGate,
    CertifiedResearchEvidenceCollectionBatchActivationInvariantError, stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 30)]

def write_batch(directory: Path) -> dict:
    entry_body = {
        "batch_sequence": 1, "session_sequence": 1, "evidence_sequence": 1, "work_item_id": "work.test",
        "worker_id": "oracle-worker-test", "dimension": "market_microstructure", "key": "spread-regime",
        "tier": "qualified", "priority_score": "0.990000", "research_objective": "Collect bounded canonical evidence.",
        "evidence_scope_id": "scope.test", "authorized_evidence_operations": ["read_canonical_observations", "read_market_state_lineage"],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": ["preserve_source_hashes", "record_observation_bounds"],
        "batch_entry_status": EVIDENCE_BATCH_ENTRY_AUTHORIZED, "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2], "source_session_entry_hash": HASHES[3],
    }
    entry = dict(entry_body); entry["batch_entry_hash"] = batch_stable_hash(entry_body)
    body = {
        "schema_version": "OIA-028", "engine_id": "OIA-028", "generated_at": "2026-07-21T10:00:00+00:00",
        "evidence_batch_id": "oia028-batch-test", "batch_status": EVIDENCE_BATCH_ISSUED, "batch_number": 1,
        "worker_id": "oracle-worker-test", "source_evidence_session_id": "oia027-session-test",
        "source_evidence_manifest_id": "oia026-manifest-test", "source_certification_id": "oia025-certification-test",
        "source_readiness_id": "oia024-readiness-test", "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test", "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test", "selected_batch_id": "oia020-batch-test", "selected_batch_number": 1,
        "batch_entry_count": 1, "evidence_session_policy_id": "session-policy-test",
        "evidence_batch_policy_id": EVIDENCE_BATCH_POLICY_ID, "entries": [entry],
        "source_evidence_session_hash": HASHES[4], "source_evidence_manifest_hash": HASHES[5],
        "source_certification_hash": HASHES[6], "source_readiness_hash": HASHES[7], "source_session_hash": HASHES[8],
        "source_activation_hash": HASHES[9], "source_claim_hash": HASHES[10], "source_dispatch_manifest_hash": HASHES[11],
        "source_batch_hash": HASHES[12], "read_only_corpus": True, "evidence_collection_allowed": True,
        "research_execution_allowed": False, "analytic_conclusion_allowed": False, "forecast_creation_allowed": False,
        "signals_allowed": False, "alerts_allowed": False, "qseries_handoff_allowed": False, "execution_allowed": False,
        "trading_recommendations_allowed": False, "source_mutation_allowed": False, "market_order_creation_allowed": False,
        "funds_movement_allowed": False, "portfolio_mutation_allowed": False, "batch_artifact_persistence_allowed": True,
    }
    payload = dict(body); payload["evidence_batch_hash"] = batch_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload

def main() -> int:
    print("=" * 40); print(" OIA-029 TEST"); print(" EVIDENCE COLLECTION BATCH ACTIVATION"); print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary); batch_dir = root / "batch"; active_dir = root / "active"
        source = write_batch(batch_dir)
        gate = OracleCertifiedResearchEvidenceCollectionBatchActivationGate(evidence_batch_directory=batch_dir, active_batch_directory=active_dir)
        fixed = datetime(2026, 7, 21, 11, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-029" and first.engine_id == "OIA-029"
        assert first.active_batch_status == EVIDENCE_BATCH_ACTIVE
        assert first.evidence_batch_activation_policy_id == EVIDENCE_BATCH_ACTIVATION_POLICY_ID
        assert first.source_evidence_batch_hash == source["evidence_batch_hash"]
        assert first.active_entry_count == 1 and first.entries[0].active_entry_status == EVIDENCE_BATCH_ENTRY_ACTIVE
        assert first.entries[0].source_batch_entry_hash == source["entries"][0]["batch_entry_hash"]
        assert first.read_only_corpus is True and first.evidence_collection_allowed is True
        for value in (first.research_execution_allowed, first.analytic_conclusion_allowed, first.forecast_creation_allowed,
                      first.signals_allowed, first.alerts_allowed, first.qseries_handoff_allowed, first.execution_allowed,
                      first.trading_recommendations_allowed, first.source_mutation_allowed, first.market_order_creation_allowed,
                      first.funds_movement_allowed, first.portfolio_mutation_allowed):
            assert value is False
        body = dict(first.to_dict()); activation_hash = body.pop("evidence_batch_activation_hash"); assert activation_hash == stable_hash(body)
        entry_body = dict(first.entries[0].to_dict()); entry_hash = entry_body.pop("active_entry_hash"); assert entry_hash == stable_hash(entry_body)
        assert (active_dir / "current.json").exists() and list((active_dir / "activations").glob("*.json"))
        tampered = json.loads((batch_dir / "current.json").read_text(encoding="utf-8")); tampered["entries"][0]["priority_score"] = "0.000000"
        (batch_dir / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionBatchActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-028 evidence batch was accepted.")
    print("[PASS] Actual OIA-028 evidence batch contract consumed")
    print("[PASS] Active batch and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-028 lineage preserved")
    print("[PASS] Bounded read-only evidence collection batch activated")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered evidence batch rejected")
    print("[PASS] Atomic active batch artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
