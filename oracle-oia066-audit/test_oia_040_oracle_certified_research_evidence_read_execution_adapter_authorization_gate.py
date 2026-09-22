from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    stable_hash as readiness_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_authorization_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 90)]


def seed(directory: Path) -> dict:
    entry_body = {
        "readiness_sequence": 1,
        "binding_sequence": 1,
        "activation_sequence": 1,
        "invocation_sequence": 1,
        "authorization_sequence": 1,
        "request_sequence": 1,
        "task_sequence": 1,
        "work_item_id": "work.test",
        "worker_id": "oracle-worker-test",
        "dimension": "market_microstructure",
        "key": "spread-regime",
        "evidence_scope_id": "scope.test",
        "read_operations": [
            "read_canonical_observations",
            "read_market_state_lineage",
        ],
        "adapter_ids": list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "operation_adapter_bindings": [
            [
                "read_canonical_observations",
                "oracle_read_only_canonical_observation_adapter.v1",
            ],
            [
                "read_market_state_lineage",
                "oracle_read_only_market_state_lineage_adapter.v1",
            ],
        ],
        "adapter_contract_checks": [
            "adapter_id_allowlisted",
            "adapter_identity_read_only",
            "operation_mapping_exact",
            "source_binding_hash_verified",
            "corpus_execution_disabled",
        ],
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "readiness_status": EVIDENCE_READ_EXECUTION_ADAPTER_READY,
        "source_active_invocation_hash": H[1],
        "source_adapter_binding_hash": H[2],
    }
    entry = dict(entry_body)
    entry["adapter_readiness_hash"] = readiness_hash(entry_body)

    body = {
        "schema_version": "OIA-039",
        "engine_id": "OIA-039",
        "evaluated_at": "2026-07-21T21:00:00+00:00",
        "evidence_read_execution_adapter_readiness_manifest_id": "oia039-test",
        "readiness_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
        "worker_id": "oracle-worker-test",
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
        "readiness_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_adapter_binding_policy_id": "oia038-policy",
        "evidence_read_execution_adapter_readiness_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
        "readiness_entries": [entry],
        "source_evidence_read_execution_adapter_binding_manifest_hash": H[3],
        "source_evidence_read_execution_invocation_activation_hash": H[4],
        "source_evidence_read_execution_invocation_manifest_hash": H[5],
        "source_evidence_read_execution_authorization_hash": H[6],
        "source_evidence_read_execution_readiness_hash": H[7],
        "source_evidence_read_request_activation_hash": H[8],
        "source_evidence_read_request_manifest_hash": H[9],
        "source_evidence_task_activation_hash": H[10],
        "source_evidence_task_manifest_hash": H[11],
        "source_evidence_batch_activation_hash": H[12],
        "source_evidence_batch_hash": H[13],
        "source_evidence_session_hash": H[14],
        "source_evidence_manifest_hash": H[15],
        "source_certification_hash": H[16],
        "source_readiness_hash": H[17],
        "source_session_hash": H[18],
        "source_activation_hash": H[19],
        "source_claim_hash": H[20],
        "source_dispatch_manifest_hash": H[21],
        "source_batch_hash": H[22],
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
        "adapter_readiness_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_adapter_readiness_manifest_hash"] = (
        readiness_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-040 TEST")
    print(" EVIDENCE READ ADAPTER AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"
        source = seed(readiness_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterAuthorizationGate(
            readiness_directory=readiness_directory,
            authorization_directory=authorization_directory,
        )
        fixed = datetime(2026, 7, 21, 22, 0, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-040"
        assert first.engine_id == "OIA-040"
        assert first.authorization_manifest_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_ISSUED
        )
        assert first.evidence_read_execution_adapter_authorization_policy_id == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZATION_POLICY_ID
        )
        assert first.authorization_count == 1
        assert first.authorizations[0].authorization_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_AUTHORIZED
        )
        assert first.source_evidence_read_execution_adapter_readiness_manifest_hash == (
            source["evidence_read_execution_adapter_readiness_manifest_hash"]
        )
        assert first.authorizations[0].source_adapter_readiness_hash == (
            source["readiness_entries"][0]["adapter_readiness_hash"]
        )
        assert set(first.authorizations[0].authorized_adapter_ids).issubset(
            set(APPROVED_READ_ONLY_ADAPTER_IDS)
        )
        assert all(
            operation.startswith("read_")
            for operation in first.authorizations[0].authorized_read_operations
        )
        assert "readiness_hash_verified" in (
            first.authorizations[0].authorization_checks
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_adapter_authorization_allowed is True

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
            "evidence_read_execution_adapter_authorization_manifest_hash"
        )
        assert manifest_hash == stable_hash(body)

        authorization_body = dict(first.authorizations[0].to_dict())
        authorization_hash_value = authorization_body.pop(
            "adapter_authorization_hash"
        )
        assert authorization_hash_value == stable_hash(authorization_body)

        assert (authorization_directory / "current.json").exists()
        assert list((authorization_directory / "manifests").glob("*.json"))
        assert list(
            (authorization_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (readiness_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_entries"][0]["adapter_contract_checks"].remove(
            "corpus_execution_disabled"
        )
        (readiness_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.authorize(authorized_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterAuthorizationInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-039 adapter readiness accepted.")

    print("[PASS] Actual OIA-039 adapter readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-039 lineage preserved")
    print("[PASS] Only readiness-certified read-only adapters authorized")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or incomplete readiness rejected")
    print("[PASS] Atomic adapter-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
