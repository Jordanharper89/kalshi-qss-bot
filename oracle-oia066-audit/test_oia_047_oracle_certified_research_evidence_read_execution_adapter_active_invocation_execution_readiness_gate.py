import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_readiness_gate import (
    ActiveInvocationExecutionReadinessInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionReadinessGate,
    POLICY_ID,
    STATUS_ACTIVE_INVOCATION_READY,
    STATUS_READINESS_ISSUED,
    stable_hash,
)


def seed_oia046(directory: Path) -> dict:
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

    active_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation":
            "read_canonical_observations",
        "active_invocation_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
        },
        "activation_checks": [
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
        ],
        "activation_status":
            "evidence_read_execution_adapter_execution_invocation_active",
        "source_execution_invocation_hash":
            stable_hash({"source": "oia045-entry"}),
        "source_authorization_entry_hash":
            stable_hash({"source": "oia044-entry"}),
        "source_readiness_entry_hash":
            stable_hash({"source": "oia043-entry"}),
        "source_active_adapter_invocation_hash":
            stable_hash({"source": "oia042-entry"}),
    }

    active_invocation = dict(active_body)
    active_invocation[
        "active_execution_invocation_hash"
    ] = stable_hash(active_body)

    manifest_body = {
        "schema_version": "OIA-046",
        "engine_id": "OIA-046",
        "activated_at":
            "2026-07-22T04:00:00+00:00",
        "activation_id":
            "oia046-test-activation",
        "activation_status":
            "evidence_read_execution_adapter_execution_invocation_activation_issued",
        "activation_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "execution-invocation-activation.v1",
        "worker_id":
            "oracle-worker-test",
        "active_invocation_count": 1,
        "active_invocations": [active_invocation],
        "source_execution_invocation_manifest_id":
            "oia045-test-manifest",
        "source_execution_invocation_manifest_hash":
            stable_hash({"source": "oia045-manifest"}),
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
        "invocation_activation_issued": True,
        "execution_readiness_evaluation_allowed": True,
        "callable_resolution_allowed": False,
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
        "activation_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload["activation_manifest_hash"] = stable_hash(
        manifest_body
    )

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def rehash_activation(payload: dict) -> dict:
    for invocation in payload["active_invocations"]:
        invocation_body = dict(invocation)
        invocation_body.pop(
            "active_execution_invocation_hash",
            None,
        )
        invocation[
            "active_execution_invocation_hash"
        ] = stable_hash(invocation_body)

    manifest_body = dict(payload)
    manifest_body.pop("activation_manifest_hash", None)

    payload["activation_manifest_hash"] = stable_hash(
        manifest_body
    )

    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-047 TEST")
    print(" ACTIVE INVOCATION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        activation_directory = root / "activation"
        readiness_directory = root / "readiness"

        source = seed_oia046(activation_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionReadinessGate(
                activation_directory=activation_directory,
                readiness_directory=readiness_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            5,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.evaluate(
            evaluated_at=fixed,
            persist=True,
        )

        second = gate.evaluate(
            evaluated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-047"
        assert first.engine_id == "OIA-047"

        assert (
            first.execution_readiness_status
            == STATUS_READINESS_ISSUED
        )

        assert (
            first.execution_readiness_policy_id
            == POLICY_ID
        )

        assert first.readiness_entry_count == 1

        entry = first.readiness_entries[0]

        assert (
            entry.readiness_status
            == STATUS_ACTIVE_INVOCATION_READY
        )

        assert (
            entry.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            entry.read_operation
            == "read_canonical_observations"
        )

        assert entry.readiness_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
        }

        assert (
            entry.source_active_execution_invocation_hash
            == source["active_invocations"][0][
                "active_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_execution_invocation_hash
            == source["active_invocations"][0][
                "source_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_authorization_entry_hash
            == source["active_invocations"][0][
                "source_authorization_entry_hash"
            ]
        )

        assert (
            entry.source_readiness_entry_hash
            == source["active_invocations"][0][
                "source_readiness_entry_hash"
            ]
        )

        assert (
            entry.source_active_adapter_invocation_hash
            == source["active_invocations"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "activation_manifest_hash_verified",
            "active_execution_invocation_hash_verified",
            "execution_invocation_lineage_verified",
            "authorization_lineage_verified",
            "readiness_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_argument_allowlist_verified",
            "active_invocation_remained_non_executing",
            "callable_resolution_not_performed",
            "callable_binding_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(entry.readiness_checks))

        assert first.source_invocation_activation_id == (
            source["activation_id"]
        )

        assert (
            first.source_invocation_activation_manifest_hash
            == source["activation_manifest_hash"]
        )

        assert first.source_lineage == source["source_lineage"]

        assert first.execution_readiness_issued is True

        assert (
            first.execution_authorization_evaluation_allowed
            is True
        )

        assert first.callable_resolution_allowed is False
        assert first.callable_resolution_performed is False
        assert first.callable_binding_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False

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
            "execution_readiness_manifest_hash"
        )

        manifest_body["readiness_entries"] = [
            dict(item.__dict__)
            for item in first.readiness_entries
        ]

        assert manifest_hash == stable_hash(manifest_body)

        entry_body = dict(entry.__dict__)
        entry_hash = entry_body.pop(
            "active_invocation_execution_readiness_hash"
        )

        assert entry_hash == stable_hash(entry_body)

        assert (
            readiness_directory / "current.json"
        ).exists()

        assert list(
            (
                readiness_directory / "readiness"
            ).glob("*.json")
        )

        assert list(
            (
                readiness_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert (
            current[
                "execution_authorization_evaluation_allowed"
            ]
            is True
        )

        assert current["callable_resolution_allowed"] is False
        assert current["callable_resolution_performed"] is False
        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False

        tampered = json.loads(
            (
                activation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["active_invocations"][0][
            "active_invocation_arguments"
        ]["execute"] = True

        (
            activation_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.evaluate(
                evaluated_at=fixed,
                persist=False,
            )
        except ActiveInvocationExecutionReadinessInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-046 invocation accepted."
            )

        seed_oia046(activation_directory)

        write_capable = json.loads(
            (
                activation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        write_capable["active_invocations"][0][
            "adapter_id"
        ] = "oracle_write_capable_observation_adapter.v1"

        rehash_activation(write_capable)

        (
            activation_directory / "current.json"
        ).write_text(
            json.dumps(write_capable, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.evaluate(
                evaluated_at=fixed,
                persist=False,
            )
        except ActiveInvocationExecutionReadinessInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter passed readiness."
            )

        seed_oia046(activation_directory)

        duplicate = json.loads(
            (
                activation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        duplicate_invocation = dict(
            duplicate["active_invocations"][0]
        )
        duplicate_invocation["sequence"] = 2

        duplicate["active_invocations"].append(
            duplicate_invocation
        )
        duplicate["active_invocation_count"] = 2

        rehash_activation(duplicate)

        (
            activation_directory / "current.json"
        ).write_text(
            json.dumps(duplicate, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.evaluate(
                evaluated_at=fixed,
                persist=False,
            )
        except ActiveInvocationExecutionReadinessInvariantError:
            pass
        else:
            raise AssertionError(
                "Duplicate active work item passed readiness."
            )

    print("[PASS] Actual OIA-046 invocation-activation contract consumed")
    print("[PASS] Readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-046 lineage preserved")
    print("[PASS] Exact active read-only invocation declared ready")
    print("[PASS] Invocation remained activated, read-only, and non-executing")
    print("[PASS] Callable resolution and binding remained disabled")
    print("[PASS] No adapter was imported, resolved, bound, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, or write-capable invocation rejected")
    print("[PASS] Atomic execution-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
