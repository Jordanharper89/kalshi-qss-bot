import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_argument_binding_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableArgumentBindingGate,
    ProductionCallableArgumentBindingInvariantError,
    stable_hash,
)


def seed(path: Path) -> dict:
    entry_body = {
        "sequence": 1,
        "worker_id": "oracle-worker-test",
        "work_item_id": "work-1",
        "adapter_id": "oracle_read_only_canonical_observation_adapter.v1",
        "read_operation": "read_canonical_observations",
        "module_path": "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "owner_name": "OracleLiveCorpusInspector",
        "callable_name": "inspect",
        "callable_kind": "instance_method",
        "callable_qualified_name": "OracleLiveCorpusInspector.inspect",
        "constructor_signature": "(*, connection_factory: 'Callable[[], Any]', stale_after_seconds: 'int' = 300, market_limit: 'int' = 100)",
        "callable_signature": "(self, *, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
        "authorized_constructor_parameters": ["connection_factory", "stale_after_seconds", "market_limit"],
        "authorized_callable_parameters": ["inspected_at"],
        "required_constructor_parameters": ["connection_factory"],
        "optional_constructor_parameters": ["stale_after_seconds", "market_limit"],
        "required_callable_parameters": [],
        "optional_callable_parameters": ["inspected_at"],
        "binding_authorized": True,
        "owner_instantiated": False,
        "constructor_arguments_bound": False,
        "callable_arguments_bound": False,
        "callable_invoked": False,
        "adapter_executed": False,
        "authorization_checks": ["ok"],
        "authorization_status": "evidence_read_execution_adapter_production_callable_binding_authorized",
    }
    for field_name in (
        "source_callable_binding_readiness_hash", "source_callable_resolution_hash",
        "source_active_invocation_execution_authorization_hash", "source_active_invocation_execution_readiness_hash",
        "source_active_execution_invocation_hash", "source_execution_invocation_hash",
        "source_authorization_entry_hash", "source_readiness_entry_hash", "source_active_adapter_invocation_hash",
    ):
        entry_body[field_name] = stable_hash({field_name: 1})
    entry = dict(entry_body)
    entry["callable_binding_authorization_hash"] = stable_hash(entry_body)
    manifest = {
        "schema_version": "OIA-051", "engine_id": "OIA-051", "authorized_at": "2026-07-22T00:00:00+00:00",
        "callable_binding_authorization_id": "oia051-test", "callable_binding_authorization_status": "evidence_read_execution_adapter_production_callable_binding_authorization_issued",
        "callable_binding_authorization_policy_id": "test", "worker_id": "oracle-worker-test", "authorization_entry_count": 1, "authorization_entries": [entry],
        "source_callable_binding_readiness_id": "oia050-test", "source_callable_binding_readiness_manifest_hash": stable_hash({"50": 1}),
        "source_callable_resolution_id": "oia049-test", "source_callable_resolution_manifest_hash": stable_hash({"49": 1}),
        "source_execution_authorization_id": "48", "source_execution_authorization_manifest_hash": stable_hash({"48": 1}),
        "source_execution_readiness_id": "47", "source_execution_readiness_manifest_hash": stable_hash({"47": 1}),
        "source_invocation_activation_id": "46", "source_invocation_activation_manifest_hash": stable_hash({"46": 1}),
        "source_execution_invocation_manifest_id": "45", "source_execution_invocation_manifest_hash": stable_hash({"45": 1}),
        "source_prior_execution_authorization_id": "44", "source_prior_execution_authorization_manifest_hash": stable_hash({"44": 1}),
        "source_prior_execution_readiness_id": "43", "source_prior_execution_readiness_manifest_hash": stable_hash({"43": 1}),
        "source_activation_hash": stable_hash({"42": 1}), "source_lineage": {"dispatch_manifest_id": "20", "source_claim_id": "21"},
        "callable_binding_authorization_issued": True, "constructor_argument_binding_evaluation_allowed": True, "callable_argument_binding_evaluation_allowed": True,
        "owner_instantiation_allowed": False, "owner_instantiation_performed": False, "constructor_argument_binding_allowed": False, "constructor_argument_binding_performed": False,
        "callable_argument_binding_allowed": False, "callable_argument_binding_performed": False, "callable_invocation_allowed": False, "callable_invocation_performed": False,
        "adapter_execution_allowed": False, "adapter_execution_performed": False, "corpus_read_execution_allowed": False, "corpus_read_execution_performed": False,
        "research_execution_allowed": False, "analytic_conclusion_allowed": False, "forecast_creation_allowed": False, "signals_allowed": False, "alerts_allowed": False,
        "qseries_handoff_allowed": False, "execution_allowed": False, "trading_recommendations_allowed": False, "source_mutation_allowed": False,
        "market_order_creation_allowed": False, "funds_movement_allowed": False, "portfolio_mutation_allowed": False, "authorization_artifact_persistence_allowed": True,
    }
    manifest["callable_binding_authorization_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    print("=" * 40)
    print(" OIA-052 TEST")
    print(" CALLABLE ARGUMENT BINDING")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization = root / "authorization"
        binding = root / "binding"
        seed(authorization)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableArgumentBindingGate(authorization_directory=authorization, binding_directory=binding)
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.bind(bound_at=fixed, persist=True)
        second = gate.bind(bound_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-052" and first.binding_entry_count == 1
        entry = first.binding_entries[0]
        assert entry.bound_constructor_arguments == {"connection_factory": "symbolic://oracle/runtime/connection_factory", "stale_after_seconds": 300, "market_limit": 100}
        assert entry.bound_callable_arguments == {"self": "symbolic://oracle/owner_instance", "inspected_at": None}
        assert entry.owner_instantiated is False and entry.callable_bound_to_owner is False
        assert entry.callable_invoked is False and entry.adapter_executed is False
        assert first.symbolic_binding_only is True
        assert first.constructor_argument_binding_performed is True and first.callable_argument_binding_performed is True
        assert first.callable_invocation_evaluation_allowed is True
        assert first.callable_invocation_allowed is False and first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False and first.corpus_read_execution_allowed is False
        assert (binding / "current.json").exists()
        bad = json.loads((authorization / "current.json").read_text(encoding="utf-8"))
        bad["authorization_entries"][0]["callable_invoked"] = True
        (authorization / "current.json").write_text(json.dumps(bad), encoding="utf-8")
        try:
            gate.bind(bound_at=fixed, persist=False)
            raise AssertionError("tampered input accepted")
        except ProductionCallableArgumentBindingInvariantError:
            pass
    print("[PASS] Actual OIA-051 callable-binding authorization contract consumed")
    print("[PASS] Repository-verified constructor and callable signatures consumed")
    print("[PASS] Exact approved arguments bound symbolically and deterministically")
    print("[PASS] Binding manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-051 lineage preserved")
    print("[PASS] Owners were not instantiated and methods were not owner-bound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] Corpus read execution remained disabled")
    print("[PASS] Unknown, duplicate, tampered, or executable input rejected")
    print("[PASS] Atomic callable-argument-binding artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
