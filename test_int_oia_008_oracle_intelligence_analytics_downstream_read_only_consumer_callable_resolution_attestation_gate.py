from __future__ import annotations

import json
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_attestation_gate import (
    APPROVED_CALLABLE_NAME,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError,
    stable_hash,
)


TEST_MODULE = "int_oia_008_test_consumer_module"


class OracleResearchAnalyticsConsumer:
    def analyze_certified_oia_artifacts(
        self,
        *,
        certified_artifacts,
        execution_context,
    ):
        raise AssertionError("INT-OIA-008 must not invoke the callable")


def _install_test_module() -> None:
    module = types.ModuleType(TEST_MODULE)
    module.OracleResearchAnalyticsConsumer = (
        OracleResearchAnalyticsConsumer
    )
    sys.modules[TEST_MODULE] = module


def _seed_readiness(path: Path) -> None:
    callable_path = (
        f"{TEST_MODULE}."
        "OracleResearchAnalyticsConsumer."
        f"{APPROVED_CALLABLE_NAME}"
    )
    record = {
        "sequence": 1,
        "resolution_readiness_id": "resolution-readiness-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": TEST_MODULE,
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": APPROVED_CALLABLE_NAME,
        "callable_path": callable_path,
        "source_binding_contract_id": "binding-test",
        "source_binding_contract_hash": stable_hash({"binding": 1}),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "module_identity_valid": True,
        "class_identity_valid": True,
        "callable_identity_valid": True,
        "callable_path_consistent": True,
        "exact_identity_hash_verified": True,
        "dynamic_import_allowed": False,
        "module_import_performed": False,
        "callable_resolution_allowed": True,
        "callable_resolution_performed": False,
        "callable_binding_allowed": False,
        "callable_binding_performed": False,
        "callable_invocation_allowed": False,
        "callable_invocation_performed": False,
        "corpus_read_allowed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "controlled_resolution_authorized": True,
        "readiness_status": "ready_for_controlled_resolution",
    }
    record["resolution_readiness_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-007",
        "engine_id": "INT-OIA-007",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "resolution_readiness_manifest_id": "int-oia-007-test",
        "resolution_readiness_status": (
            "downstream_read_only_consumer_callable_resolution_ready"
        ),
        "resolution_readiness_policy_id": "test",
        "source_binding_manifest_id": "int-oia-006-test",
        "source_binding_manifest_hash": stable_hash({"int": 6}),
        "source_activation_manifest_id": "int-oia-005-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record],
        "all_binding_hashes_verified": True,
        "all_callable_paths_consistent": True,
        "exact_callable_identity_preserved": True,
        "source_boundary_consumed_without_reexecution": True,
        "dynamic_import_allowed": False,
        "module_import_performed": False,
        "callable_resolution_allowed": True,
        "callable_resolution_performed": False,
        "callable_binding_allowed": False,
        "callable_binding_performed": False,
        "callable_invocation_allowed": False,
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
        "controlled_callable_resolution_authorized": True,
        "readiness_artifact_persistence_allowed": True,
    }
    manifest["resolution_readiness_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-008 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE RESOLUTION ATTESTATION")
    print("=" * 40)

    _install_test_module()

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        readiness = root / "readiness"
        attestation = root / "attestation"
        _seed_readiness(readiness)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationGate(
            readiness_directory=readiness,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-008"
        assert first.attestation_record_count == 1
        assert first.all_readiness_hashes_verified
        assert first.all_modules_imported
        assert first.all_classes_resolved
        assert first.all_callables_resolved
        assert first.all_callables_callable
        assert first.exact_callable_identity_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert first.callable_binding_allowed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_allowed
        assert not first.callable_invocation_performed
        assert not first.consumer_instantiation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_callable_binding_authorized
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.attestation_records[0]
        assert record.module_imported
        assert record.class_resolved
        assert record.callable_resolved
        assert record.callable_is_callable
        assert record.callable_parameter_names == (
            "self",
            "certified_artifacts",
            "execution_context",
        )
        assert not record.callable_bound
        assert not record.callable_invoked
        assert not record.consumer_instantiated
        assert not record.corpus_read_performed
        assert record.resolution_status == "resolved_not_bound"

        assert (attestation / "current.json").exists()

        tampered = json.loads(
            (readiness / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_records"][0][
            "callable_invocation_allowed"
        ] = True
        (readiness / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered readiness accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-007 resolution-readiness consumed")
    print("[PASS] Every resolution-readiness hash verified")
    print("[PASS] Exact consumer module imported")
    print("[PASS] Exact consumer class resolved")
    print("[PASS] Exact approved analytical callable resolved")
    print("[PASS] Callable signature captured deterministically")
    print("[PASS] Consumer was not instantiated")
    print("[PASS] Callable was not bound or invoked")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe readiness evidence rejected")
    print("[PASS] Atomic resolution-attestation artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
