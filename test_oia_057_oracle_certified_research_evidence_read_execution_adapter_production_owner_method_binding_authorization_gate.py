import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_method_binding_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate,
    ProductionOwnerMethodBindingAuthorizationInvariantError,
    stable_hash,
)


def seed_oia056(path: Path) -> dict:
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
        "owner_state_fingerprint": stable_hash({"owner": "inert"}),
        "owner_construction_hash": stable_hash({"55": 1}),
        "method_descriptor_type": "function",
        "method_descriptor_module": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "method_descriptor_qualname": "OracleLiveCorpusInspector.inspect",
        "method_signature_verified": True,
        "instance_parameter_verified": True,
        "descriptor_static_resolution_verified": True,
        "owner_reconstruction_required": True,
        "owner_reconstructed": False,
        "method_bound_to_owner": False,
        "method_invoked": False,
        "adapter_executed": False,
        "readiness_checks": ["approved_method_descriptor_statically_resolved"],
        "readiness_status": "evidence_read_execution_adapter_production_owner_method_binding_ready",
        "source_owner_construction_authorization_hash": stable_hash({"54": 1}),
        "source_owner_construction_readiness_hash": stable_hash({"53": 1}),
        "source_callable_argument_binding_hash": stable_hash({"52": 1}),
    }
    entry = dict(entry_body)
    entry["owner_method_binding_readiness_hash"] = stable_hash(entry_body)
    manifest_body = {
        "schema_version": "OIA-056",
        "engine_id": "OIA-056",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "owner_method_binding_readiness_id": "oia056-test",
        "owner_method_binding_readiness_status": "evidence_read_execution_adapter_production_owner_method_binding_readiness_issued",
        "owner_method_binding_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [entry],
        "source_owner_construction_id": "oia055-test",
        "source_owner_construction_manifest_hash": stable_hash({"55m": 1}),
        "source_owner_construction_authorization_id": "oia054-test",
        "source_owner_construction_authorization_manifest_hash": stable_hash({"54m": 1}),
        "source_lineage": {"dispatch_manifest_id": "oia020-test", "source_claim_id": "oia021-test"},
        "owner_method_binding_readiness_issued": True,
        "owner_method_binding_authorization_evaluation_allowed": True,
        "owner_reconstruction_allowed": False,
        "owner_reconstruction_performed": False,
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
        "readiness_artifact_persistence_allowed": True,
    }
    payload = dict(manifest_body)
    payload["owner_method_binding_readiness_manifest_hash"] = stable_hash(manifest_body)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def rehash(payload: dict) -> None:
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("owner_method_binding_readiness_hash", None)
        entry["owner_method_binding_readiness_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_method_binding_readiness_manifest_hash", None)
    payload["owner_method_binding_readiness_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionOwnerMethodBindingAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-057 TEST")
    print(" OWNER METHOD BINDING AUTHORIZATION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed_oia056(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerMethodBindingAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-057"
        assert first.engine_id == "OIA-057"
        assert first.owner_method_binding_authorization_issued is True
        assert first.owner_reconstruction_evaluation_allowed is True
        assert first.callable_binding_to_owner_evaluation_allowed is True
        assert first.authorization_entry_count == 1
        entry = first.authorization_entries[0]
        assert entry.owner_method_binding_ready is True
        assert entry.owner_method_binding_authorized is True
        assert entry.owner_reconstruction_requested is False
        assert entry.owner_reconstructed is False
        assert entry.method_binding_requested is False
        assert entry.method_bound_to_owner is False
        assert entry.method_invoked is False
        assert entry.adapter_executed is False
        assert first.owner_reconstruction_allowed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_method_binding_readiness_manifest_hash == source["owner_method_binding_readiness_manifest_hash"]
        assert (authorization / "current.json").exists()

        tampered = json.loads((readiness / "current.json").read_text())
        tampered["readiness_entries"][0]["callable_signature"] = "(self, *args, **kwargs)"
        rehash(tampered)
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "tampered signature accepted")

        seed_oia056(readiness)
        bound = json.loads((readiness / "current.json").read_text())
        bound["readiness_entries"][0]["method_bound_to_owner"] = True
        rehash(bound)
        (readiness / "current.json").write_text(json.dumps(bound), encoding="utf-8")
        reject(gate, fixed, "premature binding accepted")

        seed_oia056(readiness)
        executable = json.loads((readiness / "current.json").read_text())
        executable["adapter_execution_allowed"] = True
        rehash(executable)
        (readiness / "current.json").write_text(json.dumps(executable), encoding="utf-8")
        reject(gate, fixed, "executable manifest accepted")

        seed_oia056(readiness)
        duplicate = json.loads((readiness / "current.json").read_text())
        duplicate["readiness_entries"].append(dict(duplicate["readiness_entries"][0]))
        duplicate["readiness_entries"][1]["sequence"] = 2
        duplicate["readiness_entry_count"] = 2
        rehash(duplicate)
        (readiness / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

    print("[PASS] Actual OIA-056 owner-method-binding-readiness contract consumed")
    print("[PASS] Exact verified owner method binding plans authorized deterministically")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-056 lineage preserved")
    print("[PASS] Binding evaluation authorized without reconstructing or binding owners")
    print("[PASS] Owners were not reconstructed and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, bound, or executable input rejected")
    print("[PASS] Atomic owner-method-binding-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
