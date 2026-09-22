from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_invocation_manifest_builder import (
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY,
    stable_hash as invocation_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_invocation_activation_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVE,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivationGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 120)]


def seed(directory: Path) -> dict:
    invocation_body = {
        "adapter_invocation_sequence": 1,
        "adapter_authorization_sequence": 1,
        "adapter_readiness_sequence": 1,
        "binding_sequence": 1,
        "activation_sequence": 1,
        "invocation_sequence": 1,
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "evidence_scope_id": "scope.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "invocation_arguments": {
            "worker_id": "oracle-worker-test",
            "work_item_id": "work.test",
            "evidence_scope_id": "scope.test",
            "dimension": "market_microstructure",
            "key": "spread-regime",
            "read_only": True,
            "execute": False,
        },
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "invocation_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY,
        "source_active_invocation_hash": H[1],
        "source_adapter_binding_hash": H[2],
        "source_adapter_readiness_hash": H[3],
        "source_adapter_authorization_hash": H[4],
    }
    invocation = dict(invocation_body)
    invocation["adapter_invocation_hash"] = invocation_hash(invocation_body)

    body = {
        "schema_version": "OIA-041",
        "engine_id": "OIA-041",
        "generated_at": "2026-07-21T23:00:00+00:00",
        "evidence_read_execution_adapter_invocation_manifest_id":
            "oia041-test",
        "invocation_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_read_execution_adapter_authorization_manifest_id":
            "oia040-test",
        "source_evidence_read_execution_adapter_readiness_manifest_id":
            "oia039-test",
        "source_evidence_read_execution_adapter_binding_manifest_id":
            "oia038-test",
        "source_evidence_read_execution_invocation_activation_id":
            "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id":
            "oia036-test",
        "source_evidence_read_execution_authorization_id": "oia035-test",
        "source_evidence_read_execution_readiness_id": "oia034-test",
        "source_evidence_read_request_activation_id": "oia033-test",
        "source_evidence_read_request_manifest_id": "oia032-test",
        "source_evidence_task_activation_id": "oia031-test",
        "source_evidence_task_manifest_id": "oia030-test",
        "source_evidence_batch_activation_id": "oia029-test",
        "source_evidence_batch_id": "oia028-test",
        "source_evidence_session_id": "oia027-test",
        "source_evidence_manifest_id": "oia026-test",
        "source_certification_id": "oia025-test",
        "source_readiness_id": "oia024-test",
        "source_session_id": "oia023-test",
        "source_activation_id": "oia022-test",
        "source_claim_id": "oia021-test",
        "dispatch_manifest_id": "oia020-manifest-test",
        "selected_batch_id": "oia020-batch-test",
        "selected_batch_number": 1,
        "adapter_invocation_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_adapter_authorization_policy_id":
            "oia040-policy",
        "evidence_read_execution_adapter_invocation_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
        "adapter_invocations": [invocation],
        "source_evidence_read_execution_adapter_authorization_manifest_hash":
            H[5],
        "source_evidence_read_execution_adapter_readiness_manifest_hash":
            H[6],
        "source_evidence_read_execution_adapter_binding_manifest_hash":
            H[7],
        "source_evidence_read_execution_invocation_activation_hash":
            H[8],
        "source_evidence_read_execution_invocation_manifest_hash":
            H[9],
        "source_evidence_read_execution_authorization_hash": H[10],
        "source_evidence_read_execution_readiness_hash": H[11],
        "source_evidence_read_request_activation_hash": H[12],
        "source_evidence_read_request_manifest_hash": H[13],
        "source_evidence_task_activation_hash": H[14],
        "source_evidence_task_manifest_hash": H[15],
        "source_evidence_batch_activation_hash": H[16],
        "source_evidence_batch_hash": H[17],
        "source_evidence_session_hash": H[18],
        "source_evidence_manifest_hash": H[19],
        "source_certification_hash": H[20],
        "source_readiness_hash": H[21],
        "source_session_hash": H[22],
        "source_activation_hash": H[23],
        "source_claim_hash": H[24],
        "source_dispatch_manifest_hash": H[25],
        "source_batch_hash": H[26],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
        "read_execution_authorization_allowed": True,
        "read_execution_invocation_allowed": True,
        "read_execution_invocation_activation_allowed": True,
        "read_execution_adapter_binding_allowed": True,
        "read_execution_adapter_readiness_allowed": True,
        "read_execution_adapter_authorization_allowed": True,
        "read_execution_adapter_invocation_allowed": True,
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
        "adapter_invocation_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_adapter_invocation_manifest_hash"] = (
        invocation_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-042 TEST")
    print(" ADAPTER INVOCATION ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        invocation_directory = root / "invocation"
        active_directory = root / "active"
        source = seed(invocation_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationActivationGate(
                invocation_directory=invocation_directory,
                active_invocation_directory=active_directory,
            )
        )
        fixed = datetime(2026, 7, 22, 0, 0, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-042"
        assert first.engine_id == "OIA-042"
        assert first.activation_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_ISSUED
        )
        assert (
            first.evidence_read_execution_adapter_invocation_activation_policy_id
            == EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVATION_POLICY_ID
        )
        assert first.active_adapter_invocation_count == 1
        active = first.active_adapter_invocations[0]
        assert active.activation_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_ACTIVE
        )
        assert (
            first.source_evidence_read_execution_adapter_invocation_manifest_hash
            == source[
                "evidence_read_execution_adapter_invocation_manifest_hash"
            ]
        )
        assert active.source_adapter_invocation_hash == (
            source["adapter_invocations"][0]["adapter_invocation_hash"]
        )
        assert active.adapter_id in APPROVED_READ_ONLY_ADAPTER_IDS
        assert active.read_operation.startswith("read_")
        assert active.invocation_arguments["activated"] is True
        assert active.invocation_arguments["execute"] is False
        assert active.invocation_arguments["read_only"] is True
        assert first.corpus_read_execution_allowed is False
        assert (
            first.read_execution_adapter_invocation_activation_allowed
            is True
        )

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
        activation_hash = body.pop(
            "evidence_read_execution_adapter_invocation_activation_hash"
        )
        assert activation_hash == stable_hash(body)

        active_body = dict(active.to_dict())
        active_hash = active_body.pop("active_adapter_invocation_hash")
        assert active_hash == stable_hash(active_body)

        assert (active_directory / "current.json").exists()
        assert list((active_directory / "activations").glob("*.json"))
        assert list(
            (active_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (invocation_directory / "current.json").read_text(
                encoding="utf-8"
            )
        )
        tampered["adapter_invocations"][0]["invocation_arguments"][
            "execute"
        ] = True
        (invocation_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(activated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-041 adapter invocation accepted.")

    print("[PASS] Actual OIA-041 adapter invocation contract consumed")
    print("[PASS] Activation and active-invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-041 lineage preserved")
    print("[PASS] Only approved read-only adapter invocations activated")
    print("[PASS] Invocation arguments remained non-executing")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or executable invocation rejected")
    print("[PASS] Atomic active-invocation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
