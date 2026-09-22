from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_request_activation_gate import (
    EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
    EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID,
    EVIDENCE_READ_REQUEST_ACTIVE,
    stable_hash as activation_stable_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ENTRY_READY,
    EVIDENCE_READ_EXECUTION_READY,
    EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionReadinessInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionReadinessGate,
    stable_hash,
)

HASHES = [f"{index:064x}" for index in range(1, 60)]


def write_activation(directory: Path) -> dict:
    request_body = {
        "activation_sequence": 1,
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
        "authorized_read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "active_request_status": EVIDENCE_READ_REQUEST_ACTIVE,
        "source_task_hash": HASHES[1],
        "source_active_task_hash": HASHES[2],
        "source_evidence_read_request_hash": HASHES[3],
    }
    request = dict(request_body)
    request["active_evidence_read_request_hash"] = activation_stable_hash(request_body)

    body = {
        "schema_version": "OIA-033",
        "engine_id": "OIA-033",
        "activated_at": "2026-07-21T15:00:00+00:00",
        "evidence_read_request_activation_id": "oia033-read-activation-test",
        "activation_status": EVIDENCE_READ_REQUEST_ACTIVATION_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_read_request_manifest_id": "oia032-read-manifest-test",
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
        "active_request_count": 1,
        "evidence_task_manifest_policy_id": "task-manifest-policy-test",
        "evidence_task_activation_policy_id": "task-activation-policy-test",
        "evidence_read_request_policy_id": "read-request-policy-test",
        "evidence_read_request_activation_policy_id": (
            EVIDENCE_READ_REQUEST_ACTIVATION_POLICY_ID
        ),
        "requests": [request],
        "source_evidence_read_request_manifest_hash": HASHES[4],
        "source_evidence_task_activation_hash": HASHES[5],
        "source_evidence_task_manifest_hash": HASHES[6],
        "source_evidence_batch_activation_hash": HASHES[7],
        "source_evidence_batch_hash": HASHES[8],
        "source_evidence_session_hash": HASHES[9],
        "source_evidence_manifest_hash": HASHES[10],
        "source_certification_hash": HASHES[11],
        "source_readiness_hash": HASHES[12],
        "source_session_hash": HASHES[13],
        "source_activation_hash": HASHES[14],
        "source_claim_hash": HASHES[15],
        "source_dispatch_manifest_hash": HASHES[16],
        "source_batch_hash": HASHES[17],
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
        "active_read_request_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_request_activation_hash"] = activation_stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-034 TEST")
    print(" EVIDENCE READ EXECUTION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        activation_directory = root / "active"
        readiness_directory = root / "readiness"
        source = write_activation(activation_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionReadinessGate(
            active_read_request_directory=activation_directory,
            readiness_directory=readiness_directory,
        )
        fixed = datetime(2026, 7, 21, 16, 0, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-034"
        assert first.engine_id == "OIA-034"
        assert first.readiness_status == EVIDENCE_READ_EXECUTION_READY
        assert (
            first.evidence_read_execution_readiness_policy_id
            == EVIDENCE_READ_EXECUTION_READINESS_POLICY_ID
        )
        assert (
            first.source_evidence_read_request_activation_hash
            == source["evidence_read_request_activation_hash"]
        )
        assert first.readiness_entry_count == 1
        assert first.entries[0].readiness_status == EVIDENCE_READ_EXECUTION_ENTRY_READY
        assert (
            first.entries[0].source_active_evidence_read_request_hash
            == source["requests"][0]["active_evidence_read_request_hash"]
        )
        assert all(
            operation.startswith("read_")
            for operation in first.entries[0].authorized_read_operations
        )
        assert first.read_only_corpus is True
        assert first.evidence_collection_allowed is True
        assert first.corpus_read_requests_allowed is True
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_readiness_allowed is True

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
        readiness_hash = body.pop("evidence_read_execution_readiness_hash")
        assert readiness_hash == stable_hash(body)

        entry_body = dict(first.entries[0].to_dict())
        entry_hash = entry_body.pop("readiness_entry_hash")
        assert entry_hash == stable_hash(entry_body)

        assert (readiness_directory / "current.json").exists()
        assert list((readiness_directory / "readiness").glob("*.json"))
        assert list(
            (readiness_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (activation_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["requests"][0]["authorized_read_operations"].append("create_order")
        (activation_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionReadinessInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-033 activation was accepted.")

    print("[PASS] Actual OIA-033 active read-request contract consumed")
    print("[PASS] Readiness and readiness-entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-033 lineage preserved")
    print("[PASS] Only bounded read-prefixed requests certified ready")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered active read-request activation rejected")
    print("[PASS] Atomic read-execution readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
