from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_binding_gate import (
    APPROVED_READ_ONLY_ADAPTER_IDS,
    EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
    stable_hash as binding_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_readiness_gate import (
    EVIDENCE_READ_EXECUTION_ADAPTER_READY,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED,
    EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID,
    CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate,
    stable_hash,
)

H = [f"{index:064x}" for index in range(1, 80)]


def seed(directory: Path) -> dict:
    binding_body = {
        "binding_sequence": 1,
        "activation_sequence": 1,
        "invocation_sequence": 1,
        "authorization_sequence": 1,
        "readiness_sequence": 1,
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
        "prohibited_operations": ["create_signal", "create_order"],
        "completion_requirements": [
            "preserve_source_hashes",
            "record_observation_bounds",
        ],
        "binding_status": EVIDENCE_READ_EXECUTION_ADAPTER_BOUND,
        "source_evidence_read_request_hash": H[1],
        "source_active_evidence_read_request_hash": H[2],
        "source_readiness_entry_hash": H[3],
        "source_authorization_entry_hash": H[4],
        "source_invocation_hash": H[5],
        "source_active_invocation_hash": H[6],
    }
    binding = dict(binding_body)
    binding["adapter_binding_hash"] = binding_hash(binding_body)

    body = {
        "schema_version": "OIA-038",
        "engine_id": "OIA-038",
        "bound_at": "2026-07-21T20:00:00+00:00",
        "evidence_read_execution_adapter_binding_manifest_id": "oia038-test",
        "binding_manifest_status":
            EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_ISSUED,
        "worker_id": "oracle-worker-test",
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
        "binding_count": 1,
        "approved_read_only_adapter_ids":
            list(APPROVED_READ_ONLY_ADAPTER_IDS),
        "evidence_read_execution_invocation_activation_policy_id":
            "oia037-policy",
        "evidence_read_execution_adapter_binding_policy_id":
            EVIDENCE_READ_EXECUTION_ADAPTER_BINDING_POLICY_ID,
        "bindings": [binding],
        "source_evidence_read_execution_invocation_activation_hash": H[7],
        "source_evidence_read_execution_invocation_manifest_hash": H[8],
        "source_evidence_read_execution_authorization_hash": H[9],
        "source_evidence_read_execution_readiness_hash": H[10],
        "source_evidence_read_request_activation_hash": H[11],
        "source_evidence_read_request_manifest_hash": H[12],
        "source_evidence_task_activation_hash": H[13],
        "source_evidence_task_manifest_hash": H[14],
        "source_evidence_batch_activation_hash": H[15],
        "source_evidence_batch_hash": H[16],
        "source_evidence_session_hash": H[17],
        "source_evidence_manifest_hash": H[18],
        "source_certification_hash": H[19],
        "source_readiness_hash": H[20],
        "source_session_hash": H[21],
        "source_activation_hash": H[22],
        "source_claim_hash": H[23],
        "source_dispatch_manifest_hash": H[24],
        "source_batch_hash": H[25],
        "read_only_corpus": True,
        "evidence_collection_allowed": True,
        "corpus_read_requests_allowed": True,
        "corpus_read_execution_allowed": False,
        "read_execution_readiness_allowed": True,
        "read_execution_authorization_allowed": True,
        "read_execution_invocation_allowed": True,
        "read_execution_invocation_activation_allowed": True,
        "read_execution_adapter_binding_allowed": True,
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
        "adapter_binding_artifact_persistence_allowed": True,
    }
    payload = dict(body)
    payload["evidence_read_execution_adapter_binding_manifest_hash"] = (
        binding_hash(body)
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-039 TEST")
    print(" EVIDENCE READ ADAPTER READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binding_directory = root / "bindings"
        readiness_directory = root / "readiness"
        source = seed(binding_directory)

        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterReadinessGate(
            binding_directory=binding_directory,
            readiness_directory=readiness_directory,
        )
        fixed = datetime(2026, 7, 21, 21, 0, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-039"
        assert first.engine_id == "OIA-039"
        assert first.readiness_manifest_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_ISSUED
        )
        assert first.evidence_read_execution_adapter_readiness_policy_id == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READINESS_POLICY_ID
        )
        assert first.readiness_count == 1
        assert first.readiness_entries[0].readiness_status == (
            EVIDENCE_READ_EXECUTION_ADAPTER_READY
        )
        assert first.source_evidence_read_execution_adapter_binding_manifest_hash == (
            source["evidence_read_execution_adapter_binding_manifest_hash"]
        )
        assert first.readiness_entries[0].source_adapter_binding_hash == (
            source["bindings"][0]["adapter_binding_hash"]
        )
        assert set(first.readiness_entries[0].adapter_ids).issubset(
            set(APPROVED_READ_ONLY_ADAPTER_IDS)
        )
        assert "operation_mapping_exact" in (
            first.readiness_entries[0].adapter_contract_checks
        )
        assert first.corpus_read_execution_allowed is False
        assert first.read_execution_adapter_readiness_allowed is True

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
            "evidence_read_execution_adapter_readiness_manifest_hash"
        )
        assert manifest_hash == stable_hash(body)

        readiness_body = dict(first.readiness_entries[0].to_dict())
        readiness_hash_value = readiness_body.pop("adapter_readiness_hash")
        assert readiness_hash_value == stable_hash(readiness_body)

        assert (readiness_directory / "current.json").exists()
        assert list((readiness_directory / "manifests").glob("*.json"))
        assert list(
            (readiness_directory / "workers" / first.worker_id).glob("*.json")
        )

        tampered = json.loads(
            (binding_directory / "current.json").read_text(encoding="utf-8")
        )
        tampered["bindings"][0]["adapter_ids"][0] = (
            "oracle_write_capable_observation_adapter.v1"
        )
        (binding_directory / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
        except CertifiedResearchEvidenceReadExecutionAdapterReadinessInvariantError:
            pass
        else:
            raise AssertionError("Tampered OIA-038 adapter binding accepted.")

    print("[PASS] Actual OIA-038 adapter binding contract consumed")
    print("[PASS] Readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-038 lineage preserved")
    print("[PASS] Only approved read-only adapters certified ready")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable adapters rejected")
    print("[PASS] Atomic adapter-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
