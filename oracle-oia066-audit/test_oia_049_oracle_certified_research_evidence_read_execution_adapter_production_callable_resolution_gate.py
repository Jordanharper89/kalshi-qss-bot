import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_resolution_gate import (
    APPROVED_PRODUCTION_CALLABLE_REGISTRY,
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableResolutionGate,
    ProductionCallableResolutionInvariantError,
    STATUS_CALLABLE_RESOLVED,
    STATUS_RESOLUTION_MANIFEST_ISSUED,
    stable_hash,
)


def lineage() -> dict:
    return {
        "source_evidence_read_execution_adapter_invocation_manifest_id": "oia041-test",
        "source_evidence_read_execution_adapter_authorization_manifest_id": "oia040-test",
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
        "dispatch_manifest_id": "oia020-test",
        "selected_batch_id": "oia020-batch",
        "selected_batch_number": 1,
    }


def authorization_entry(adapter_id: str, operation: str, sequence: int) -> dict:
    body = {
        "sequence": sequence,
        "worker_id": "oracle-worker-test",
        "work_item_id": f"work.test.{sequence}",
        "adapter_id": adapter_id,
        "read_operation": operation,
        "authorization_arguments": {
            "activated": True,
            "read_only": True,
            "execute": False,
            "callable_resolution_requested": False,
            "callable_resolution_authorized": True,
        },
        "authorization_checks": [
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
        ],
        "authorization_status":
            "evidence_read_execution_adapter_active_invocation_execution_authorized",
        "source_active_invocation_execution_readiness_hash": stable_hash({"s": sequence, "n": 47}),
        "source_active_execution_invocation_hash": stable_hash({"s": sequence, "n": 46}),
        "source_execution_invocation_hash": stable_hash({"s": sequence, "n": 45}),
        "source_authorization_entry_hash": stable_hash({"s": sequence, "n": 44}),
        "source_readiness_entry_hash": stable_hash({"s": sequence, "n": 43}),
        "source_active_adapter_invocation_hash": stable_hash({"s": sequence, "n": 42}),
    }
    body["active_invocation_execution_authorization_hash"] = stable_hash(body)
    return body


def seed(directory: Path) -> dict:
    entries = [
        authorization_entry(
            "oracle_read_only_canonical_observation_adapter.v1",
            "read_canonical_observations",
            1,
        ),
        authorization_entry(
            "oracle_read_only_market_state_lineage_adapter.v1",
            "read_market_state_lineage",
            2,
        ),
    ]
    body = {
        "schema_version": "OIA-048",
        "engine_id": "OIA-048",
        "authorized_at": "2026-07-22T06:00:00+00:00",
        "execution_authorization_id": "oia048-test",
        "execution_authorization_status":
            "evidence_read_execution_adapter_active_invocation_execution_authorization_issued",
        "execution_authorization_policy_id":
            "oracle.certified-research-evidence-read-execution-adapter-"
            "active-invocation-execution-authorization.v1",
        "worker_id": "oracle-worker-test",
        "authorization_entry_count": len(entries),
        "authorization_entries": entries,
        "source_execution_readiness_id": "oia047-test",
        "source_execution_readiness_manifest_hash": stable_hash({"n": 47}),
        "source_invocation_activation_id": "oia046-test",
        "source_invocation_activation_manifest_hash": stable_hash({"n": 46}),
        "source_execution_invocation_manifest_id": "oia045-test",
        "source_execution_invocation_manifest_hash": stable_hash({"n": 45}),
        "source_prior_execution_authorization_id": "oia044-test",
        "source_prior_execution_authorization_manifest_hash": stable_hash({"n": 44}),
        "source_prior_execution_readiness_id": "oia043-test",
        "source_prior_execution_readiness_manifest_hash": stable_hash({"n": 43}),
        "source_activation_hash": stable_hash({"n": 42}),
        "source_lineage": lineage(),
        "execution_authorization_issued": True,
        "callable_resolution_evaluation_allowed": True,
        "callable_resolution_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_allowed": False,
        "callable_binding_performed": False,
        "adapter_execution_allowed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_allowed": False,
        "corpus_read_execution_performed": False,
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
    payload = dict(body)
    payload["execution_authorization_manifest_hash"] = stable_hash(body)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["authorization_entries"]:
        body = dict(entry)
        body.pop("active_invocation_execution_authorization_hash", None)
        entry["active_invocation_execution_authorization_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("execution_authorization_manifest_hash", None)
    payload["execution_authorization_manifest_hash"] = stable_hash(body)


def expect_rejection(gate, timestamp, message):
    try:
        gate.resolve(resolved_at=timestamp, persist=False)
    except ProductionCallableResolutionInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-049 TEST")
    print(" PRODUCTION CALLABLE RESOLUTION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization_directory = root / "authorization"
        resolution_directory = root / "resolution"
        source = seed(authorization_directory)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableResolutionGate(
            authorization_directory=authorization_directory,
            resolution_directory=resolution_directory,
        )
        timestamp = datetime(2026, 7, 22, 7, 0, tzinfo=timezone.utc)
        first = gate.resolve(resolved_at=timestamp, persist=True)
        second = gate.resolve(resolved_at=timestamp, persist=False)
        assert first == second
        assert first.schema_version == "OIA-049"
        assert first.engine_id == "OIA-049"
        assert first.callable_resolution_status == STATUS_RESOLUTION_MANIFEST_ISSUED
        assert first.resolution_entry_count == 2
        assert first.approved_registry_hash == stable_hash({
            key: dict(value)
            for key, value in APPROVED_PRODUCTION_CALLABLE_REGISTRY.items()
        })
        expected = {
            "oracle_read_only_canonical_observation_adapter.v1": (
                "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
                "OracleLiveCorpusInspector",
                "inspect",
            ),
            "oracle_read_only_market_state_lineage_adapter.v1": (
                "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
                "OracleCanonicalMarketLineageLedger",
                "records",
            ),
        }
        for entry in first.resolution_entries:
            assert entry.resolution_status == STATUS_CALLABLE_RESOLVED
            assert (
                entry.module_path,
                entry.owner_name,
                entry.callable_name,
            ) == expected[entry.adapter_id]
            assert entry.module_imported is True
            assert entry.owner_resolved is True
            assert entry.callable_resolved is True
            assert entry.owner_instantiated is False
            assert entry.callable_bound is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            body = dict(entry.__dict__)
            entry_hash = body.pop("callable_resolution_hash")
            assert entry_hash == stable_hash(body)
        assert first.source_execution_authorization_manifest_hash == source[
            "execution_authorization_manifest_hash"
        ]
        assert first.source_lineage == source["source_lineage"]
        assert first.callable_resolution_issued is True
        assert first.module_import_allowed is True
        assert first.module_import_performed is True
        assert first.owner_resolution_allowed is True
        assert first.owner_resolution_performed is True
        assert first.callable_resolution_allowed is True
        assert first.callable_resolution_performed is True
        assert first.owner_instantiation_allowed is False
        assert first.owner_instantiation_performed is False
        assert first.callable_binding_allowed is False
        assert first.callable_binding_performed is False
        assert first.adapter_invocation_allowed is False
        assert first.adapter_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        prohibited = (
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
        assert all(value is False for value in prohibited)
        body = dict(first.__dict__)
        manifest_hash = body.pop("callable_resolution_manifest_hash")
        body["resolution_entries"] = [
            dict(entry.__dict__) for entry in first.resolution_entries
        ]
        assert manifest_hash == stable_hash(body)
        assert (resolution_directory / "current.json").exists()
        assert list((resolution_directory / "resolutions").glob("*.json"))
        assert list((resolution_directory / "workers" / first.worker_id).glob("*.json"))

        tampered = json.loads((authorization_directory / "current.json").read_text())
        tampered["authorization_entries"][0]["authorization_arguments"]["execute"] = True
        rehash(tampered)
        (authorization_directory / "current.json").write_text(json.dumps(tampered))
        expect_rejection(gate, timestamp, "Executable invocation was resolved.")

        seed(authorization_directory)
        unknown = json.loads((authorization_directory / "current.json").read_text())
        unknown["authorization_entries"][0]["adapter_id"] = "oracle_read_only_unknown_adapter.v1"
        rehash(unknown)
        (authorization_directory / "current.json").write_text(json.dumps(unknown))
        expect_rejection(gate, timestamp, "Unknown adapter was resolved.")

        seed(authorization_directory)
        mismatch = json.loads((authorization_directory / "current.json").read_text())
        mismatch["authorization_entries"][0]["read_operation"] = "read_market_state_lineage"
        rehash(mismatch)
        (authorization_directory / "current.json").write_text(json.dumps(mismatch))
        expect_rejection(gate, timestamp, "Adapter-operation mismatch was resolved.")

        seed(authorization_directory)
        duplicate = json.loads((authorization_directory / "current.json").read_text())
        duplicate["authorization_entries"][1]["work_item_id"] = duplicate["authorization_entries"][0]["work_item_id"]
        rehash(duplicate)
        (authorization_directory / "current.json").write_text(json.dumps(duplicate))
        expect_rejection(gate, timestamp, "Duplicate work item was resolved.")

    print("[PASS] Actual OIA-048 execution-authorization contract consumed")
    print("[PASS] Actual OIA-038 approved adapter identities preserved")
    print("[PASS] Production modules imported from repository-verified paths")
    print("[PASS] Approved owner classes and public methods resolved")
    print("[PASS] Resolution manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-048 lineage preserved")
    print("[PASS] Owners were not instantiated and callables were not bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Unknown, mismatched, duplicate, or executable input rejected")
    print("[PASS] Atomic callable-resolution artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
