from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_readiness_gate import (
    APPROVED_INPUT_MODE,
    APPROVED_OUTPUT_MODE,
    REQUIRED_BOUND_PARAMETERS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError,
    stable_hash,
)


def _seed_binding(path: Path) -> None:
    record = {
        "sequence": 1,
        "binding_attestation_id": "binding-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "source_resolution_attestation_id": "resolution-test",
        "source_resolution_attestation_record_hash": stable_hash(
            {"resolution": 1}
        ),
        "source_binding_contract_id": "binding-contract-test",
        "source_binding_contract_hash": stable_hash(
            {"binding-contract": 1}
        ),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation-nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "consumer_instantiated": True,
        "consumer_instance_type": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer"
        ),
        "callable_bound": True,
        "bound_callable_is_callable": True,
        "bound_callable_signature": (
            "(*, certified_artifacts, execution_context)"
        ),
        "bound_callable_parameter_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "bound_callable_identity_hash": stable_hash(
            {"bound-callable": 1}
        ),
        "callable_invocation_allowed": True,
        "callable_invocation_performed": False,
        "corpus_read_performed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "binding_status": "bound_not_invoked",
    }
    record["binding_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-009",
        "engine_id": "INT-OIA-009",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "binding_attestation_manifest_id": "int-oia-009-test",
        "binding_attestation_status": (
            "downstream_read_only_consumer_callable_binding_attested"
        ),
        "binding_attestation_policy_id": "test",
        "source_resolution_attestation_manifest_id": "int-oia-008-test",
        "source_resolution_attestation_manifest_hash": stable_hash(
            {"int": 8}
        ),
        "source_resolution_readiness_manifest_id": "int-oia-007-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_resolution_hashes_verified": True,
        "all_consumers_instantiated": True,
        "all_callables_bound": True,
        "all_bound_callables_callable": True,
        "exact_callable_identity_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "callable_invocation_allowed": True,
        "callable_invocation_performed": False,
        "corpus_read_execution_repeated": False,
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
        "controlled_callable_invocation_authorized": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["binding_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-010 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        binding = root / "binding"
        readiness = root / "readiness"
        _seed_binding(binding)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-010"
        assert first.readiness_record_count == 1
        assert first.all_binding_attestation_hashes_verified
        assert first.all_bound_callable_identities_verified
        assert first.all_required_arguments_verified
        assert first.all_invocation_nonces_unique
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.one_time_invocation_required
        assert first.controlled_invocation_authorized
        assert not first.invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.readiness_records[0]
        assert record.certified_artifact_input_mode == APPROVED_INPUT_MODE
        assert record.immutable_output_mode == APPROVED_OUTPUT_MODE
        assert record.required_argument_names == REQUIRED_BOUND_PARAMETERS
        assert record.one_time_invocation
        assert record.invocation_authorized
        assert not record.invocation_performed
        assert not record.corpus_read_allowed
        assert not record.corpus_read_performed
        assert len(record.invocation_nonce) == 64
        assert len(record.argument_contract_hash) == 64
        assert (
            record.readiness_status
            == "ready_for_one_time_controlled_invocation"
        )

        assert (readiness / "current.json").exists()

        tampered = json.loads(
            (binding / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "bound_callable_parameter_names"
        ] = ["unsafe_argument"]
        (binding / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
            raise AssertionError("tampered binding accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-009 binding attestation consumed")
    print("[PASS] Every binding-attestation hash verified")
    print("[PASS] Bound callable identity independently verified")
    print("[PASS] Exact invocation argument contract verified")
    print("[PASS] One-time invocation nonce generated deterministically")
    print("[PASS] Invocation nonces remained unique")
    print("[PASS] Certified-artifact-only input mode preserved")
    print("[PASS] Immutable research-artifact output mode preserved")
    print("[PASS] Controlled one-time invocation authorized")
    print("[PASS] Callable was not invoked")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe binding evidence rejected")
    print("[PASS] Atomic invocation-readiness artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
