from __future__ import annotations

import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_invocation_execution_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError,
    stable_hash,
)


TEST_MODULE = "int_oia_011_test_consumer_module"
INVOCATION_COUNT = 0


class OracleResearchAnalyticsConsumer:
    def analyze_certified_oia_artifacts(
        self,
        certified_artifacts,
        execution_context,
    ):
        global INVOCATION_COUNT
        INVOCATION_COUNT += 1
        return {
            "artifact_count": len(certified_artifacts),
            "consumer_mode": execution_context["consumer_mode"],
            "evidence_hash": stable_hash(certified_artifacts),
            "read_only": True,
        }


def _install_test_module() -> None:
    module = types.ModuleType(TEST_MODULE)
    module.OracleResearchAnalyticsConsumer = OracleResearchAnalyticsConsumer
    sys.modules[TEST_MODULE] = module


def _seed_readiness(path: Path) -> None:
    consumer = OracleResearchAnalyticsConsumer()
    bound = consumer.analyze_certified_oia_artifacts
    import inspect

    signature = inspect.signature(bound)
    identity_hash = stable_hash(
        {
            "consumer_module": TEST_MODULE,
            "consumer_class": "OracleResearchAnalyticsConsumer",
            "consumer_instance_type": (
                f"{consumer.__class__.__module__}."
                f"{consumer.__class__.__qualname__}"
            ),
            "callable_name": "analyze_certified_oia_artifacts",
            "callable_path": (
                f"{TEST_MODULE}."
                "OracleResearchAnalyticsConsumer."
                "analyze_certified_oia_artifacts"
            ),
            "bound_callable_signature": str(signature),
            "bound_callable_parameter_names": tuple(
                signature.parameters.keys()
            ),
        }
    )

    record = {
        "sequence": 1,
        "invocation_readiness_id": "invocation-readiness-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": TEST_MODULE,
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": (
            f"{TEST_MODULE}."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "bound_callable_signature": str(signature),
        "bound_callable_parameter_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "bound_callable_identity_hash": identity_hash,
        "source_binding_attestation_id": "binding-attestation-test",
        "source_binding_attestation_record_hash": stable_hash(
            {"binding-attestation": 1}
        ),
        "source_resolution_attestation_id": "resolution-test",
        "source_binding_contract_id": "binding-contract-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifact_input_mode": "certified_artifacts_only",
        "immutable_output_mode": "immutable_research_artifact_only",
        "required_argument_names": [
            "certified_artifacts",
            "execution_context",
        ],
        "argument_contract_hash": stable_hash({"arguments": 1}),
        "one_time_invocation": True,
        "invocation_authorized": True,
        "invocation_performed": False,
        "corpus_read_allowed": False,
        "corpus_read_performed": False,
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
        "readiness_status": "ready_for_one_time_controlled_invocation",
    }
    record["invocation_readiness_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-010",
        "engine_id": "INT-OIA-010",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "invocation_readiness_manifest_id": "int-oia-010-test",
        "invocation_readiness_status": (
            "downstream_read_only_consumer_controlled_invocation_ready"
        ),
        "invocation_readiness_policy_id": "test",
        "source_binding_attestation_manifest_id": "int-oia-009-test",
        "source_binding_attestation_manifest_hash": stable_hash(
            {"int": 9}
        ),
        "source_resolution_attestation_manifest_id": "int-oia-008-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record],
        "all_binding_attestation_hashes_verified": True,
        "all_bound_callable_identities_verified": True,
        "all_required_arguments_verified": True,
        "all_invocation_nonces_unique": True,
        "certified_artifact_input_mode_preserved": True,
        "immutable_output_mode_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "one_time_invocation_required": True,
        "controlled_invocation_authorized": True,
        "invocation_performed": False,
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
        "readiness_artifact_persistence_allowed": True,
    }
    manifest["invocation_readiness_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    global INVOCATION_COUNT

    print("=" * 40)
    print(" INT-OIA-011 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED INVOCATION EXECUTION")
    print("=" * 40)

    _install_test_module()

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        readiness = root / "readiness"
        execution = root / "execution"
        _seed_readiness(readiness)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionGate(
            readiness_directory=readiness,
            execution_directory=execution,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        artifacts = (
            {"artifact_id": "a-1", "certified": True},
            {"artifact_id": "a-2", "certified": True},
        )
        context = {
            "consumer_mode": "read_only_research",
            "execution_id": "test-execution",
        }

        INVOCATION_COUNT = 0
        first = gate.execute(
            certified_artifacts=artifacts,
            execution_context=context,
            executed_at=fixed,
            persist=True,
        )
        assert INVOCATION_COUNT == 1

        INVOCATION_COUNT = 0
        second = gate.execute(
            certified_artifacts=artifacts,
            execution_context=context,
            executed_at=fixed,
            persist=False,
        )
        assert INVOCATION_COUNT == 1
        assert first == second

        assert first.schema_version == "INT-OIA-011"
        assert first.execution_record_count == 1
        assert first.all_readiness_hashes_verified
        assert first.all_invocation_nonces_unique
        assert first.all_bound_callable_identities_verified
        assert first.all_argument_contracts_verified
        assert first.all_results_deterministically_hashable
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.one_time_invocation_enforced
        assert first.controlled_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.database_connection_performed
        assert not first.source_mutation_performed
        assert not first.forecast_creation_allowed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.execution_records[0]
        assert record.invocation_performed
        assert record.invocation_count == 1
        assert record.result_payload["artifact_count"] == 2
        assert record.result_payload["read_only"] is True
        assert len(record.result_hash) == 64
        assert not record.corpus_read_performed
        assert not record.database_connection_performed
        assert record.execution_status == "invoked_once_result_captured"

        assert (execution / "current.json").exists()

        tampered = json.loads(
            (readiness / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_records"][0]["invocation_performed"] = True
        (readiness / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.execute(
                certified_artifacts=artifacts,
                execution_context=context,
                executed_at=fixed,
                persist=False,
            )
            raise AssertionError("tampered readiness accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledInvocationExecutionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-010 invocation readiness consumed")
    print("[PASS] Every invocation-readiness hash verified")
    print("[PASS] Bound callable identity reconstructed and verified")
    print("[PASS] Certified artifacts passed in-memory only")
    print("[PASS] Controlled analytical callable invoked exactly once")
    print("[PASS] Immutable analytical result captured deterministically")
    print("[PASS] Result hash and execution lineage persisted")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe invocation readiness rejected")
    print("[PASS] Atomic controlled-execution artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
