from __future__ import annotations

import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowServiceRunner,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_production_evidence_service_runner_full_integration_gate import (
    evaluate_oracle_production_evidence_integration,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.production_evidence_service_runner_binding import (
    create_production_evidence_service_runner_binding,
)

from test_ola_023_oracle_live_shadow_service_runner import (
    build_components,
    initial_state,
    readiness_kwargs_factory,
    scheduler_kwargs_factory,
)


def _build_runner(
    *,
    runtime_root: Path,
    stop_after_checks=None,
):
    baseline = build_components(
        stop_after_checks=stop_after_checks
    )

    baseline_runner = baseline["runner"]

    binding = (
        create_production_evidence_service_runner_binding(
            runtime_root
        )
    )

    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=(
            baseline_runner._bootstrap_record
        ),
        readiness_provider=(
            baseline_runner._readiness_provider
        ),
        scheduler=baseline_runner._scheduler,
        state_writer=OracleLiveShadowEvidenceWriterBinding(
            writer_id=(
                "writer.oracle.production.state.ola025"
            ),
            evidence_role="runtime/state",
            writer_callable=(
                binding.state_writer_callable()
            ),
            read_only_service_boundary=True,
            execution_allowed=False,
        ),
        log_writer=OracleLiveShadowEvidenceWriterBinding(
            writer_id=(
                "writer.oracle.production.logs.ola025"
            ),
            evidence_role="runtime/logs",
            writer_callable=(
                binding.log_writer_callable()
            ),
            read_only_service_boundary=True,
            execution_allowed=False,
        ),
        clock_callable=(
            baseline_runner._clock_callable
        ),
        sleep_callable=(
            baseline_runner._sleep_callable
        ),
        stop_requested_callable=(
            baseline_runner._stop_requested_callable
        ),
        service_tick_interval_seconds=(
            baseline_runner._service_tick_interval_seconds
        ),
    )

    return {
        "runner": runner,
        "binding": binding,
        "baseline": baseline,
    }


def _run_three_iterations(
    runtime_root: Path,
):
    components = _build_runner(
        runtime_root=runtime_root
    )

    result = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=3,
        readiness_kwargs_factory=(
            readiness_kwargs_factory
        ),
        scheduler_kwargs_factory=(
            scheduler_kwargs_factory
        ),
        service_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
            "integration_gate": (
                "INT-OLA-PROD-EVIDENCE-001"
            ),
            "unattended_collection_started": False,
        },
    )

    return result, components


def _run_explicit_stop(
    runtime_root: Path,
):
    components = _build_runner(
        runtime_root=runtime_root,
        stop_after_checks=4,
    )

    result = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=None,
        readiness_kwargs_factory=(
            readiness_kwargs_factory
        ),
        scheduler_kwargs_factory=(
            scheduler_kwargs_factory
        ),
        service_metadata={
            "integration_gate": (
                "INT-OLA-PROD-EVIDENCE-001"
            ),
            "test": "explicit_stop",
            "unattended_collection_started": False,
        },
    )

    return result, components


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(
            temporary_directory
        ).resolve()

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

        assert run_record.schema_version == "OLA-023"
        assert run_record.engine_id == "OLA-023"
        assert (
            run_record.service_run_status
            == "completed"
        )
        assert run_record.iteration_count == 3
        assert len(iteration_records) == 3

        assert (
            primary_components["binding"].state_write_count
            == 3
        )
        assert (
            primary_components["binding"].log_write_count
            == 3
        )

        assert (
            primary_components[
                "baseline"
            ]["readiness_provider"].calls
            == 3
        )

        assert (
            primary_components[
                "baseline"
            ]["tick_binding"].calls
            == 3
        )

        assert (
            primary_components[
                "baseline"
            ]["cycle_runner"].calls
            == 3
        )

        assert run_record.verify_service_run_hash() is True

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

        explicit_stop_result, stop_components = (
            _run_explicit_stop(
                stop_runtime_root
            )
        )

        (
            explicit_stop_run_record,
            explicit_stop_iteration_records,
            explicit_stop_final_state,
        ) = explicit_stop_result

        assert (
            explicit_stop_run_record.service_run_status
            == "stopped"
        )
        assert (
            explicit_stop_run_record.stop_requested
            is True
        )
        assert (
            explicit_stop_run_record.iteration_count
            == 2
        )
        assert (
            len(explicit_stop_iteration_records)
            == 2
        )

        assert (
            stop_components["binding"].state_write_count
            == 2
        )
        assert (
            stop_components["binding"].log_write_count
            == 2
        )

        assert (
            explicit_stop_final_state.consecutive_failures
            == 0
        )

        gate_record = (
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

        assert gate_record.status == "passed"

        assert (
            gate_record.actual_ola_023_runner_executed
            is True
        )
        assert (
            gate_record.ola_025_actual_payload_binding_executed
            is True
        )
        assert (
            gate_record.ola_024_production_persistence_executed
            is True
        )

        assert gate_record.iteration_count == 3
        assert gate_record.state_evidence_file_count == 3
        assert gate_record.log_evidence_file_count == 3

        assert (
            gate_record.exactly_one_state_write_per_iteration
            is True
        )
        assert (
            gate_record.exactly_one_log_write_per_iteration
            is True
        )

        assert (
            gate_record.state_evidence_physically_exists
            is True
        )
        assert (
            gate_record.log_evidence_physically_exists
            is True
        )

        assert (
            gate_record.atomic_current_state_pointer_present
            is True
        )
        assert (
            gate_record.current_state_pointer_advanced_to_final_iteration
            is True
        )

        assert (
            gate_record.polling_state_chain_preserved
            is True
        )
        assert (
            gate_record.canonical_clock_lineage_preserved
            is True
        )
        assert (
            gate_record.source_runner_payload_preserved
            is True
        )

        assert (
            gate_record.deterministic_replay_valid
            is True
        )
        assert (
            gate_record.deterministic_persistence_paths_valid
            is True
        )

        assert (
            gate_record.explicit_stop_observed
            is True
        )
        assert (
            gate_record.explicit_stop_returned_control
            is True
        )

        assert (
            gate_record.state_source_immutability_preserved
            is True
        )
        assert (
            gate_record.log_source_immutability_preserved
            is True
        )
        assert (
            gate_record.immutable_physical_records_preserved
            is True
        )
        assert (
            gate_record.immutable_evidence_preserved
            is True
        )

        assert (
            gate_record.replayable_evidence_preserved
            is True
        )
        assert (
            gate_record.audit_evidence_preserved
            is True
        )

        assert gate_record.read_only is True
        assert gate_record.alerts_allowed is False
        assert (
            gate_record.qseries_intake_allowed
            is False
        )
        assert (
            gate_record.canonical_handoff_published
            is False
        )
        assert gate_record.execution_allowed is False
        assert (
            gate_record.execution_adapter_resolved
            is False
        )
        assert (
            gate_record.execution_adapter_invoked
            is False
        )
        assert (
            gate_record.trade_authorization_allowed
            is False
        )
        assert (
            gate_record.order_placement_allowed
            is False
        )
        assert gate_record.funds_moved is False
        assert gate_record.portfolio_mutated is False

        assert gate_record.verify_gate_hash() is True

        print(
            "[PASS] INT-OLA-PROD-EVIDENCE-001 "
            "Oracle Production Evidence Service Runner "
            "Full Integration Gate"
        )

        print(
            gate_record.to_dict()
        )


if __name__ == "__main__":
    main()
