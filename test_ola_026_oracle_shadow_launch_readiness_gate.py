from __future__ import annotations

from dataclasses import replace
import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_shadow_launch_readiness_gate import (
    OracleShadowLaunchReadinessGateError,
    _canonical_source_material,
    _hash_source_evidence,
    evaluate_oracle_shadow_launch_readiness,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_production_evidence_service_runner_full_integration_gate import (
    evaluate_oracle_production_evidence_integration,
)

from test_ola_018_oracle_kalshi_live_read_readiness_gate import (
    DeterministicHealthyFetcher,
    build_gate,
    evaluate_gate,
)

from test_ola_020_oracle_service_isolation_canonical_intelligence_handoff_contract import (
    build_service_contract,
)

from test_ola_022_oracle_live_shadow_service_bootstrap_contract import (
    build_bootstrap_record,
)

from test_int_ola_prod_evidence_001_oracle_production_evidence_service_runner_full_integration_gate import (
    _run_explicit_stop,
    _run_three_iterations,
)


class ToDictOnlyEvidence:

    def to_dict(self):
        return {
            "schema_version": "TEST",
            "engine_id": "TEST",
            "value": 1,
        }


class InvalidCanonicalEvidence:

    def to_canonical_dict(self):
        return "not-a-mapping"


class UnsupportedEvidence:
    pass


def _build_production_gate_record(
    *,
    root: Path,
):
    runtime_root = (
        root / "runtime-primary"
    )

    replay_runtime_root = (
        root / "runtime-replay"
    )

    stop_runtime_root = (
        root / "runtime-stop"
    )

    primary_result, primary_components = (
        _run_three_iterations(
            runtime_root
        )
    )

    (
        run_record,
        iteration_records,
        final_state,
    ) = primary_result

    replay_result, replay_components = (
        _run_three_iterations(
            replay_runtime_root
        )
    )

    (
        replay_run_record,
        replay_iteration_records,
        replay_final_state,
    ) = replay_result

    stop_result, stop_components = (
        _run_explicit_stop(
            stop_runtime_root
        )
    )

    (
        explicit_stop_run_record,
        explicit_stop_iteration_records,
        explicit_stop_final_state,
    ) = stop_result

    assert (
        explicit_stop_final_state.consecutive_failures
        == 0
    )

    assert (
        stop_components["binding"].state_write_count
        == 2
    )

    production_gate_record = (
        evaluate_oracle_production_evidence_integration(
            runtime_root=runtime_root,
            replay_runtime_root=(
                replay_runtime_root
            ),
            run_record=run_record,
            iteration_records=iteration_records,
            final_state=final_state,
            binding=primary_components["binding"],
            replay_run_record=replay_run_record,
            replay_iteration_records=(
                replay_iteration_records
            ),
            replay_final_state=replay_final_state,
            replay_binding=(
                replay_components["binding"]
            ),
            explicit_stop_run_record=(
                explicit_stop_run_record
            ),
            explicit_stop_iteration_records=(
                explicit_stop_iteration_records
            ),
        )
    )

    return (
        runtime_root,
        production_gate_record,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(
            temporary_directory
        ).resolve()

        healthy_fetcher = (
            DeterministicHealthyFetcher()
        )

        adapter, live_gate = build_gate(
            fetcher=healthy_fetcher
        )

        live_readiness_record = evaluate_gate(
            gate=live_gate
        )

        service_isolation_contract = (
            build_service_contract()
        )

        bootstrap_record = (
            build_bootstrap_record()
        )

        (
            runtime_root,
            production_gate_record,
        ) = _build_production_gate_record(
            root=root
        )

        assert hasattr(
            live_readiness_record,
            "to_canonical_dict",
        )

        assert hasattr(
            service_isolation_contract,
            "to_canonical_dict",
        )

        assert hasattr(
            bootstrap_record,
            "to_canonical_dict",
        )

        live_material = _canonical_source_material(
            live_readiness_record,
            field_name="live_readiness_record",
        )

        isolation_material = _canonical_source_material(
            service_isolation_contract,
            field_name="service_isolation_contract",
        )

        bootstrap_material = _canonical_source_material(
            bootstrap_record,
            field_name="bootstrap_record",
        )

        production_material = _canonical_source_material(
            production_gate_record,
            field_name="production_gate_record",
        )

        assert (
            live_material["schema_version"]
            == "OLA-018"
        )

        assert (
            isolation_material["schema_version"]
            == "OLA-020"
        )

        assert (
            bootstrap_material["schema_version"]
            == "OLA-022"
        )

        assert (
            production_material["schema_version"]
            == "INT-OLA-PROD-EVIDENCE-001"
        )

        to_dict_material = _canonical_source_material(
            ToDictOnlyEvidence(),
            field_name="to_dict_only",
        )

        assert to_dict_material["value"] == 1

        mapping_material = _canonical_source_material(
            {
                "schema_version": "MAP",
                "engine_id": "MAP",
            },
            field_name="mapping",
        )

        assert (
            mapping_material["schema_version"]
            == "MAP"
        )

        invalid_canonical_failed_closed = False

        try:
            _canonical_source_material(
                InvalidCanonicalEvidence(),
                field_name="invalid_canonical",
            )
        except OracleShadowLaunchReadinessGateError:
            invalid_canonical_failed_closed = True

        assert invalid_canonical_failed_closed is True

        unsupported_failed_closed = False

        try:
            _canonical_source_material(
                UnsupportedEvidence(),
                field_name="unsupported",
            )
        except OracleShadowLaunchReadinessGateError:
            unsupported_failed_closed = True

        assert unsupported_failed_closed is True

        source_hashes = {
            "live": _hash_source_evidence(
                live_readiness_record,
                field_name="live",
            ),
            "isolation": _hash_source_evidence(
                service_isolation_contract,
                field_name="isolation",
            ),
            "bootstrap": _hash_source_evidence(
                bootstrap_record,
                field_name="bootstrap",
            ),
            "production": _hash_source_evidence(
                production_gate_record,
                field_name="production",
            ),
        }

        assert all(
            isinstance(value, str)
            and len(value) == 64
            for value in source_hashes.values()
        )

        readiness = (
            evaluate_oracle_shadow_launch_readiness(
                live_readiness_record=(
                    live_readiness_record
                ),
                service_isolation_contract=(
                    service_isolation_contract
                ),
                bootstrap_record=bootstrap_record,
                production_evidence_gate_record=(
                    production_gate_record
                ),
                runtime_root=runtime_root,
            )
        )

        assert readiness.schema_version == "OLA-026"
        assert readiness.engine_id == "OLA-026"
        assert readiness.readiness_status == "ready"
        assert readiness.launch_ready is True

        assert (
            readiness.live_read_readiness_passed
            is True
        )
        assert readiness.public_endpoint_only is True
        assert (
            readiness.authentication_not_used
            is True
        )
        assert (
            readiness.one_live_get_probe_observed
            is True
        )
        assert readiness.source_reachable is True
        assert (
            readiness.source_control_acquisition_allowed
            is True
        )

        assert (
            readiness.service_isolation_passed
            is True
        )
        assert (
            readiness.oracle_service_id
            == "service.oracle.intelligence"
        )
        assert (
            readiness.qseries_service_id
            == "service.qseries.execution"
        )
        assert (
            readiness.separate_process_required
            is True
        )
        assert (
            readiness.oracle_execution_authority
            is False
        )
        assert (
            readiness.direct_execution_import_allowed
            is False
        )
        assert (
            readiness.qseries_oracle_history_mutation_allowed
            is False
        )

        assert (
            readiness.bootstrap_readiness_passed
            is True
        )
        assert readiness.bootstrap_status == "ready"
        assert readiness.service_start_allowed is True
        assert (
            readiness.runtime_state_role_valid
            is True
        )
        assert (
            readiness.runtime_logs_role_valid
            is True
        )

        assert (
            readiness.production_evidence_gate_passed
            is True
        )
        assert (
            readiness.actual_ola_023_runner_proven
            is True
        )
        assert (
            readiness.ola_025_actual_payload_binding_proven
            is True
        )
        assert (
            readiness.ola_024_production_persistence_proven
            is True
        )

        assert (
            readiness.exactly_one_state_write_per_iteration_proven
            is True
        )
        assert (
            readiness.exactly_one_log_write_per_iteration_proven
            is True
        )
        assert (
            readiness.current_state_pointer_proven
            is True
        )
        assert (
            readiness.polling_state_chain_proven
            is True
        )
        assert (
            readiness.canonical_clock_lineage_proven
            is True
        )
        assert (
            readiness.deterministic_replay_proven
            is True
        )
        assert (
            readiness.immutable_evidence_proven
            is True
        )
        assert (
            readiness.replayable_evidence_proven
            is True
        )
        assert (
            readiness.audit_evidence_proven
            is True
        )
        assert readiness.explicit_stop_proven is True

        assert readiness.runtime_root_ready is True
        assert (
            readiness.runtime_state_directory_ready
            is True
        )
        assert (
            readiness.runtime_logs_directory_ready
            is True
        )

        assert (
            readiness.unattended_collection_started
            is False
        )

        assert readiness.alerts_allowed is False
        assert (
            readiness.qseries_intake_allowed
            is False
        )
        assert (
            readiness.canonical_handoff_published
            is False
        )
        assert readiness.read_only is True
        assert readiness.execution_allowed is False
        assert (
            readiness.execution_adapter_resolved
            is False
        )
        assert (
            readiness.execution_adapter_invoked
            is False
        )
        assert (
            readiness.trade_authorization_allowed
            is False
        )
        assert (
            readiness.order_placement_allowed
            is False
        )
        assert readiness.funds_moved is False
        assert readiness.portfolio_mutated is False

        assert readiness.immutable is True
        assert readiness.replayable is True
        assert readiness.auditable is True
        assert readiness.explainable is True

        assert readiness.verify_readiness_hash() is True

        assert len(
            readiness.source_evidence_hashes
        ) == 4

        readiness_hash_map = dict(
            readiness.source_evidence_hashes
        )

        assert (
            readiness_hash_map[
                "ola_018_live_readiness"
            ]
            == source_hashes["live"]
        )

        assert (
            readiness_hash_map[
                "ola_020_service_isolation"
            ]
            == source_hashes["isolation"]
        )

        assert (
            readiness_hash_map[
                "ola_022_bootstrap"
            ]
            == source_hashes["bootstrap"]
        )

        assert (
            readiness_hash_map[
                "int_ola_prod_evidence_001"
            ]
            == source_hashes["production"]
        )

        replay_readiness = (
            evaluate_oracle_shadow_launch_readiness(
                live_readiness_record=(
                    live_readiness_record
                ),
                service_isolation_contract=(
                    service_isolation_contract
                ),
                bootstrap_record=bootstrap_record,
                production_evidence_gate_record=(
                    production_gate_record
                ),
                runtime_root=runtime_root,
            )
        )

        assert (
            replay_readiness.to_dict()
            == readiness.to_dict()
        )

        blocked_production_gate = replace(
            production_gate_record,
            explicit_stop_observed=False,
        )

        blocked_readiness = (
            evaluate_oracle_shadow_launch_readiness(
                live_readiness_record=(
                    live_readiness_record
                ),
                service_isolation_contract=(
                    service_isolation_contract
                ),
                bootstrap_record=bootstrap_record,
                production_evidence_gate_record=(
                    blocked_production_gate
                ),
                runtime_root=runtime_root,
            )
        )

        assert (
            blocked_readiness.readiness_status
            == "blocked"
        )
        assert blocked_readiness.launch_ready is False
        assert (
            blocked_readiness.explicit_stop_proven
            is False
        )
        assert (
            "blocked:explicit_stop_proven"
            in blocked_readiness.reason_codes
        )

        blocked_live_readiness = replace(
            live_readiness_record,
            readiness_status="blocked",
            live_shadow_cycle_entry_ready=False,
        )

        blocked_live_result = (
            evaluate_oracle_shadow_launch_readiness(
                live_readiness_record=(
                    blocked_live_readiness
                ),
                service_isolation_contract=(
                    service_isolation_contract
                ),
                bootstrap_record=bootstrap_record,
                production_evidence_gate_record=(
                    production_gate_record
                ),
                runtime_root=runtime_root,
            )
        )

        assert blocked_live_result.launch_ready is False

        assert (
            blocked_live_result.live_read_readiness_passed
            is False
        )

        print(
            "[PASS] OLA-026 Oracle Shadow "
            "Launch Readiness Gate"
        )

        print(
            readiness.to_dict()
        )


if __name__ == "__main__":
    main()
