from __future__ import annotations

import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError,
    stable_hash,
)


TEST_MODULE = "int_oia_009_test_consumer_module"


class OracleResearchAnalyticsConsumer:
    def __init__(self):
        self.initialized = True

    def analyze_certified_oia_artifacts(
        self,
        *,
        certified_artifacts,
        execution_context,
    ):
        raise AssertionError("INT-OIA-009 must not invoke the callable")


def _install_test_module() -> None:
    module = types.ModuleType(TEST_MODULE)
    module.OracleResearchAnalyticsConsumer = OracleResearchAnalyticsConsumer
    sys.modules[TEST_MODULE] = module


def _seed_resolution(path: Path) -> None:
    callable_path = (
        f"{TEST_MODULE}."
        "OracleResearchAnalyticsConsumer."
        "analyze_certified_oia_artifacts"
    )
    record = {
        "sequence": 1,
        "resolution_attestation_id": "resolution-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": TEST_MODULE,
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": "analyze_certified_oia_artifacts",
        "callable_path": callable_path,
        "source_resolution_readiness_id": "resolution-readiness-test",
        "source_resolution_readiness_record_hash": stable_hash(
            {"readiness": 1}
        ),
        "source_binding_contract_id": "binding-test",
        "source_binding_contract_hash": stable_hash({"binding": 1}),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "module_imported": True,
        "class_resolved": True,
        "callable_resolved": True,
        "callable_is_callable": True,
        "callable_is_coroutine": False,
        "callable_signature": (
            "(self, *, certified_artifacts, execution_context)"
        ),
        "callable_parameter_names": [
            "self",
            "certified_artifacts",
            "execution_context",
        ],
        "callable_bound": False,
        "callable_invoked": False,
        "consumer_instantiated": False,
        "corpus_read_performed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "resolution_status": "resolved_not_bound",
    }
    record["resolution_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-008",
        "engine_id": "INT-OIA-008",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "resolution_attestation_manifest_id": "int-oia-008-test",
        "resolution_attestation_status": (
            "downstream_read_only_consumer_callable_resolution_attested"
        ),
        "resolution_attestation_policy_id": "test",
        "source_resolution_readiness_manifest_id": "int-oia-007-test",
        "source_resolution_readiness_manifest_hash": stable_hash(
            {"int": 7}
        ),
        "source_binding_manifest_id": "int-oia-006-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_readiness_hashes_verified": True,
        "all_modules_imported": True,
        "all_classes_resolved": True,
        "all_callables_resolved": True,
        "all_callables_callable": True,
        "exact_callable_identity_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "callable_binding_allowed": True,
        "callable_binding_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
        "consumer_instantiation_performed": False,
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
        "controlled_callable_binding_authorized": True,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["resolution_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-009 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING ATTESTATION")
    print("=" * 40)

    _install_test_module()

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        resolution = root / "resolution"
        binding = root / "binding"
        _seed_resolution(resolution)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationGate(
            resolution_directory=resolution,
            binding_directory=binding,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-009"
        assert first.attestation_record_count == 1
        assert first.all_resolution_hashes_verified
        assert first.all_consumers_instantiated
        assert first.all_callables_bound
        assert first.all_bound_callables_callable
        assert first.exact_callable_identity_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.callable_invocation_allowed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_callable_invocation_authorized
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.attestation_records[0]
        assert record.consumer_instantiated
        assert record.callable_bound
        assert record.bound_callable_is_callable
        assert record.bound_callable_parameter_names == (
            "certified_artifacts",
            "execution_context",
        )
        assert len(record.bound_callable_identity_hash) == 64
        assert record.callable_invocation_allowed
        assert not record.callable_invocation_performed
        assert not record.corpus_read_performed
        assert record.binding_status == "bound_not_invoked"

        assert (binding / "current.json").exists()

        tampered = json.loads(
            (resolution / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "callable_invoked"
        ] = True
        (resolution / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered resolution accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-008 resolution attestation consumed")
    print("[PASS] Every resolution-attestation hash verified")
    print("[PASS] Exact consumer class instantiated")
    print("[PASS] Exact approved analytical callable bound")
    print("[PASS] Bound callable signature captured deterministically")
    print("[PASS] Bound callable identity hash persisted")
    print("[PASS] Controlled callable invocation authorized")
    print("[PASS] Callable was not invoked")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe resolution evidence rejected")
    print("[PASS] Atomic binding-attestation artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
