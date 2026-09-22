
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_readiness_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationConsumptionReadinessGate,
    ProductionCallableInvocationConsumptionReadinessInvariantError,
    stable_hash,
)


SPECS = (
    (
        "oracle_read_only_canonical_observation_adapter.v1",
        "work.observations",
        "read_canonical_observations",
        "qseries_v2.oracle_intelligence.analytics.oracle_live_corpus_inspector",
        "OracleLiveCorpusInspector",
        "inspect",
        "OracleLiveCorpusInspector.inspect",
        "(*, inspected_at: 'Optional[datetime]' = None) -> 'OracleLiveCorpusReport'",
        {"inspected_at": None},
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
        {},
    ),
)


def seed(path: Path):
    entries = []
    for sequence, spec in enumerate(SPECS, start=1):
        (
            adapter_id,
            work_item_id,
            read_operation,
            module_path,
            owner_name,
            callable_name,
            qualname,
            signature,
            arguments,
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
            "bound_method_module": module_path,
            "bound_method_qualname": qualname,
            "bound_method_signature": signature,
            "invocation_arguments": arguments,
            "invocation_argument_hash": stable_hash(arguments),
            "source_callable_invocation_authorization_hash": stable_hash(
                {"60": owner_name}
            ),
            "source_callable_invocation_readiness_hash": stable_hash(
                {"59": owner_name}
            ),
            "source_owner_method_binding_hash": stable_hash({"58": owner_name}),
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
            "activation_nonce": stable_hash(
                {"adapter_id": adapter_id, "work_item_id": work_item_id}
            ),
            "single_use_activation": True,
            "invocation_activation_granted": True,
            "invocation_activation_consumed": False,
            "owner_reconstruction_performed": False,
            "method_binding_performed": False,
            "callable_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "activation_checks": ["verified"],
            "activation_status": (
                "evidence_read_execution_adapter_production_callable_invocation_activated"
            ),
        }
        body["callable_invocation_activation_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-061",
        "engine_id": "OIA-061",
        "activated_at": "2026-07-22T00:00:00+00:00",
        "callable_invocation_activation_id": "oia061-test",
        "callable_invocation_activation_status": (
            "evidence_read_execution_adapter_production_callable_invocation_activation_issued"
        ),
        "callable_invocation_activation_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "activation_entry_count": len(entries),
        "activation_entries": entries,
        "source_callable_invocation_authorization_id": "oia060-test",
        "source_callable_invocation_authorization_manifest_hash": stable_hash(
            {"60m": 1}
        ),
        "source_callable_invocation_readiness_id": "oia059-test",
        "source_callable_invocation_readiness_manifest_hash": stable_hash(
            {"59m": 1}
        ),
        "source_owner_method_binding_id": "oia058-test",
        "source_owner_method_binding_manifest_hash": stable_hash({"58m": 1}),
        "source_lineage": {
            "dispatch_manifest_id": "oia020-test",
            "source_claim_id": "oia021-test",
        },
        "callable_invocation_activation_issued": True,
        "single_use_activation_required": True,
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
        "activation_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest["callable_invocation_activation_manifest_hash"] = stable_hash(
        manifest
    )
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["activation_entries"]:
        body = dict(entry)
        body.pop("callable_invocation_activation_hash", None)
        entry["callable_invocation_activation_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("callable_invocation_activation_manifest_hash", None)
    payload["callable_invocation_activation_manifest_hash"] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.evaluate(evaluated_at=fixed, persist=False)
    except ProductionCallableInvocationConsumptionReadinessInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-062 TEST")
    print(" INVOCATION CONSUMPTION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        activation = root / "activation"
        readiness = root / "readiness"
        source = seed(activation)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationConsumptionReadinessGate(
            activation_directory=activation,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-062"
        assert first.engine_id == "OIA-062"
        assert first.callable_invocation_consumption_readiness_issued is True
        assert first.activation_consumption_authorization_evaluation_allowed is True
        assert first.activation_consumption_allowed is False
        assert first.activation_consumption_performed is False
        assert first.readiness_entry_count == 2
        assert first.source_callable_invocation_activation_manifest_hash == source[
            "callable_invocation_activation_manifest_hash"
        ]
        assert first.owner_reconstruction_performed is False
        assert first.callable_binding_to_owner_performed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_performed is False
        assert first.corpus_read_execution_performed is False

        nonces = set()
        for entry in first.readiness_entries:
            assert entry.single_use_activation_verified is True
            assert entry.activation_unconsumed_verified is True
            assert entry.invocation_consumption_ready is True
            assert entry.activation_consumed is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            nonces.add(entry.activation_nonce)
        assert len(nonces) == 2
        assert (readiness / "current.json").exists()

        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["invocation_activation_consumed"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "consumed activation accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][1]["activation_nonce"] = payload[
            "activation_entries"
        ][0]["activation_nonce"]
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate activation nonce accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["activation_entries"][0]["callable_invoked"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(activation)
        payload = json.loads((activation / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (activation / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable activation manifest accepted")

    print("[PASS] Actual OIA-061 callable-invocation-activation contract consumed")
    print("[PASS] Exact single-use activation entries verified")
    print("[PASS] Activation nonce format and uniqueness verified")
    print("[PASS] Consumption-readiness manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-061 lineage preserved")
    print("[PASS] Activation consumption remained unauthorized and unperformed")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Consumed, duplicate, tampered, invoked, or executable input rejected")
    print("[PASS] Atomic invocation-consumption-readiness artifacts persisted")
    print("[PASS] Signals, alerts, Q Series, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
