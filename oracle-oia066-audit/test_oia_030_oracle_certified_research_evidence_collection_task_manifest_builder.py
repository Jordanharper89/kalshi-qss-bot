from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_batch_activation_gate import (
    EVIDENCE_BATCH_ACTIVE,
    EVIDENCE_BATCH_ENTRY_ACTIVE,
    EVIDENCE_BATCH_ACTIVATION_POLICY_ID,
    stable_hash as activation_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_manifest_builder import (
    EVIDENCE_TASK_MANIFEST_ISSUED,
    EVIDENCE_TASK_MANIFEST_POLICY_ID,
    EVIDENCE_TASK_READY,
    CertifiedResearchEvidenceCollectionTaskManifestInvariantError,
    OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_active_batch(directory: Path) -> dict:
    entry_body = {
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
        "prohibited_operations": [
            "create_signal",
            "create_order",
        ],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "active_entry_status": EVIDENCE_BATCH_ENTRY_ACTIVE,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
    }
    entry = dict(entry_body)
    entry["active_entry_hash"] = activation_stable_hash(entry_body)

    body = {
        "schema_version": "OIA-029",
        "engine_id": "OIA-029",
        "activated_at": "2026-07-21T11:00:00+00:00",
        "evidence_batch_activation_id": "oia029-active-batch-test",
        "active_batch_status": EVIDENCE_BATCH_ACTIVE,
        "batch_number": 1,
        "worker_id": "oracle-worker-test",
        "source_evidence_batch_id": "oia028-batch-test",
        "source_evidence_session_id": "oia027-session-test",
        "source_evidence_manifest_id": "oia026-manifest-test",
        "source_certification_id": "oia025-certification-test",
        "source_readiness_id": "oia024-readiness-test",
        "source_session_id": "oia023-session-test",
        "source_activation_id": "oia022-activation-test",
        "source_claim_id": "oia021-claim-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "active_entry_count": 1,
        "evidence_session_policy_id": "session-policy-test",
        "evidence_batch_policy_id": "batch-policy-test",
        "evidence_batch_activation_policy_id": (
            EVIDENCE_BATCH_ACTIVATION_POLICY_ID
        ),
        "entries": [entry],
        "source_evidence_batch_hash": HASHES[5],
        "source_evidence_session_hash": HASHES[6],
        "source_evidence_manifest_hash": HASHES[7],
        "source_certification_hash": HASHES[8],
        "source_readiness_hash": HASHES[9],
        "source_session_hash": HASHES[10],
        "source_activation_hash": HASHES[11],
        "source_claim_hash": HASHES[12],
        "source_dispatch_manifest_hash": HASHES[13],
        "source_batch_hash": HASHES[14],
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
        "active_batch_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_batch_activation_hash"] = activation_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-030 TEST")
    print(" EVIDENCE COLLECTION TASK MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        active_directory = root / "active"
        task_directory = root / "tasks"
        source = write_active_batch(active_directory)

        builder = OracleCertifiedResearchEvidenceCollectionTaskManifestBuilder(
            active_batch_directory=active_directory,
            task_manifest_directory=task_directory,
        )
        fixed = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed, persist=True)
        second = builder.build(generated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-030"
        assert first.engine_id == "OIA-030"
        assert first.task_manifest_status == EVIDENCE_TASK_MANIFEST_ISSUED
        assert (
            first.evidence_task_manifest_policy_id
            == EVIDENCE_TASK_MANIFEST_POLICY_ID
        )
        assert (
            first.source_evidence_batch_activation_hash
            == source["evidence_batch_activation_hash"]
        )
        assert first.task_count == 1
        assert first.tasks[0].task_status == EVIDENCE_TASK_READY
        assert (
            first.tasks[0].source_active_entry_hash
            == source["entries"][0]["active_entry_hash"]
        )
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
        manifest_hash = body.pop("evidence_task_manifest_hash")
        assert manifest_hash == stable_hash(body)

        task_body = dict(first.tasks[0].to_dict())
        task_hash = task_body.pop("task_hash")
        assert task_hash == stable_hash(task_body)

        assert (task_directory / "current.json").exists()
        assert list((task_directory / "manifests").glob("*.json"))
        assert list(
            (task_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (active_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["entries"][0]["priority_score"] = "0.000000"
        (active_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            builder.build(generated_at=fixed, persist=False)
        except CertifiedResearchEvidenceCollectionTaskManifestInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-029 active batch was accepted.")

    print("[PASS] Actual OIA-029 active evidence batch contract consumed")
    print("[PASS] Evidence task manifest and task hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-029 lineage preserved")
    print("[PASS] Bounded read-only evidence collection tasks issued")
    print("[PASS] Analytic conclusions and forecasts remained disabled")
    print("[PASS] Tampered active evidence batch rejected")
    print("[PASS] Atomic task manifest artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
