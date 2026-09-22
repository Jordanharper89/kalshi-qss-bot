import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_authorization_gate import (
    AdapterExecutionAuthorizationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate,
    POLICY_ID,
    STATUS_AUTHORIZED,
    STATUS_ISSUED,
    stable_hash,
)


def seed_oia043(directory: Path) -> dict:
    active_invocation = {
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
        "activation_status":
            "evidence_read_execution_adapter_invocation_active",
    }

    active_invocation["active_adapter_invocation_hash"] = stable_hash(
        active_invocation
    )

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

    readiness_entry_body = {
        "sequence": 1,
        "worker_id": active_invocation["worker_id"],
        "work_item_id": active_invocation["work_item_id"],
        "adapter_id": active_invocation["adapter_id"],
        "read_operation": active_invocation["read_operation"],
        "invocation_arguments":
            dict(active_invocation["invocation_arguments"]),
        "checks": [
            "activation_hash_verified",
            "adapter_read_only_verified",
            "operation_read_only_verified",
            "invocation_non_executing_verified",
            "corpus_execution_disabled",
        ],
        "status":
            "evidence_read_execution_adapter_execution_ready",
        "source_active_adapter_invocation_hash":
            active_invocation["active_adapter_invocation_hash"],
    }

    readiness_entry = dict(readiness_entry_body)
    readiness_entry["entry_hash"] = stable_hash(
        readiness_entry_body
    )

    activation_hash = stable_hash(
        {
            "schema_version": "OIA-042",
            "engine_id": "OIA-042",
            "active_adapter_invocation":
                active_invocation["active_adapter_invocation_hash"],
        }
    )

    manifest_body = {
        "schema_version": "OIA-043",
        "engine_id": "OIA-043",
        "evaluated_at": "2026-07-22T01:00:00+00:00",
        "readiness_id": "oia043-test-readiness",
        "status":
            "evidence_read_execution_adapter_execution_readiness_issued",
        "worker_id": "oracle-worker-test",
        "entries": [readiness_entry],
        "source_activation_hash": activation_hash,
        "source_lineage": source_lineage,
        "corpus_read_execution_allowed": False,
        "research_execution_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_allowed": False,
        "source_mutation_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
    }

    payload = dict(manifest_body)
    payload["manifest_hash"] = stable_hash(manifest_body)

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> int:
    print("=" * 40)
    print(" OIA-044 TEST")
    print(" ADAPTER EXECUTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness_directory = root / "readiness"
        authorization_directory = root / "authorization"

        source = seed_oia043(readiness_directory)

        gate = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionAuthorizationGate(
                readiness_directory=readiness_directory,
                authorization_directory=authorization_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            2,
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
        assert first.schema_version == "OIA-044"
        assert first.engine_id == "OIA-044"
        assert first.authorization_status == STATUS_ISSUED
        assert first.authorization_policy_id == POLICY_ID
        assert first.authorization_entry_count == 1

        entry = first.entries[0]

        assert entry.authorization_status == STATUS_AUTHORIZED
        assert (
            entry.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )
        assert entry.read_operation == "read_canonical_observations"
        assert entry.authorized_invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert entry.source_readiness_entry_hash == (
            source["entries"][0]["entry_hash"]
        )

        assert entry.source_active_adapter_invocation_hash == (
            source["entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        }.issubset(set(entry.authorization_checks))

        assert first.source_execution_readiness_id == (
            source["readiness_id"]
        )

        assert first.source_execution_readiness_manifest_hash == (
            source["manifest_hash"]
        )

        assert first.source_lineage == source["source_lineage"]
        assert first.read_only_authorization_issued is True
        assert first.adapter_execution_authorization_allowed is True
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.authorization_artifact_persistence_allowed is True

        for prohibited_value in (
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
            assert prohibited_value is False

        manifest_body = dict(first.__dict__)
        manifest_hash = manifest_body.pop(
            "authorization_manifest_hash"
        )
        manifest_body["entries"] = [
            dict(item.__dict__) for item in first.entries
        ]
        assert manifest_hash == stable_hash(manifest_body)

        entry_body = dict(entry.__dict__)
        entry_hash = entry_body.pop(
            "authorization_entry_hash"
        )
        assert entry_hash == stable_hash(entry_body)

        assert (
            authorization_directory / "current.json"
        ).exists()

        assert list(
            (
                authorization_directory / "authorizations"
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

        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["entries"][0]["invocation_arguments"][
            "execute"
        ] = True

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.authorize(
                authorized_at=fixed,
                persist=False,
            )
        except AdapterExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-043 readiness accepted."
            )

        seed_oia043(readiness_directory)

        tampered_adapter = json.loads(
            (
                readiness_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["entries"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        entry_payload = dict(tampered_adapter["entries"][0])
        entry_payload.pop("entry_hash")
        tampered_adapter["entries"][0]["entry_hash"] = stable_hash(
            entry_payload
        )

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("manifest_hash")
        tampered_adapter["manifest_hash"] = stable_hash(
            manifest_payload
        )

        (
            readiness_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            gate.authorize(
                authorized_at=fixed,
                persist=False,
            )
        except AdapterExecutionAuthorizationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter identity was authorized."
            )

    print("[PASS] Actual OIA-043 execution-readiness contract consumed")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-043 lineage preserved")
    print("[PASS] Only readiness-certified read-only adapter execution authorized")
    print("[PASS] Invocation arguments remained non-executing")
    print("[PASS] Authorization did not invoke or execute an adapter")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable readiness rejected")
    print("[PASS] Atomic execution-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
