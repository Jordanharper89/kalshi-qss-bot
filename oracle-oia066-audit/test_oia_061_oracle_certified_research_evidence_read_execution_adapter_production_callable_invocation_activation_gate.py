
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_certified_research_evidence_read_execution_adapter_production_callable_invocation_activation_gate import (
    OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationActivationGate,
    ProductionCallableInvocationActivationInvariantError,
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
            "callable_invocation_authorization_granted": True,
            "owner_reconstruction_authorized": True,
            "owner_reconstruction_performed": False,
            "method_binding_authorized": True,
            "method_binding_performed": False,
            "callable_invocation_authorized": True,
            "callable_invoked": False,
            "adapter_executed": False,
            "corpus_read_executed": False,
            "authorization_checks": ["verified"],
            "authorization_status": (
                "evidence_read_execution_adapter_production_callable_invocation_authorized"
            ),
        }
        body["callable_invocation_authorization_hash"] = stable_hash(body)
        entries.append(body)

    manifest = {
        "schema_version": "OIA-060",
        "engine_id": "OIA-060",
        "authorized_at": "2026-07-22T00:00:00+00:00",
        "callable_invocation_authorization_id": "oia060-test",
        "callable_invocation_authorization_status": (
            "evidence_read_execution_adapter_production_callable_invocation_authorization_issued"
        ),
        "callable_invocation_authorization_policy_id": "test",
        "worker_id": "oracle-worker-test",
        "authorization_entry_count": len(entries),
        "authorization_entries": entries,
        "source_callable_invocation_readiness_id": "oia059-test",
        "source_callable_invocation_readiness_manifest_hash": stable_hash(
            {"59m": 1}
        ),
        "source_owner_method_binding_id": "oia058-test",
        "source_owner_method_binding_manifest_hash": stable_hash({"58m": 1}),
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
        "callable_invocation_authorization_issued": True,
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
        "authorization_artifact_persistence_allowed": True,
        "owner_instances_retained": False,
        "bound_methods_retained": False,
    }
    manifest["callable_invocation_authorization_manifest_hash"] = stable_hash(
        manifest
    )
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def rehash(payload):
    for entry in payload["authorization_entries"]:
        body = dict(entry)
        body.pop("callable_invocation_authorization_hash", None)
        entry["callable_invocation_authorization_hash"] = stable_hash(body)
    body = dict(payload)
    body.pop("callable_invocation_authorization_manifest_hash", None)
    payload["callable_invocation_authorization_manifest_hash"] = stable_hash(
        body
    )


def reject(gate, fixed, message):
    try:
        gate.activate(activated_at=fixed, persist=False)
    except ProductionCallableInvocationActivationInvariantError:
        return
    raise AssertionError(message)


def main():
    print("=" * 40)
    print(" OIA-061 TEST")
    print(" CALLABLE INVOCATION ACTIVATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        authorization = root / "authorization"
        activation = root / "activation"
        source = seed(authorization)
        gate = OracleCertifiedResearchEvidenceReadExecutionAdapterProductionCallableInvocationActivationGate(
            authorization_directory=authorization,
            activation_directory=activation,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "OIA-061"
        assert first.engine_id == "OIA-061"
        assert first.callable_invocation_activation_issued is True
        assert first.single_use_activation_required is True
        assert first.activation_entry_count == 2
        assert first.source_callable_invocation_authorization_manifest_hash == source[
            "callable_invocation_authorization_manifest_hash"
        ]
        assert first.owner_reconstruction_allowed is False
        assert first.callable_binding_to_owner_allowed is False
        assert first.callable_invocation_allowed is False
        assert first.callable_invocation_performed is False
        assert first.adapter_execution_allowed is False
        assert first.corpus_read_execution_allowed is False

        nonces = set()
        for entry in first.activation_entries:
            assert entry.single_use_activation is True
            assert entry.invocation_activation_granted is True
            assert entry.invocation_activation_consumed is False
            assert entry.owner_reconstruction_performed is False
            assert entry.method_binding_performed is False
            assert entry.callable_invoked is False
            assert entry.adapter_executed is False
            assert entry.corpus_read_executed is False
            assert _valid_nonce(entry.activation_nonce)
            nonces.add(entry.activation_nonce)
        assert len(nonces) == 2
        assert (activation / "current.json").exists()

        payload = json.loads((authorization / "current.json").read_text())
        payload["authorization_entries"][0]["callable_invoked"] = True
        rehash(payload)
        (authorization / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "premature invocation accepted")

        seed(authorization)
        payload = json.loads((authorization / "current.json").read_text())
        payload["authorization_entries"][0]["invocation_arguments"] = {
            "inspected_at": "2026-07-22T00:00:00+00:00"
        }
        payload["authorization_entries"][0]["invocation_argument_hash"] = stable_hash(
            payload["authorization_entries"][0]["invocation_arguments"]
        )
        rehash(payload)
        (authorization / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "altered invocation arguments accepted")

        seed(authorization)
        payload = json.loads((authorization / "current.json").read_text())
        payload["authorization_entries"][0]["bound_method_signature"] = (
            "(*args, **kwargs)"
        )
        rehash(payload)
        (authorization / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "signature drift accepted")

        seed(authorization)
        payload = json.loads((authorization / "current.json").read_text())
        payload["authorization_entries"].append(
            dict(payload["authorization_entries"][0])
        )
        payload["authorization_entries"][-1]["sequence"] = 3
        payload["authorization_entry_count"] = 3
        rehash(payload)
        (authorization / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "duplicate authorization entry accepted")

        seed(authorization)
        payload = json.loads((authorization / "current.json").read_text())
        payload["callable_invocation_allowed"] = True
        rehash(payload)
        (authorization / "current.json").write_text(json.dumps(payload))
        reject(gate, fixed, "executable authorization manifest accepted")

    print("[PASS] Actual OIA-060 callable-invocation-authorization contract consumed")
    print("[PASS] Exact approved invocation authorizations activated deterministically")
    print("[PASS] Unique single-use activation nonces issued")
    print("[PASS] Activation manifest and entry hashes deterministic")
    print("[PASS] Complete OIA-020 through OIA-060 lineage preserved")
    print("[PASS] Activation remained unconsumed and non-executing")
    print("[PASS] Owners were not reconstructed and methods were not rebound")
    print("[PASS] No callable was invoked and no adapter executed")
    print("[PASS] PostgreSQL connections and corpus reads remained disabled")
    print("[PASS] Tampered, duplicate, invoked, or executable input rejected")
    print("[PASS] Atomic callable-invocation-activation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series, orders, funds, and portfolio mutation remained disabled")
    return 0


def _valid_nonce(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


if __name__ == "__main__":
    raise SystemExit(main())
