from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_manifest_builder import (
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
    stable_hash as manifest_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_activation_gate import (
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
    CertifiedResearchEvidenceCollectionTaskActivationInvariantError,
    OracleCertifiedResearchEvidenceCollectionTaskActivationGate,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_task_manifest(directory: Path) -> dict:
    task_body = {
        "task_sequence": 1,
        "activation_sequence": 1,
        "batch_sequence": 1,
        "session_sequence": 1,
        "evidence_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "tier": "qualified",
        "priority_score": "0.990000",
        "research_objective": "Collect bounded canonical evidence.",
        "evidence_scope_id": "scope.test",
        "authorized_evidence_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "task_status": EVIDENCE_TASK_READY,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
        "source_active_entry_hash": HASHES[5],
    }
    task = dict(task_body)
    task["task_hash"] = manifest_stable_hash(task_body)

    body = {
        "schema_version": "OIA-030",
        "engine_id": "OIA-030",
        "generated_at": "2026-07-21T12:00:00+00:00",
        "evidence_task_manifest_id": "oia030-task-manifest-test",
        "task_manifest_status": EVIDENCE_TASK_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_batch_activation_id": "oia029-active-test",
        "source_evidence_batch_id": "oia028-batch-test",
        "source_evidence_session_id": "oia027-session-test",
        "source_evidence_manifest_id": "oia026-manifest-test",
        "source_certification_id": "oia025-cert-test",
        "source_readiness_id": "oia024-ready-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "task_count": 1,
        "evidence_session_policy_id": "session-policy-test",
        "evidence_batch_policy_id": "batch-policy-test",
        "evidence_batch_activation_policy_id": "activation-policy-test",
        "evidence_task_manifest_policy_id": EVIDENCE_TASK_MANIFEST_POLICY_ID,
        "tasks": [task],
        "source_evidence_batch_activation_hash": HASHES[6],
        "source_evidence_batch_hash": HASHES[7],
        "source_evidence_session_hash": HASHES[8],
        "source_evidence_manifest_hash": HASHES[9],
        "source_certification_hash": HASHES[10],
        "source_readiness_hash": HASHES[11],
        "source_session_hash": HASHES[12],
        "source_activation_hash": HASHES[13],
        "source_claim_hash": HASHES[14],
        "source_dispatch_manifest_hash": HASHES[15],
        "source_batch_hash": HASHES[16],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
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
        "task_manifest_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_task_manifest_hash"] = manifest_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-031 TEST")
    print(" EVIDENCE COLLECTION TASK ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        manifest_directory = root / "manifests"
        active_directory = root / "active"
        source = write_task_manifest(manifest_directory)

        gate = OracleCertifiedResearchEvidenceCollectionTaskActivationGate(
            task_manifest_directory=manifest_directory,
            active_task_directory=active_directory,
        )
        fixed = datetime(2026, 7, 21, 13, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-031"
        assert first.engine_id == "OIA-031"
        assert first.task_activation_status == EVIDENCE_TASK_ACTIVATION_ISSUED
        assert (
            first.evidence_task_activation_policy_id
            == EVIDENCE_TASK_ACTIVATION_POLICY_ID
        )
        assert (
            first.source_evidence_task_manifest_hash
            == source["evidence_task_manifest_hash"]
        )
        assert first.active_task_count == 1
        assert first.tasks[0].active_task_status == EVIDENCE_TASK_ACTIVE
        assert first.tasks[0].source_task_hash == source["tasks"][0]["task_hash"]
        assert first.read_only_corpus is True
        assert first.evidence_collection_allowed is True

        for value in (
            first.research_execution_allowed,
            first.analytic_conclusion_allowed,
            first.forecast_creation_allowed,
            first.signals_allowed,
            first.alerts_allowed,
            first.qseries_handoff_allowed,
            first.execution_allowed,
            first.trading_recommendations_allowed,
            first.source_mutation_allowed,
            first.market_order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        ):
            assert value is False

        body = dict(first.to_dict())
        activation_hash = body.pop("evidence_task_activation_hash")
        assert activation_hash == stable_hash(body)

        task_body = dict(first.tasks[0].to_dict())
        active_task_hash = task_body.pop("active_task_hash")
        assert active_task_hash == stable_hash(task_body)

        assert (active_directory / "current.json").exists()
        assert list((active_directory / "activations").glob("*.json"))
        assert list(
            (active_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (manifest_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["tasks"][0]["priority_score"] = "0.000000"
        (manifest_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionTaskActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-030 task manifest was accepted.")

    print("[PASS] Actual OIA-030 evidence task manifest contract consumed")
    print("[PASS] Task activation and active-task hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-030 lineage preserved")
    print("[PASS] Bounded read-only evidence collection tasks activated")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered evidence task manifest rejected")
    print("[PASS] Atomic active-task artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
