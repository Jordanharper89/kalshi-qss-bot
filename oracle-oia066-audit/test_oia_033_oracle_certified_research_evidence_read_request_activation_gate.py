from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_request_manifest_builder import (
    EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
    EVIDENCE_READ_REQUEST_POLICY_ID,
    EVIDENCE_READ_REQUEST_READY,
    stable_hash as manifest_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_request_activation_gate import (
    EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
    EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID,
    EVIDENCE_READ_REQUEST_ACTIVE,
    CertifiedResearchEvidenceReadRequestActivationInvariantError,
    OracleCertifiedResearchEvidenceReadRequestActivationGate,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 50)]


def write_manifest(directory: Path) -> dict:
    request_body = {
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "tier": "qualified",
        "priority_score": "0.990000",
        "research_objective": "Collect bounded canonical evidence.",
        "evidence_scope_id": "scope.test",
        "requested_read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "request_status": EVIDENCE_READ_REQUEST_READY,
        "source_task_hash": HASHES[1],
        "source_active_task_hash": HASHES[2],
    }
    request = dict(request_body)
    request["evidence_read_request_hash"] = manifest_stable_hash(request_body)

    body = {
        "schema_version": "OIA-032",
        "engine_id": "OIA-032",
        "generated_at": "2026-07-21T14:00:00+00:00",
        "evidence_read_request_manifest_id": "oia032-request-manifest-test",
        "manifest_status": EVIDENCE_READ_REQUEST_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_task_activation_id": "oia031-task-activation-test",
        "source_evidence_task_manifest_id": "oia030-task-manifest-test",
        "source_evidence_batch_activation_id": "oia029-batch-active-test",
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
        "request_count": 1,
        "evidence_task_manifest_policy_id": "task-manifest-policy-test",
        "evidence_task_activation_policy_id": "task-activation-policy-test",
        "evidence_read_request_policy_id": EVIDENCE_READ_REQUEST_POLICY_ID,
        "requests": [request],
        "source_evidence_task_activation_hash": HASHES[3],
        "source_evidence_task_manifest_hash": HASHES[4],
        "source_evidence_batch_activation_hash": HASHES[5],
        "source_evidence_batch_hash": HASHES[6],
        "source_evidence_session_hash": HASHES[7],
        "source_evidence_manifest_hash": HASHES[8],
        "source_certification_hash": HASHES[9],
        "source_readiness_hash": HASHES[10],
        "source_session_hash": HASHES[11],
        "source_activation_hash": HASHES[12],
        "source_claim_hash": HASHES[13],
        "source_dispatch_manifest_hash": HASHES[14],
        "source_batch_hash": HASHES[15],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
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
        "read_request_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_request_manifest_hash"] = manifest_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-033 TEST")
    print(" EVIDENCE READ REQUEST ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        manifest_directory = root / "manifests"
        active_directory = root / "active"
        source = write_manifest(manifest_directory)

        gate = OracleCertifiedResearchEvidenceReadRequestActivationGate(
            read_request_directory=manifest_directory,
            active_read_request_directory=active_directory,
        )
        fixed = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-033"
        assert first.engine_id == "OIA-033"
        assert (
            first.activation_status
            == EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED
        )
        assert (
            first.evidence_read_request_activation_policy_id
            == EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID
        )
        assert (
            first.source_evidence_read_request_manifest_hash
            == source["evidence_read_request_manifest_hash"]
        )
        assert first.active_request_count == 1
        assert (
            first.requests[0].active_request_status
            == EVIDENCE_READ_REQUEST_ACTIVE
        )
        assert (
            first.requests[0].source_evidence_read_request_hash
            == source["requests"][0]["evidence_read_request_hash"]
        )
        assert all(
            operation.startswith("read_")
            for operation in first.requests[0].authorized_read_operations
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
        activation_hash = body.pop("evidence_read_request_activation_hash")
        assert activation_hash == stable_hash(body)

        request_body = dict(first.requests[0].to_dict())
        active_hash = request_body.pop("active_evidence_read_request_hash")
        assert active_hash == stable_hash(request_body)

        assert (active_directory / "current.json").exists()
        assert list((active_directory / "activations").glob("*.json"))
        assert list(
            (active_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (manifest_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["requests"][0]["requested_read_operations"].append(
            "create_order"
        )
        (manifest_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadRequestActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-032 read manifest was accepted.")

    print("[PASS] Actual OIA-032 read-request manifest contract consumed")
    print("[PASS] Read activation and active-request hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-032 lineage preserved")
    print("[PASS] Only bounded read-prefixed requests activated")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered read-request manifest rejected")
    print("[PASS] Atomic active read-request artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
