import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_invocation_activation_gate import (
    AdapterExecutionInvocationActivationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate,
    POLICY_ID,
    STATUS_ACTIVATION_ISSUED,
    STATUS_INVOCATION_ACTIVE,
    stable_hash,
)


def seed_oia045(directory: Path) -> dict:
    source_lineage = {
        "source_evidence_read_execution_adapter_invocation_manifest_id":
            "oia041-test",
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
        "source_evidence_read_execution_authorization_id":
            "oia035-test",
        "source_evidence_read_execution_readiness_id":
            "oia034-test",
        "source_evidence_read_request_activation_id":
            "oia033-test",
        "source_evidence_read_request_manifest_id":
            "oia032-test",
        "source_evidence_task_activation_id":
            "oia031-test",
        "source_evidence_task_manifest_id":
            "oia030-test",
        "source_evidence_batch_activation_id":
            "oia029-test",
        "source_evidence_batch_id":
            "oia028-test",
        "source_evidence_session_id":
            "oia027-test",
        "source_evidence_manifest_id":
            "oia026-test",
        "source_certification_id":
            "oia025-test",
        "source_readiness_id":
            "oia024-test",
        "source_session_id":
            "oia023-test",
        "source_activation_id":
            "oia022-test",
        "source_claim_id":
            "oia021-test",
        "dispatch_manifest_id":
            "oia020-test",
        "selected_batch_id":
            "oia020-batch",
        "selected_batch_number": 1,
    }

    invocation_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "invocation_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
        },
        "invocation_checks": [
            "authorization_manifest_hash_verified",
            "authorization_entry_hash_verified",
            "readiness_entry_lineage_verified",
            "active_invocation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        ],
        "invocation_status":
            "evidence_read_execution_adapter_execution_invocation_ready",
        "source_authorization_entry_hash": stable_hash(
            {"source": "oia044-entry"}
        ),
        "source_readiness_entry_hash": stable_hash(
            {"source": "oia043-entry"}
        ),
        "source_active_adapter_invocation_hash": stable_hash(
            {"source": "oia042-active-invocation"}
        ),
    }

    invocation = dict(invocation_body)
    invocation["execution_invocation_hash"] = stable_hash(
        invocation_body
    )

    manifest_body = {
        "schema_version": "OIA-045",
        "engine_id": "OIA-045",
        "created_at": "2026-07-22T03:00:00+00:00",
        "invocation_manifest_id":
            "oia045-test-invocation-manifest",
        "invocation_manifest_status":
            "evidence_read_execution_adapter_execution_invocation_manifest_issued",
        "invocation_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "execution-invocation-manifest.v1",
        "worker_id": "oracle-worker-test",
        "invocation_count": 1,
        "invocations": [invocation],
        "source_execution_authorization_id":
            "oia044-test-authorization",
        "source_execution_authorization_manifest_hash":
            stable_hash({"source": "oia044-manifest"}),
        "source_execution_readiness_id":
            "oia043-test-readiness",
        "source_execution_readiness_manifest_hash":
            stable_hash({"source": "oia043-manifest"}),
        "source_activation_hash":
            stable_hash({"source": "oia042-activation"}),
        "source_lineage": source_lineage,
        "invocation_manifest_created": True,
        "invocation_activation_allowed": True,
        "adapter_execution_allowed": False,
        "adapter_execution_performed": False,
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
        "invocation_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload["invocation_manifest_hash"] = stable_hash(
        manifest_body
    )

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-046 TEST")
    print(" EXECUTION INVOCATION ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        invocation_directory = root / "invocations"
        activation_directory = root / "activation"

        source = seed_oia045(invocation_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationActivationGate(
                invocation_directory=invocation_directory,
                activation_directory=activation_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            4,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.activate(
            activated_at=fixed,
            persist=True,
        )

        second = gate.activate(
            activated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-046"
        assert first.engine_id == "OIA-046"
        assert first.activation_status == STATUS_ACTIVATION_ISSUED
        assert first.activation_policy_id == POLICY_ID
        assert first.active_invocation_count == 1

        active = first.active_invocations[0]

        assert active.activation_status == STATUS_INVOCATION_ACTIVE

        assert (
            active.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            active.read_operation
            == "read_canonical_observations"
        )

        assert active.active_invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert active.source_execution_invocation_hash == (
            source["invocations"][0][
                "execution_invocation_hash"
            ]
        )

        assert active.source_authorization_entry_hash == (
            source["invocations"][0][
                "source_authorization_entry_hash"
            ]
        )

        assert active.source_readiness_entry_hash == (
            source["invocations"][0][
                "source_readiness_entry_hash"
            ]
        )

        assert active.source_active_adapter_invocation_hash == (
            source["invocations"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "invocation_manifest_hash_verified",
            "execution_invocation_hash_verified",
            "authorization_lineage_verified",
            "readiness_lineage_verified",
            "prior_activation_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "active_invocation_remained_non_executing",
            "callable_resolution_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(active.activation_checks))

        assert first.source_execution_invocation_manifest_id == (
            source["invocation_manifest_id"]
        )

        assert (
            first.source_execution_invocation_manifest_hash
            == source["invocation_manifest_hash"]
        )

        assert first.source_execution_authorization_id == (
            source["source_execution_authorization_id"]
        )

        assert (
            first.source_execution_authorization_manifest_hash
            == source[
                "source_execution_authorization_manifest_hash"
            ]
        )

        assert first.source_execution_readiness_id == (
            source["source_execution_readiness_id"]
        )

        assert (
            first.source_execution_readiness_manifest_hash
            == source[
                "source_execution_readiness_manifest_hash"
            ]
        )

        assert first.source_activation_hash == (
            source["source_activation_hash"]
        )

        assert first.source_lineage == source["source_lineage"]

        assert first.invocation_activation_issued is True
        assert first.execution_readiness_evaluation_allowed is True
        assert first.callable_resolution_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.activation_artifact_persistence_allowed is True

        prohibited_values = (
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
        )

        assert all(value is False for value in prohibited_values)

        manifest_body = dict(first.__dict__)
        manifest_hash = manifest_body.pop(
            "activation_manifest_hash"
        )

        manifest_body["active_invocations"] = [
            dict(item.__dict__)
            for item in first.active_invocations
        ]

        assert manifest_hash == stable_hash(manifest_body)

        active_body = dict(active.__dict__)
        active_hash = active_body.pop(
            "active_execution_invocation_hash"
        )

        assert active_hash == stable_hash(active_body)

        assert (
            activation_directory / "current.json"
        ).exists()

        assert list(
            (
                activation_directory / "activations"
            ).glob("*.json")
        )

        assert list(
            (
                activation_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                activation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["callable_resolution_allowed"] is False
        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["invocations"][0][
            "invocation_arguments"
        ]["execute"] = True

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-045 invocation accepted."
            )

        seed_oia045(invocation_directory)

        tampered_adapter = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["invocations"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        invocation_payload = dict(
            tampered_adapter["invocations"][0]
        )
        invocation_payload.pop("execution_invocation_hash")

        tampered_adapter["invocations"][0][
            "execution_invocation_hash"
        ] = stable_hash(invocation_payload)

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("invocation_manifest_hash")

        tampered_adapter[
            "invocation_manifest_hash"
        ] = stable_hash(manifest_payload)

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter invocation was activated."
            )

        seed_oia045(invocation_directory)

        duplicate_work_item = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        duplicate = dict(
            duplicate_work_item["invocations"][0]
        )
        duplicate["sequence"] = 2
        duplicate.pop("execution_invocation_hash")
        duplicate["execution_invocation_hash"] = stable_hash(
            {
                key: value
                for key, value in duplicate.items()
                if key != "execution_invocation_hash"
            }
        )

        duplicate_work_item["invocations"].append(duplicate)
        duplicate_work_item["invocation_count"] = 2

        duplicate_manifest_body = dict(duplicate_work_item)
        duplicate_manifest_body.pop("invocation_manifest_hash")

        duplicate_work_item[
            "invocation_manifest_hash"
        ] = stable_hash(duplicate_manifest_body)

        (
            invocation_directory / "current.json"
        ).write_text(
            json.dumps(duplicate_work_item, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationActivationInvariantError:
            pass
        else:
            raise AssertionError(
                "Duplicate work-item invocation was activated."
            )

    print("[PASS] Actual OIA-045 execution-invocation contract consumed")
    print("[PASS] Activation manifest and active-invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-045 lineage preserved")
    print("[PASS] Exact authorized read-only invocation activated")
    print("[PASS] Active invocation arguments remained non-executing")
    print("[PASS] Callable resolution remained disabled")
    print("[PASS] No adapter was imported, resolved, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, or write-capable invocation rejected")
    print("[PASS] Atomic invocation-activation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
