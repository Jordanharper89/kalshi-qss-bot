from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_collection_task_activation_gate import (
    EVIDENCE_TASK_ACTIVATION_ISSUED,
    EVIDENCE_TASK_ACTIVATION_POLICY_ID,
    EVIDENCE_TASK_ACTIVE,
    stable_hash as activation_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_request_manifest_builder import (
    EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
    EVIDENCE_READ_REQUEST_POLICY_ID,
    EVIDENCE_READ_REQUEST_READY,
    CertifiedResearchEvidenceReadRequestManifestInvariantError,
    OracleCertifiedResearchEvidenceReadRequestManifestBuilder,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 40)]


def write_activation(directory: Path) -> dict:
    task_body = {
        "activation_sequence": 1,
        "task_sequence": 1,
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
        "active_task_status": EVIDENCE_TASK_ACTIVE,
        "source_certification_entry_hash": HASHES[1],
        "source_evidence_entry_hash": HASHES[2],
        "source_session_entry_hash": HASHES[3],
        "source_batch_entry_hash": HASHES[4],
        "source_active_entry_hash": HASHES[5],
        "source_task_hash": HASHES[6],
    }
    task = dict(task_body)
    task["active_task_hash"] = activation_stable_hash(task_body)

    body = {
        "schema_version": "OIA-031",
        "engine_id": "OIA-031",
        "activated_at": "2026-07-21T13:00:00+00:00",
        "evidence_task_activation_id": "oia031-task-activation-test",
        "task_activation_status": EVIDENCE_TASK_ACTIVATION_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_task_manifest_id": "oia030-task-manifest-test",
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
        "active_task_count": 1,
        "evidence_task_manifest_policy_id": "task-manifest-policy-test",
        "evidence_task_activation_policy_id": EVIDENCE_TASK_ACTIVATION_POLICY_ID,
        "tasks": [task],
        "source_evidence_task_manifest_hash": HASHES[7],
        "source_evidence_batch_activation_hash": HASHES[8],
        "source_evidence_batch_hash": HASHES[9],
        "source_evidence_session_hash": HASHES[10],
        "source_evidence_manifest_hash": HASHES[11],
        "source_certification_hash": HASHES[12],
        "source_readiness_hash": HASHES[13],
        "source_session_hash": HASHES[14],
        "source_activation_hash": HASHES[15],
        "source_claim_hash": HASHES[16],
        "source_dispatch_manifest_hash": HASHES[17],
        "source_batch_hash": HASHES[18],
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
        "active_task_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_task_activation_hash"] = activation_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-032 TEST")
    print(" EVIDENCE READ REQUEST MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        active_directory = root / "active"
        request_directory = root / "requests"
        source = write_activation(active_directory)

        builder = OracleCertifiedResearchEvidenceReadRequestManifestBuilder(
            active_task_directory=active_directory,
            read_request_directory=request_directory,
        )
        fixed = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed, persist=True)
        second = builder.build(generated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-032"
        assert first.engine_id == "OIA-032"
        assert first.manifest_status == EVIDENCE_READ_REQUEST_MANIFEST_ISSUED
        assert first.evidence_read_request_policy_id == EVIDENCE_READ_REQUEST_POLICY_ID
        assert (
            first.source_evidence_task_activation_hash
            == source["evidence_task_activation_hash"]
        )
        assert first.request_count == 1
        assert first.requests[0].request_status == EVIDENCE_READ_REQUEST_READY
        assert (
            first.requests[0].source_active_task_hash
            == source["tasks"][0]["active_task_hash"]
        )
        assert all(
            operation.startswith("read_")
            for operation in first.requests[0].requested_read_operations
        )
        assert first.read_only_corpus is True
        assert first.evidence_collection_allowed is True
        assert first.corpus_read_requests_allowed is True
        assert first.corpus_read_execution_allowed is False

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
        manifest_hash = body.pop("evidence_read_request_manifest_hash")
        assert manifest_hash == stable_hash(body)

        request_body = dict(first.requests[0].to_dict())
        request_hash = request_body.pop("evidence_read_request_hash")
        assert request_hash == stable_hash(request_body)

        assert (request_directory / "current.json").exists()
        assert list((request_directory / "manifests").glob("*.json"))
        assert list(
            (request_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (active_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["tasks"][0]["authorized_evidence_operations"].append(
            "create_order"
        )
        (active_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            builder.build(generated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadRequestManifestInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-031 task activation was accepted.")

    print("[PASS] Actual OIA-031 active-task contract consumed")
    print("[PASS] Read-request manifest and request hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-031 lineage preserved")
    print("[PASS] Only bounded read-prefixed corpus requests issued")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered active-task activation rejected")
    print("[PASS] Atomic read-request artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
