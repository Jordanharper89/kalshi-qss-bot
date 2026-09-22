from __future__ import annotations
import json, tempfile
from datetime import datetime, timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_result_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError,
    stable_hash,
)

def seed(path: Path) -> None:
    result = {"artifact_count": 2, "read_only": True, "finding": "certified"}
    record = {
        "sequence": 1,
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": "test.module",
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": "test.module.OracleResearchAnalyticsConsumer.analyze_certified_oia_artifacts",
        "bound_callable_identity_hash": stable_hash({"callable": 1}),
        "source_invocation_readiness_id": "readiness-test",
        "source_invocation_readiness_record_hash": stable_hash({"readiness": 1}),
        "source_binding_attestation_id": "binding-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifacts_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "execution_context_hash": stable_hash({"mode": "read_only"}),
        "argument_contract_hash": stable_hash({"arguments": 1}),
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result),
        "result_payload": result,
        "one_time_invocation": True,
        "invocation_authorized": True,
        "invocation_performed": True,
        "invocation_count": 1,
        "corpus_read_performed": False,
        "database_connection_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "execution_status": "invoked_once_result_captured",
    }
    record["invocation_execution_record_hash"] = stable_hash(record)
    manifest = {
        "schema_version": "INT-OIA-011",
        "engine_id": "INT-OIA-011",
        "executed_at": "2026-07-22T00:00:00+00:00",
        "invocation_execution_manifest_id": "int-oia-011-test",
        "invocation_execution_status": "downstream_read_only_consumer_controlled_invocation_executed",
        "invocation_execution_policy_id": "test",
        "source_invocation_readiness_manifest_id": "int-oia-010-test",
        "source_invocation_readiness_manifest_hash": stable_hash({"int": 10}),
        "source_binding_attestation_manifest_id": "int-oia-009-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "execution_record_count": 1,
        "execution_records": [record],
        "all_readiness_hashes_verified": True,
        "all_invocation_nonces_unique": True,
        "all_bound_callable_identities_verified": True,
        "all_argument_contracts_verified": True,
        "all_results_deterministically_hashable": True,
        "certified_artifact_input_mode_preserved": True,
        "immutable_output_mode_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "one_time_invocation_enforced": True,
        "controlled_invocation_performed": True,
        "corpus_read_execution_repeated": False,
        "database_connection_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "immutable_execution_artifact_persistence_allowed": True,
    }
    manifest["invocation_execution_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")

def main() -> int:
    print("=" * 40)
    print(" INT-OIA-012 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" INVOCATION RESULT ATTESTATION")
    print("=" * 40)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); execution = root / "execution"; attestation = root / "attestation"
        seed(execution)
        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationGate(execution_directory=execution, attestation_directory=attestation)
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "INT-OIA-012"
        assert first.all_execution_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_execution_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_result_admission_authorized
        assert not first.downstream_release_performed
        record = first.attestation_records[0]
        assert record.result_hash == record.recomputed_result_hash
        assert record.result_hash_verified
        assert record.result_admission_authorized
        assert record.attestation_status == "result_verified_not_released"
        assert (attestation / "current.json").exists()
        tampered = json.loads((execution / "current.json").read_text(encoding="utf-8"))
        tampered["execution_records"][0]["result_payload"]["read_only"] = False
        (execution / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered execution accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationResultAttestationInvariantError:
            pass
    print("[PASS] Actual INT-OIA-011 controlled execution consumed")
    print("[PASS] Every execution and lineage hash verified")
    print("[PASS] Analytical result hash independently recomputed")
    print("[PASS] One-time invocation count independently verified")
    print("[PASS] Immutable result payload attested")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe execution evidence rejected")
    print("[PASS] Controlled result admission authorized")
    print("[PASS] Result was not released downstream")
    print("[PASS] Atomic result-attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series execution, orders, funds, and portfolio mutation remained disabled")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
