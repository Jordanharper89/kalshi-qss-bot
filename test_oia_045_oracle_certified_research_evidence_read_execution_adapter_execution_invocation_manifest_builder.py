import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_execution_invocation_manifest_builder import (
    AdapterExecutionInvocationInvariantError,
    OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder,
    POLICY_ID,
    STATUS_INVOCATION_READY,
    STATUS_MANIFEST_ISSUED,
    stable_hash,
)


def seed_oia044(directory: Path) -> dict:
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

    authorization_entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id":
            "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "authorized_invocation_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
        },
        "authorization_checks": [
            "readiness_manifest_hash_verified",
            "readiness_entry_hash_verified",
            "active_invocation_hash_verified",
            "adapter_read_only_identity_verified",
            "operation_read_only_verified",
            "invocation_arguments_allowlisted",
            "invocation_remained_non_executing",
            "corpus_execution_remained_disabled",
            "oracle_qseries_boundary_verified",
        ],
        "authorization_status":
            "evidence_read_execution_adapter_execution_authorized",
        "source_readiness_entry_hash": stable_hash(
            {"source": "oia043-entry"}
        ),
        "source_active_adapter_invocation_hash": stable_hash(
            {"source": "oia042-active-invocation"}
        ),
    }

    authorization_entry = dict(authorization_entry_body)
    authorization_entry["authorization_entry_hash"] = stable_hash(
        authorization_entry_body
    )

    manifest_body = {
        "schema_version": "OIA-044",
        "engine_id": "OIA-044",
        "authorized_at": "2026-07-22T02:00:00+00:00",
        "authorization_id": "oia044-test-authorization",
        "authorization_status":
            "evidence_read_execution_adapter_execution_authorization_issued",
        "authorization_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "execution-authorization.v1",
        "worker_id": "oracle-worker-test",
        "authorization_entry_count": 1,
        "entries": [authorization_entry],
        "source_execution_readiness_id":
            "oia043-test-readiness",
        "source_execution_readiness_manifest_hash": stable_hash(
            {"source": "oia043-manifest"}
        ),
        "source_activation_hash": stable_hash(
            {"source": "oia042-activation"}
        ),
        "source_lineage": source_lineage,
        "read_only_authorization_issued": True,
        "adapter_execution_authorization_allowed": True,
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
        "authorization_artifact_persistence_allowed": True,
    }

    payload = dict(manifest_body)
    payload["authorization_manifest_hash"] = stable_hash(
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
    print(" OIA-045 TEST")
    print(" ADAPTER EXECUTION INVOCATION MANIFEST")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization_directory = root / "authorization"
        invocation_directory = root / "invocations"

        source = seed_oia044(authorization_directory)

        builder = (
            OracleCertifiedResearchEvidenceReadExecutionAdapterExecutionInvocationManifestBuilder(
                authorization_directory=authorization_directory,
                invocation_directory=invocation_directory,
            )
        )

        fixed = datetime(
            2026,
            7,
            22,
            3,
            0,
            tzinfo=timezone.utc,
        )

        first = builder.build(
            created_at=fixed,
            persist=True,
        )

        second = builder.build(
            created_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "OIA-045"
        assert first.engine_id == "OIA-045"
        assert (
            first.invocation_manifest_status
            == STATUS_MANIFEST_ISSUED
        )
        assert first.invocation_policy_id == POLICY_ID
        assert first.invocation_count == 1

        invocation = first.invocations[0]

        assert (
            invocation.invocation_status
            == STATUS_INVOCATION_READY
        )

        assert (
            invocation.adapter_id
            == "oracle_read_only_canonical_observation_adapter.v1"
        )

        assert (
            invocation.read_operation
            == "read_canonical_observations"
        )

        assert invocation.invocation_arguments == {
            "activated": True,
            "read_only": True,
            "execute": False,
        }

        assert invocation.source_authorization_entry_hash == (
            source["entries"][0]["authorization_entry_hash"]
        )

        assert invocation.source_readiness_entry_hash == (
            source["entries"][0]["source_readiness_entry_hash"]
        )

        assert (
            invocation.source_active_adapter_invocation_hash
            == source["entries"][0][
                "source_active_adapter_invocation_hash"
            ]
        )

        assert {
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
        }.issubset(set(invocation.invocation_checks))

        assert first.source_execution_authorization_id == (
            source["authorization_id"]
        )

        assert (
            first.source_execution_authorization_manifest_hash
            == source["authorization_manifest_hash"]
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
        assert first.invocation_manifest_created is True
        assert first.invocation_activation_allowed is True
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.invocation_artifact_persistence_allowed is True

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
            "invocation_manifest_hash"
        )
        manifest_body["invocations"] = [
            dict(item.__dict__)
            for item in first.invocations
        ]

        assert manifest_hash == stable_hash(manifest_body)

        invocation_body = dict(invocation.__dict__)
        invocation_hash = invocation_body.pop(
            "execution_invocation_hash"
        )

        assert invocation_hash == stable_hash(invocation_body)

        assert (
            invocation_directory / "current.json"
        ).exists()

        assert list(
            (
                invocation_directory / "manifests"
            ).glob("*.json")
        )

        assert list(
            (
                invocation_directory
                / "workers"
                / first.worker_id
            ).glob("*.json")
        )

        current = json.loads(
            (
                invocation_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        assert current["adapter_execution_allowed"] is False
        assert current["adapter_execution_performed"] is False
        assert current["execution_allowed"] is False
        assert current["qseries_handoff_allowed"] is False

        tampered = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered["entries"][0][
            "authorized_invocation_arguments"
        ]["execute"] = True

        (
            authorization_directory / "current.json"
        ).write_text(
            json.dumps(tampered, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            builder.build(
                created_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered executable OIA-044 authorization accepted."
            )

        seed_oia044(authorization_directory)

        tampered_adapter = json.loads(
            (
                authorization_directory / "current.json"
            ).read_text(encoding="utf-8")
        )

        tampered_adapter["entries"][0]["adapter_id"] = (
            "oracle_write_capable_observation_adapter.v1"
        )

        entry_payload = dict(tampered_adapter["entries"][0])
        entry_payload.pop("authorization_entry_hash")

        tampered_adapter["entries"][0][
            "authorization_entry_hash"
        ] = stable_hash(entry_payload)

        manifest_payload = dict(tampered_adapter)
        manifest_payload.pop("authorization_manifest_hash")

        tampered_adapter[
            "authorization_manifest_hash"
        ] = stable_hash(manifest_payload)

        (
            authorization_directory / "current.json"
        ).write_text(
            json.dumps(tampered_adapter, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            builder.build(
                created_at=fixed,
                persist=False,
            )
        except AdapterExecutionInvocationInvariantError:
            pass
        else:
            raise AssertionError(
                "Write-capable adapter invocation was accepted."
            )

    print("[PASS] Actual OIA-044 execution-authorization contract consumed")
    print("[PASS] Invocation manifest and invocation hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-044 lineage preserved")
    print("[PASS] Exact authorized read-only invocation recorded")
    print("[PASS] Invocation arguments remained non-executing")
    print("[PASS] No adapter was imported, resolved, invoked, or executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered or write-capable authorization rejected")
    print("[PASS] Atomic execution-invocation artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
