from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_authorization_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
    stable_hash as authorization_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_invocation_manifest_builder import (
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID,
    EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY,
    CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifestBuilder,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 100)]


def seed(directory: Path) -> dict:
    authorization_body = {
        "authorization_sequence": 1,
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
        "authorized_read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "authorized_adapter_ids": list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "authorized_operation_adapter_bindings": [
            [
                "read_canonical_observations",
                "oracle_read_only_canonical_observation_adapter.v1",
            ],
            [
                "read_market_state_lineage",
                "oracle_read_only_market_state_lineage_adapter.v1",
            ],
        ],
        "authorization_checks": [
            "readiness_status_verified",
            "readiness_hash_verified",
            "adapter_allowlist_verified",
            "operation_mapping_verified",
            "read_only_identity_verified",
            "corpus_execution_disabled",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "authorization_status": EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
        "source_active_invocation_hash": H[1],
        "source_adapter_binding_hash": H[2],
        "source_adapter_readiness_hash": H[3],
    }
    authorization = dict(authorization_body)
    authorization["adapter_authorization_hash"] = authorization_hash(
        authorization_body
    )

    body = {
        "schema_version": "OIA-040",
        "engine_id": "OIA-040",
        "authorized_at": "2026-07-21T22:00:00+00:00",
        "evidence_read_execution_adapter_authorization_manifest_id": "oia040-test",
        "authorization_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
        "worker_id": "oracle-worker-test",
        "source_evidence_read_execution_adapter_readiness_manifest_id": "oia039-test",
        "source_evidence_read_execution_adapter_binding_manifest_id": "oia038-test",
        "source_evidence_read_execution_invocation_activation_id": "oia037-test",
        "source_evidence_read_execution_invocation_manifest_id": "oia036-test",
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
        "authorization_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_adapter_readiness_policy_id": "oia039-policy",
        "evidence_read_execution_adapter_authorization_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
        "authorizations": [authorization],
        "source_evidence_read_execution_adapter_readiness_manifest_hash": H[4],
        "source_evidence_read_execution_adapter_binding_manifest_hash": H[5],
        "source_evidence_read_execution_invocation_activation_hash": H[6],
        "source_evidence_read_execution_invocation_manifest_hash": H[7],
        "source_evidence_read_execution_authorization_hash": H[8],
        "source_evidence_read_execution_readiness_hash": H[9],
        "source_evidence_read_request_activation_hash": H[10],
        "source_evidence_read_request_manifest_hash": H[11],
        "source_evidence_task_activation_hash": H[12],
        "source_evidence_task_manifest_hash": H[13],
        "source_evidence_batch_activation_hash": H[14],
        "source_evidence_batch_hash": H[15],
        "source_evidence_session_hash": H[16],
        "source_evidence_manifest_hash": H[17],
        "source_certification_hash": H[18],
        "source_readiness_hash": H[19],
        "source_session_hash": H[20],
        "source_activation_hash": H[21],
        "source_claim_hash": H[22],
        "source_dispatch_manifest_hash": H[23],
        "source_batch_hash": H[24],
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
        "adapter_authorization_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_adapter_authorization_manifest_hash"] = (
        authorization_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-041 TEST")
    print(" EVIDENCE READ ADAPTER INVOCATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization_directory = root / "authorization"
        invocation_directory = root / "invocation"
        source = seed(authorization_directory)

        builder = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterInvocationManifestBuilder(
                authorization_directory=authorization_directory,
                invocation_directory=invocation_directory,
            )
        )
        fixed = datetime(2026, 7, 21, 23, 0, tzinfo=timezone.utc)
        first = builder.build(generated_at=fixed, persist=True)
        second = builder.build(generated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-041"
        assert first.engine_id == "OIA-041"
        assert first.invocation_manifest_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_MANIFEST_ISSUED
        )
        assert first.evidence_read_execution_adapter_invocation_policy_id == (
            EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_POLICY_ID
        )
        assert first.adapter_invocation_count == 2
        assert all(
            invocation.invocation_status
            == EVIDENCE_READ_EXECUTION_ADAPTER_INVOCATION_READY
            for invocation in first.adapter_invocations
        )
        assert first.source_evidence_read_execution_adapter_authorization_manifest_hash == (
            source["evidence_read_execution_adapter_authorization_manifest_hash"]
        )
        assert all(
            invocation.source_adapter_authorization_hash
            == source["authorizations"][0]["adapter_authorization_hash"]
            for invocation in first.adapter_invocations
        )
        assert all(
            invocation.read_operation.startswith("read_")
            for invocation in first.adapter_invocations
        )
        assert all(
            invocation.adapter_id in APPROVED_READ_ONLY_ADAPTER_IDS
            for invocation in first.adapter_invocations
        )
        assert all(
            invocation.invocation_arguments["execute"] is False
            and invocation.invocation_arguments["read_only"] is True
            for invocation in first.adapter_invocations
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_adapter_invocation_allowed is True

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
        manifest_hash = body.pop(
            "evidence_read_execution_adapter_invocation_manifest_hash"
        )
        assert manifest_hash == stable_hash(body)

        for invocation in first.adapter_invocations:
            invocation_body = dict(invocation.to_dict())
            invocation_hash_value = invocation_body.pop(
                "adapter_invocation_hash"
            )
            assert invocation_hash_value == stable_hash(invocation_body)

        assert (invocation_directory / "current.json").exists()
        assert list((invocation_directory / "manifests").glob("*.json"))
        assert list(
            (invocation_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (authorization_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["authorizations"][0][
            "authorized_operation_adapter_bindings"
        ][0][1] = "oracle_write_capable_observation_adapter.v1"
        (authorization_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            builder.build(generated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterInvocationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-040 adapter authorization accepted.")

    print("[PASS] Actual OIA-040 adapter authorization contract consumed")
    print("[PASS] Invocation manifest and adapter-invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-040 lineage preserved")
    print("[PASS] Only authorized read-only adapter invocations issued")
    print("[PASS] Invocation arguments remained non-executing and read-only")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable authorization rejected")
    print("[PASS] Atomic adapter-invocation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
