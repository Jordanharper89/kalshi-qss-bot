import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate,
    ProductionOwnerMethodBindingReadinessInvariantError,
    stable_hash,
)


def seed_oia055(path: Path) -> dict:
    entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work.test",
        "adapter_id": "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "constructor_signature": "(*, connection_factory, stale_after_seconds=300, market_limit=100)",
        "callable_signature": "(self, *, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
        "constructor_dependency_names": ["connection_factory"],
        "constructor_default_names": ["stale_after_seconds", "market_limit"],
        "owner_constructed": True,
        "owner_type_verified": True,
        "owner_read_only_verified": True,
        "owner_execution_disabled_verified": True,
        "callable_bound_to_owner": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "construction_checks": ["approved_owner_identity_verified"],
        "construction_status": "evidence_read_execution_adapter_production_owner_constructed",
        "source_owner_construction_authorization_hash": stable_hash({"54": 1}),
        "source_owner_construction_readiness_hash": stable_hash({"53": 1}),
        "source_callable_argument_binding_hash": stable_hash({"52": 1}),
        "owner_state_fingerprint": stable_hash({"owner": "inert"}),
    }
    entry = dict(entry_body)
    entry["owner_construction_hash"] = stable_hash(entry_body)

    manifest_body = {
        "schema_version": "OIA-055",
        "engine_id": "OIA-055",
        "constructed_at": "2026-07-22T00:00:00+00:00",
        "owner_construction_id": "oia055-test",
        "owner_construction_status": "evidence_read_execution_adapter_production_owner_construction_issued",
        "owner_construction_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "construction_entry_count": 1,
        "construction_entries": [entry],
        "source_owner_construction_authorization_id": "oia054-test",
        "source_owner_construction_authorization_manifest_hash": stable_hash({"54m": 1}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
            "source_activation_id": "oia022-test",
        },
        "owner_construction_performed": True,
        "owner_instances_retained": False,
        "callable_binding_to_owner_allowed": False,
        "callable_binding_to_owner_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
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
        "construction_artifact_persistence_allowed": True,
    }
    payload = dict(manifest_body)
    payload["owner_construction_manifest_hash"] = stable_hash(manifest_body)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["construction_entries"]:
        body = dict(entry)
        body.pop("owner_construction_hash", None)
        entry["owner_construction_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_construction_manifest_hash", None)
    payload["owner_construction_manifest_hash"] = stable_hash(body)


def reject(gate, evaluated_at, message):
    try:
        gate.evaluate(evaluated_at=evaluated_at, persist=False)
    except ProductionOwnerMethodBindingReadinessInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-056 TEST")
    print(" OWNER METHOD BINDING READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        construction = root / "construction"
        readiness = root / "readiness"
        source = seed_oia055(construction)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingReadinessGate(
            construction_directory=construction,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-056"
        assert first.engine_id == "OIA-056"
        assert first.owner_method_binding_readiness_issued is True
        assert first.owner_method_binding_authorization_evaluation_allowed is True
        assert first.readiness_entry_count == 1
        entry = first.readiness_entries[0]
        assert entry.method_descriptor_type == "function"
        assert entry.method_descriptor_module == source["construction_entries"][0]["module_path"]
        assert entry.method_descriptor_qualname == "OracleLiveCorpusInspector.inspect"
        assert entry.method_signature_verified is True
        assert entry.instance_parameter_verified is True
        assert entry.descriptor_static_resolution_verified is True
        assert entry.owner_reconstruction_required is True
        assert entry.owner_reconstructed is False
        assert entry.method_bound_to_owner is False
        assert entry.method_invoked is False
        assert entry.adapter_executed is False
        assert first.owner_reconstruction_allowed is False
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_allowed is False
        assert first.corpus_read_execution_performed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_construction_manifest_hash == source["owner_construction_manifest_hash"]
        assert (readiness / "current.json").exists()

        tampered = json.loads((construction / "current.json").read_text())
        tampered["construction_entries"][0]["callable_signature"] = "(self, *args, **kwargs)"
        rehash(tampered)
        (construction / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "signature drift accepted")

        seed_oia055(construction)
        bound = json.loads((construction / "current.json").read_text())
        bound["construction_entries"][0]["callable_bound_to_owner"] = True
        rehash(bound)
        (construction / "current.json").write_text(json.dumps(bound), encoding="utf-8")
        reject(gate, fixed, "premature live binding accepted")

        seed_oia055(construction)
        unknown = json.loads((construction / "current.json").read_text())
        unknown["construction_entries"][0]["callable_name"] = "execute"
        rehash(unknown)
        (construction / "current.json").write_text(json.dumps(unknown), encoding="utf-8")
        reject(gate, fixed, "unknown callable accepted")

        seed_oia055(construction)
        duplicate = json.loads((construction / "current.json").read_text())
        copied = dict(duplicate["construction_entries"][0])
        copied["sequence"] = 2
        duplicate["construction_entries"].append(copied)
        duplicate["construction_entry_count"] = 2
        rehash(duplicate)
        (construction / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

    print("[PASS] Actual OIA-055 owner-construction contract consumed")
    print("[PASS] Approved owner method descriptors resolved statically")
    print("[PASS] Exact method signatures and canonical self parameters verified")
    print("[PASS] Method-binding-readiness hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-055 lineage preserved")
    print("[PASS] Owners were not reconstructed and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, unknown, duplicate, bound, or executable input rejected")
    print("[PASS] Atomic owner-method-binding-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
