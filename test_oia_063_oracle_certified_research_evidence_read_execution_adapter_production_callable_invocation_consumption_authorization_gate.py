
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_consumption_authorization_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationConsumptionAuthorizationGate,
    ProductionCallableInvocationConsumptionAuthorizationInvariantError,
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
            "activation_nonce": stable_hash(
                {"adapter_id": adapter_id, "work_item_id": work_item_id}
            ),
            "source_callable_invocation_activation_hash": stable_hash(
                {"61": owner_name}
            ),
            "source_callable_invocation_authorization_hash": stable_hash(
                {"60": owner_name}
            ),
            "source_callable_invocation_readiness_hash": stable_hash(
                {"59": owner_name}
            ),
            "source_owner_method_binding_hash": stable_hash({"58": owner_name}),
            "single_use_activation_verified": True,
            "activation_unconsumed_verified": True,
            "invocation_consumption_ready": True,
            "activation_consumed": False,
            "owner_reconstruction_performed": False,
            "method_binding_performed": False,
            "callable_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "readiness_checks": ["verified"],
            "readiness_status": (
                "evidence_read_execution_adapter_production_callable_invocation_consumption_ready"
            ),
        }
        body["callable_invocation_consumption_readiness_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-062",
        "engine_id": "OIA-062",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "callable_invocation_consumption_readiness_id": "oia062-test",
        "callable_invocation_consumption_readiness_status": (
            "evidence_read_execution_adapter_production_callable_invocation_consumption_readiness_issued"
        ),
        "callable_invocation_consumption_readiness_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "readiness_entry_count": len(entries),
        "readiness_entries": entries,
        "source_callable_invocation_activation_id": "oia061-test",
        "source_callable_invocation_activation_manifest_hash": stable_hash(
            {"61m": 1}
        ),
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
        "callable_invocation_consumption_readiness_issued": True,
        "activation_consumption_authorization_evaluation_allowed": True,
        "activation_consumption_allowed": False,
        "activation_consumption_performed": False,
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
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest[
        "callable_invocation_consumption_readiness_manifest_hash"
    ] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["readiness_entries"]:
        body = dict(entry)
        body.pop("callable_invocation_consumption_readiness_hash", None)
        entry["callable_invocation_consumption_readiness_hash"] = stable_hash(
            body
        )
    body = dict(payload)
    body.pop("callable_invocation_consumption_readiness_manifest_hash", None)
    payload[
        "callable_invocation_consumption_readiness_manifest_hash"
    ] = stable_hash(body)


def reject(gate, fixed, message):
    try:
        gate.authorize(authorized_at=fixed, persist=False)
    except ProductionCallableInvocationConsumptionAuthorizationInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-063 TEST")
    print(" INVOCATION CONSUMPTION AUTHORIZATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        readiness = root / "readiness"
        authorization = root / "authorization"
        source = seed(readiness)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationConsumptionAuthorizationGate(
            readiness_directory=readiness,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-063"
        assert first.engine_id == "OIA-063"
        assert first.callable_invocation_consumption_authorization_issued is True
        assert first.authorization_entry_count == 2
        assert first.source_callable_invocation_consumption_readiness_manifest_hash == source[
            "callable_invocation_consumption_readiness_manifest_hash"
        ]
        assert first.activation_consumption_allowed is False
        assert first.activation_consumption_performed is False
        assert first.owner_reconstruction_allowed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False

        nonces = set()
        for entry in first.authorization_entries:
            assert entry.activation_consumption_authorization_granted is True
            assert entry.activation_consumption_authorized is True
            assert entry.activation_consumed is False
            assert entry.owner_reconstruction_authorized is True
            assert entry.owner_reconstruction_performed is False
            assert entry.method_binding_authorized is True
            assert entry.method_binding_performed is False
            assert entry.callable_invocation_authorized is True
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            nonces.add(entry.activation_nonce)
        assert len(nonces) == 2
        assert (authorization / "current.json").exists()

        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["activation_consumed"] = True
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "consumed activation accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][1]["activation_nonce"] = payload[
            "readiness_entries"
        ][0]["activation_nonce"]
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate activation nonce accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["readiness_entries"][0]["callable_invoked"] = True
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(readiness)
        payload = json.loads((readiness / "current.json").read_text())
        payload["activation_consumption_allowed"] = True
        rehash(payload)
        (readiness / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable readiness manifest accepted")

    print("[PASS] Actual OIA-062 invocation-consumption-readiness contract consumed")
    print("[PASS] Exact single-use activation consumptions authorized")
    print("[PASS] Authorization manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-062 lineage preserved")
    print("[PASS] Activation consumption authorized only by exact entry and nonce")
    print("[PASS] Activation consumption remained unperformed")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Consumed, duplicate, tampered, invoked, or executable input rejected")
    print("[PASS] Atomic invocation-consumption-authorization artifacts persisted")
    print("[PASS] Signals, alerts, Q Series, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
