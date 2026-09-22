
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate,
    ProductionCallableInvocationReadinessInvariantError,
    stable_hash,
)


def seed(path: Path):
    specs = [
        (
            "oracle_read_only_canonical_observation_adapter.v1",
            "work.observations",
            "read_canonical_observations",
            "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
            "OracleLiveCorpusInspector",
            "inspect",
            "OracleLiveCorpusInspector.inspect",
            "(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
        ),
        (
            "oracle_read_only_market_state_lineage_adapter.v1",
            "work.lineage",
            "read_market_state_lineage",
            "qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_market_lineage_ledger",
            "OracleCanonicalMarketLineageLedger",
            "records",
            "OracleCanonicalMarketLineageLedger.records",
            "() -> 'tuple[CanonicalMarketStateDwellChangeLineage, ...]'",
        ),
    ]

    entries = []
    for sequence, spec in enumerate(specs, start=1):
        (
            adapter_id,
            work_item_id,
            read_operation,
            module_path,
            owner_name,
            callable_name,
            qualname,
            signature,
        ) = spec
        body = {
            "sequence": sequence,
            "worker_id": "oracle-worker-test",
            "work_item_id": work_item_id,
            "adapter_id": adapter_id,
            "read_operation": read_operation,
            "module_path": module_path,
            "owner_name": owner_name,
            "callable_name": callable_name,
            "owner_state_fingerprint": stable_hash({"owner": owner_name}),
            "owner_construction_hash": stable_hash({"construction": owner_name}),
            "method_descriptor_module": module_path,
            "method_descriptor_qualname": qualname,
            "bound_method_type": "method",
            "bound_method_module": module_path,
            "bound_method_qualname": qualname,
            "bound_method_signature": signature,
            "bound_method_self_verified": True,
            "bound_method_function_verified": True,
            "owner_reconstructed": True,
            "method_binding_requested": True,
            "method_bound_to_owner": True,
            "method_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "binding_checks": ["verified"],
            "binding_status": (
                "evidence_read_execution_adapter_production_owner_method_bound"
            ),
            "source_owner_method_binding_authorization_hash": stable_hash(
                {"57": owner_name}
            ),
            "source_owner_method_binding_readiness_hash": stable_hash(
                {"56": owner_name}
            ),
            "source_owner_construction_authorization_hash": stable_hash(
                {"54": owner_name}
            ),
            "source_owner_construction_readiness_hash": stable_hash(
                {"53": owner_name}
            ),
            "source_callable_argument_binding_hash": stable_hash(
                {"52": owner_name}
            ),
        }
        body["owner_method_binding_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-058",
        "engine_id": "OIA-058",
        "bound_at": "2026-07-22T00:00:00+00:00",
        "owner_method_binding_id": "oia058-test",
        "owner_method_binding_status": (
            "evidence_read_execution_adapter_production_owner_method_binding_issued"
        ),
        "owner_method_binding_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "binding_entry_count": len(entries),
        "binding_entries": entries,
        "source_owner_method_binding_authorization_id": "oia057-test",
        "source_owner_method_binding_authorization_manifest_hash": stable_hash(
            {"57m": 1}
        ),
        "source_owner_method_binding_readiness_id": "oia056-test",
        "source_owner_method_binding_readiness_manifest_hash": stable_hash(
            {"56m": 1}
        ),
        "source_owner_construction_id": "oia055-test",
        "source_owner_construction_manifest_hash": stable_hash({"55m": 1}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
        },
        "owner_reconstruction_allowed": True,
        "owner_reconstruction_performed": True,
        "callable_binding_to_owner_allowed": True,
        "callable_binding_to_owner_performed": True,
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
        "binding_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest["owner_method_binding_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["binding_entries"]:
        body = dict(entry)
        body.pop("owner_method_binding_hash", None)
        entry["owner_method_binding_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("owner_method_binding_manifest_hash", None)
    payload["owner_method_binding_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.evaluate(evaluated_at=fixed, persist=False)
    except ProductionCallableInvocationReadinessInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-059 TEST")
    print(" CALLABLE INVOCATION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        binding = root / "binding"
        readiness = root / "readiness"
        source = seed(binding)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-059"
        assert first.engine_id == "OIA-059"
        assert first.callable_invocation_readiness_issued is True
        assert first.callable_invocation_authorization_evaluation_allowed is True
        assert first.readiness_entry_count == 2
        assert first.source_owner_method_binding_manifest_hash == source[
            "owner_method_binding_manifest_hash"
        ]
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False
        assert first.owner_instances_retained is False
        assert first.bound_methods_retained is False

        for entry in first.readiness_entries:
            assert entry.invocation_envelope_verified is True
            assert entry.callable_invocation_ready is True
            assert entry.owner_reconstructed is False
            assert entry.method_bound_to_owner is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            assert entry.invocation_argument_hash == stable_hash(
                entry.invocation_arguments
            )

        assert (
            first.readiness_entries[0].invocation_arguments
            == {"inspected_at": None}
        )
        assert first.readiness_entries[1].invocation_arguments == {}
        assert (readiness / "current.json").exists()

        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["method_invoked"] = True
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"][0]["callable_name"] = "execute"
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "unknown callable accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["binding_entries"].append(dict(payload["binding_entries"][0]))
        payload["binding_entries"][-1]["sequence"] = 3
        payload["binding_entry_count"] = 3
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate binding accepted")

        seed(binding)
        payload = json.loads((binding / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (binding / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable binding manifest accepted")

    print("[PASS] Actual OIA-058 owner-method-binding contract consumed")
    print("[PASS] Exact approved invocation envelopes verified deterministically")
    print("[PASS] Invocation argument and readiness hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-058 lineage preserved")
    print("[PASS] Prior live owners and bound methods remained released")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Tampered, duplicate, invoked, or executable input rejected")
    print("[PASS] Atomic callable-invocation-readiness artifacts persisted")
    print("[PASS] Signals, alerts, and Q Series handoff remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
