import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_active_invocation_execution_authorization_gate import (
    ActiveInvocationExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate,
    POLICY_ID,
    STATUS_ACTIVE_INVOCATION_AUTHORIZED,
    STATUS_AUTHORIZATION_ISSUED,
    stable_hash,
)


def source_lineage() -> dict:
    return {
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


def seed_oia047(directory: Path) -> dict:
    readiness_entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation":
            "read_canonical_observations",
        "readiness_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
        },
        "readiness_checks": [
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
        ],
        "readiness_status":
            "evidence_read_execution_adapter_active_invocation_execution_ready",
        "source_active_execution_invocation_hash":
            stable_hash({"source": "oia046-active"}),
        "source_execution_invocation_hash":
            stable_hash({"source": "oia045-invocation"}),
        "source_authorization_entry_hash":
            stable_hash({"source": "oia044-authorization"}),
        "source_readiness_entry_hash":
            stable_hash({"source": "oia043-readiness"}),
        "source_active_adapter_invocation_hash":
            stable_hash({"source": "oia042-active"}),
    }

    readiness_entry = dict(readiness_entry_body)
    readiness_entry[
        "active_invocation_execution_readiness_hash"
    ] = stable_hash(readiness_entry_body)

    manifest_body = {
        "schema_version": "OIA-047",
        "engine_id": "OIA-047",
        "evaluated_at":
            "2026-07-22T05:00:00+00:00",
        "execution_readiness_id":
            "oia047-test-readiness",
        "execution_readiness_status":
            "evidence_read_execution_adapter_active_invocation_execution_readiness_issued",
        "execution_readiness_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "active-invocation-execution-readiness.v1",
        "worker_id":
            "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [readiness_entry],
        "source_invocation_activation_id":
            "oia046-test-activation",
        "source_invocation_activation_manifest_hash":
            stable_hash({"source": "oia046-manifest"}),
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
        "source_lineage":
            source_lineage(),
        "execution_readiness_issued": True,
        "execution_authorization_evaluation_allowed": True,
        "callable_resolution_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_allowed": False,
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
        "readiness_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload[
        "execution_readiness_manifest_hash"
    ] = stable_hash(manifest_body)

    directory.mkdir(parents=True, exist_ok=True)

    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def rehash_readiness(payload: dict) -> dict:
    for entry in payload["readiness_entries"]:
        entry_body = dict(entry)
        entry_body.pop(
            "active_invocation_execution_readiness_hash",
            None,
        )

        entry[
            "active_invocation_execution_readiness_hash"
        ] = stable_hash(entry_body)

    manifest_body = dict(payload)
    manifest_body.pop(
        "execution_readiness_manifest_hash",
        None,
    )

    payload[
        "execution_readiness_manifest_hash"
    ] = stable_hash(manifest_body)

    return payload


def expect_rejection(
    gate: OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate,
    authorized_at: datetime,
    message: str,
) -> None:
    try:
        gate.authorize(
            authorized_at=authorized_at,
            persist=False,
        )
    except ActiveInvocationExecutionAuthorizationInvariantError:
        return

    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-048 TEST")
    print(" ACTIVE INVOCATION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"

        source = seed_oia047(readiness_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterActiveInvocationExecutionAuthorizationGate(
                readiness_directory=readiness_directory,
                authorization_directory=authorization_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            6,
            0,
            tzinfo=timezone.utc,
        )

        first = gate.authorize(
            authorized_at=fixed,
            persist=True,
        )

        second = gate.authorize(
            authorized_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-048"
        assert first.engine_id == "OIA-048"

        assert (
            first.execution_authorization_status
            == STATUS_AUTHORIZATION_ISSUED
        )

        assert (
            first.execution_authorization_policy_id
            == POLICY_ID
        )

        assert first.authorization_entry_count == 1

        entry = first.authorization_entries[0]

        assert (
            entry.authorization_status
            == STATUS_ACTIVE_INVOCATION_AUTHORIZED
        )

        assert (
            entry.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            entry.read_operation
            == "read_canonical_observations"
        )

        assert entry.authorization_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
            "callable_resolution_authorized": True,
        }

        assert (
            entry.source_active_invocation_execution_readiness_hash
            == source["readiness_entries"][0][
                "active_invocation_execution_readiness_hash"
            ]
        )

        assert (
            entry.source_active_execution_invocation_hash
            == source["readiness_entries"][0][
                "source_active_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_execution_invocation_hash
            == source["readiness_entries"][0][
                "source_execution_invocation_hash"
            ]
        )

        assert (
            entry.source_authorization_entry_hash
            == source["readiness_entries"][0][
                "source_authorization_entry_hash"
            ]
        )

        assert (
            entry.source_readiness_entry_hash
            == source["readiness_entries"][0][
                "source_readiness_entry_hash"
            ]
        )

        assert (
            entry.source_active_adapter_invocation_hash
            == source["readiness_entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "execution_readiness_manifest_hash_verified",
            "execution_readiness_entry_hash_verified",
            "invocation_activation_lineage_verified",
            "execution_invocation_lineage_verified",
            "prior_authorization_lineage_verified",
            "prior_readiness_lineage_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "authorization_argument_allowlist_verified",
            "callable_resolution_authorized_but_not_requested",
            "callable_resolution_not_performed",
            "callable_binding_remained_disabled",
            "adapter_execution_remained_disabled",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(entry.authorization_checks))

        assert first.source_execution_readiness_id == (
            source["execution_readiness_id"]
        )

        assert (
            first.source_execution_readiness_manifest_hash
            == source["execution_readiness_manifest_hash"]
        )

        assert first.source_invocation_activation_id == (
            source["source_invocation_activation_id"]
        )

        assert (
            first.source_invocation_activation_manifest_hash
            == source[
                "source_invocation_activation_manifest_hash"
            ]
        )

        assert (
            first.source_execution_invocation_manifest_id
            == source[
                "source_execution_invocation_manifest_id"
            ]
        )

        assert (
            first.source_execution_invocation_manifest_hash
            == source[
                "source_execution_invocation_manifest_hash"
            ]
        )

        assert (
            first.source_prior_execution_authorization_id
            == source["source_execution_authorization_id"]
        )

        assert (
            first.source_prior_execution_authorization_manifest_hash
            == source[
                "source_execution_authorization_manifest_hash"
            ]
        )

        assert (
            first.source_prior_execution_readiness_id
            == source["source_execution_readiness_id"]
        )

        assert (
            first.source_prior_execution_readiness_manifest_hash
            == source[
                "source_execution_readiness_manifest_hash"
            ]
        )

        assert (
            first.source_activation_hash
            == source["source_activation_hash"]
        )

        assert first.source_lineage == source["source_lineage"]

        assert first.execution_authorization_issued is True
        assert first.callable_resolution_evaluation_allowed is True
        assert first.callable_resolution_allowed is False
        assert first.callable_resolution_performed is False
        assert first.callable_binding_allowed is False
        assert first.callable_binding_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        assert first.authorization_artifact_persistence_allowed is True

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
            "execution_authorization_manifest_hash"
        )

        manifest_body["authorization_entries"] = [
            dict(item.__dict__)
            for item in first.authorization_entries
        ]

        assert manifest_hash == stable_hash(manifest_body)

        entry_body = dict(entry.__dict__)
        entry_hash = entry_body.pop(
            "active_invocation_execution_authorization_hash"
        )

        assert entry_hash == stable_hash(entry_body)

        assert (
            authorization_directory / "current.json"
        ).exists()

        assert list(
            (
                authorization_directory
                / "authorizations"
            ).glob("*.json")
        )

        assert list(
            (
                authorization_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["execution_authorization_issued"] is True

        assert (
            current[
                "callable_resolution_evaluation_allowed"
            ]
            is True
        )

        assert current["callable_resolution_allowed"] is False
        assert current["callable_resolution_performed"] is False
        assert current["callable_binding_allowed"] is False
        assert current["callable_binding_performed"] is False
        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["corpus_read_execution_allowed"] is False
        assert current["corpus_read_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered_execute = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_execute["readiness_entries"][0][
            "readiness_arguments"
        ]["execute"] = True

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered_execute, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Tampered executable OIA-047 readiness accepted.",
        )

        seed_oia047(readiness_directory)

        resolution_requested = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        resolution_requested["readiness_entries"][0][
            "readiness_arguments"
        ]["callable_resolution_requested"] = True

        rehash_readiness(resolution_requested)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(resolution_requested, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Premature callable-resolution request was authorized.",
        )

        seed_oia047(readiness_directory)

        write_capable = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        write_capable["readiness_entries"][0][
            "adapter_id"
        ] = "oracle_write_capable_observation_adapter.v1"

        rehash_readiness(write_capable)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(write_capable, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Write-capable adapter was execution-authorized.",
        )

        seed_oia047(readiness_directory)

        unsafe_operation = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        unsafe_operation["readiness_entries"][0][
            "read_operation"
        ] = "update_canonical_observations"

        rehash_readiness(unsafe_operation)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(unsafe_operation, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Mutating operation was execution-authorized.",
        )

        seed_oia047(readiness_directory)

        duplicate = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        duplicate_entry = dict(
            duplicate["readiness_entries"][0]
        )

        duplicate_entry["sequence"] = 2

        duplicate["readiness_entries"].append(
            duplicate_entry
        )

        duplicate["readiness_entry_count"] = 2

        rehash_readiness(duplicate)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(duplicate, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Duplicate readiness work item was authorized.",
        )

        seed_oia047(readiness_directory)

        missing_lineage = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        del missing_lineage["source_lineage"][
            "source_evidence_manifest_id"
        ]

        rehash_readiness(missing_lineage)

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(missing_lineage, indent=2) + "\n",
            encoding="utf-8",
        )

        expect_rejection(
            gate,
            fixed,
            "Incomplete OIA-020 through OIA-047 lineage was authorized.",
        )

    print("[PASS] Actual OIA-047 execution-readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-047 lineage preserved")
    print("[PASS] Exact readiness-certified read-only invocation authorized")
    print("[PASS] Callable-resolution evaluation authorized")
    print("[PASS] Callable resolution itself remained disabled")
    print("[PASS] No adapter was imported, resolved, bound, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, mutating, or write-capable input rejected")
    print("[PASS] Atomic execution-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
