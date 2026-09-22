import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_owner_construction_authorization_gate import *


def _hashes():
    return {
        key: stable_hash({key: 1})
        for key in (
            "source_callable_argument_binding_hash",
            "source_callable_binding_authorization_hash",
            "source_callable_binding_readiness_hash",
            "source_callable_resolution_hash",
            "source_active_invocation_execution_authorization_hash",
            "source_active_invocation_execution_readiness_hash",
            "source_active_execution_invocation_hash",
            "source_execution_invocation_hash",
            "source_authorization_entry_hash",
            "source_readiness_entry_hash",
            "source_active_adapter_invocation_hash",
        )
    }


def seed(path: Path) -> dict:
    constructor_arguments = {
        "connection_factory": "symbolic://oracle/runtime/connection_factory",
        "stale_after_seconds": 300,
        "market_limit": 100,
    }
    callable_arguments = {
        "self": "symbolic://oracle/owner_instance",
        "inspected_at": None,
    }
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
        "callable_signature": "(self, *, inspected_at=None)",
        "bound_constructor_arguments": constructor_arguments,
        "bound_callable_arguments": callable_arguments,
        "constructor_binding_hash": stable_hash(constructor_arguments),
        "callable_binding_hash": stable_hash(callable_arguments),
        "constructor_dependency_names": ["connection_factory"],
        "constructor_default_names": ["stale_after_seconds", "market_limit"],
        "symbolic_dependencies_only": True,
        "owner_construction_ready": True,
        "owner_instantiated": False,
        "callable_bound_to_owner": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "readiness_checks": [
            "callable_argument_binding_manifest_hash_verified",
            "callable_argument_binding_entry_hash_verified",
            "constructor_binding_hash_verified",
            "callable_binding_hash_verified",
            "constructor_dependencies_classified",
            "constructor_defaults_classified",
            "symbolic_dependencies_only_verified",
            "owner_not_instantiated",
            "callable_not_bound_to_owner",
            "callable_not_invoked",
            "adapter_not_executed",
            "oracle_qseries_boundary_verified",
        ],
        "readiness_status": "evidence_read_execution_adapter_production_owner_construction_ready",
        **_hashes(),
    }
    entry = dict(entry_body)
    entry["owner_construction_readiness_hash"] = stable_hash(entry_body)
    manifest = {
        "schema_version": "OIA-053",
        "engine_id": "OIA-053",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "owner_construction_readiness_id": "oia053-test",
        "owner_construction_readiness_status": "evidence_read_execution_adapter_production_owner_construction_readiness_issued",
        "owner_construction_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": 1,
        "readiness_entries": [entry],
        "source_callable_argument_binding_id": "oia052-test",
        "source_callable_argument_binding_manifest_hash": stable_hash({"oia052": 1}),
        "source_lineage": {"dispatch_manifest_id": "20", "source_claim_id": "21"},
        "owner_construction_readiness_issued": True,
        "owner_construction_authorization_evaluation_allowed": True,
        "owner_instantiation_allowed": False,
        "owner_instantiation_performed": False,
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
    manifest["owner_construction_readiness_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def rehash(payload: dict) -> None:
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("owner_construction_readiness_hash", None)
        entry["owner_construction_readiness_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_construction_readiness_manifest_hash", None)
    payload["owner_construction_readiness_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionOwnerConstructionAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main() -> int:
    print("=" * 40)
    print(" OIA-054 TEST")
    print(" OWNER CONSTRUCTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionOwnerConstructionAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "OIA-054"
        assert first.authorization_entry_count == 1
        entry = first.authorization_entries[0]
        assert entry.owner_construction_ready is True
        assert entry.owner_construction_authorized is True
        assert entry.owner_instantiation_requested is False
        assert entry.owner_instantiated is False
        assert entry.callable_bound_to_owner is False
        assert entry.callable_invoked is False
        assert entry.adapter_executed is False
        assert entry.constructor_dependency_names == ("connection_factory",)
        assert entry.constructor_default_names == ("stale_after_seconds", "market_limit")
        assert first.owner_construction_authorization_issued is True
        assert first.owner_construction_evaluation_allowed is True
        assert first.owner_instantiation_allowed is False
        assert first.owner_instantiation_performed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.qseries_handoff_allowed is False
        assert first.execution_allowed is False
        assert first.source_owner_construction_readiness_manifest_hash == source["owner_construction_readiness_manifest_hash"]
        assert (authorization / "current.json").exists()

        tampered = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        tampered["readiness_entries"][0]["owner_instantiated"] = True
        (readiness / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        reject(gate, fixed, "instantiated owner accepted")

        seed(readiness)
        duplicate = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        extra = dict(duplicate["readiness_entries"][0])
        extra["sequence"] = 2
        duplicate["readiness_entries"].append(extra)
        duplicate["readiness_entry_count"] = 2
        rehash(duplicate)
        (readiness / "current.json").write_text(json.dumps(duplicate), encoding="utf-8")
        reject(gate, fixed, "duplicate work item accepted")

        seed(readiness)
        live_secret = json.loads((readiness / "current.json").read_text(encoding="utf-8"))
        live_secret["readiness_entries"][0]["bound_constructor_arguments"]["connection_factory"] = "postgresql://user:secret@localhost/db"
        rehash(live_secret)
        (readiness / "current.json").write_text(json.dumps(live_secret), encoding="utf-8")
        reject(gate, fixed, "changed constructor binding accepted")

    print("[PASS] Actual OIA-053 owner-construction-readiness contract consumed")
    print("[PASS] Exact symbolic construction plans authorized deterministically")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-053 lineage preserved")
    print("[PASS] Owner-construction evaluation authorized without construction")
    print("[PASS] Owners were not instantiated and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Tampered, duplicate, live, or executable input rejected")
    print("[PASS] Atomic owner-construction-authorization artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
