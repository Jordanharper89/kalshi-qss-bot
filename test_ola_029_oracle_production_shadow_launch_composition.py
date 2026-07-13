from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowServiceRunner,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_controlled_unattended_shadow_run_entrypoint import (
    create_oracle_filesystem_stop_controller,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_launch_readiness_artifact_store import (
    OracleLaunchReadinessArtifactStore,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_production_shadow_launch_composition import (
    OracleProductionShadowLaunchCompositionBlocked,
    run_oracle_production_shadow_launch,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.production_evidence_service_runner_binding import (
    create_production_evidence_service_runner_binding,
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

from test_ola_023_oracle_live_shadow_service_runner import (
    build_components,
    initial_state,
    readiness_kwargs_factory,
    scheduler_kwargs_factory,
)

from test_ola_026_oracle_shadow_launch_readiness_gate import (
    _build_production_gate_record,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_shadow_launch_readiness_gate import (
    evaluate_oracle_shadow_launch_readiness,
)


def _build_launch_readiness(
    *,
    root: Path,
):
    fetcher = DeterministicHealthyFetcher()

    adapter, live_gate = build_gate(
        fetcher=fetcher
    )

    live_readiness = evaluate_gate(
        gate=live_gate
    )

    service_isolation = (
        build_service_contract()
    )

    bootstrap_record = (
        build_bootstrap_record()
    )

    (
        readiness_runtime_root,
        production_gate_record,
    ) = _build_production_gate_record(
        root=root / "readiness-proof"
    )

    readiness_record = (
        evaluate_oracle_shadow_launch_readiness(
            live_readiness_record=live_readiness,
            service_isolation_contract=(
                service_isolation
            ),
            bootstrap_record=bootstrap_record,
            production_evidence_gate_record=(
                production_gate_record
            ),
            runtime_root=readiness_runtime_root,
        )
    )

    assert readiness_record.launch_ready is True

    assert (
        readiness_record.verify_readiness_hash()
        is True
    )

    return readiness_record


def _build_runner_composition(
    *,
    runtime_root: Path,
    stop_controller,
):
    baseline = build_components()

    baseline_runner = baseline["runner"]

    production_binding = (
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
                "writer.oracle.production.state.ola029"
            ),
            evidence_role="runtime/state",
            writer_callable=(
                production_binding.state_writer_callable()
            ),
            read_only_service_boundary=True,
            execution_allowed=False,
        ),
        log_writer=OracleLiveShadowEvidenceWriterBinding(
            writer_id=(
                "writer.oracle.production.logs.ola029"
            ),
            evidence_role="runtime/logs",
            writer_callable=(
                production_binding.log_writer_callable()
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
        stop_requested_callable=stop_controller,
        service_tick_interval_seconds=(
            baseline_runner._service_tick_interval_seconds
        ),
    )

    return (
        runner,
        production_binding,
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(
            temporary_directory
        ).resolve()

        readiness_record = (
            _build_launch_readiness(
                root=root
            )
        )

        runtime_root = (
            root
            / "production-runtime"
        )

        readiness_store = (
            OracleLaunchReadinessArtifactStore(
                runtime_root=runtime_root
            )
        )

        receipt = readiness_store.persist(
            readiness_record=readiness_record
        )

        assert receipt.engine_id == "OLA-028"

        loaded_readiness = (
            readiness_store.load_current()
        )

        assert (
            loaded_readiness
            == readiness_record
        )

        stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=runtime_root
            )
        )

        (
            runner,
            production_binding,
        ) = _build_runner_composition(
            runtime_root=runtime_root,
            stop_controller=stop_controller,
        )

        composition_record = (
            run_oracle_production_shadow_launch(
                runtime_root=runtime_root,
                readiness_store=readiness_store,
                runner=runner,
                production_binding=production_binding,
                stop_controller=stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
                service_metadata={
                    "test": "ola029",
                    "collection": (
                        "first_controlled_corpus"
                    ),
                },
            )
        )

        assert composition_record.schema_version == "OLA-029"
        assert composition_record.engine_id == "OLA-029"

        assert (
            composition_record.composition_status
            == "completed"
        )

        assert composition_record.launch_invoked is True

        assert (
            composition_record.readiness_store_engine_id
            == "OLA-028"
        )

        assert (
            composition_record.readiness_schema_version
            == "OLA-026"
        )

        assert (
            composition_record.readiness_hash
            == readiness_record.readiness_hash
        )

        assert composition_record.launch_ready is True

        assert (
            composition_record.runner_engine_id
            == "OLA-023"
        )

        assert (
            composition_record.production_binding_engine_id
            == "OLA-025"
        )

        assert (
            composition_record.production_writer_engine_id
            == "OLA-024"
        )

        assert (
            composition_record.entrypoint_engine_id
            == "OLA-027"
        )

        assert (
            composition_record.runtime_root
            == runtime_root.as_posix()
        )

        assert (
            composition_record.stop_signal_path
            == stop_controller.stop_signal_path.as_posix()
        )

        assert (
            composition_record.configured_max_iterations
            == 3
        )

        assert (
            composition_record.completed_iteration_count
            == 3
        )

        assert (
            composition_record.controlled_run_status
            == "completed"
        )

        assert (
            composition_record.service_run_status
            == "completed"
        )

        assert composition_record.state_write_count == 3
        assert composition_record.log_write_count == 3

        assert (
            composition_record.runtime_root_identity_match
            is True
        )

        assert (
            composition_record.exact_runner_stop_callable_bound
            is True
        )

        assert (
            composition_record.readiness_artifact_loaded
            is True
        )

        assert (
            composition_record.readiness_hash_verified
            is True
        )

        assert (
            composition_record.bounded_entrypoint_invoked
            is True
        )

        assert (
            composition_record.exactly_one_state_write_per_iteration
            is True
        )

        assert (
            composition_record.exactly_one_log_write_per_iteration
            is True
        )

        assert (
            composition_record.current_state_pointer_present
            is True
        )

        assert (
            runtime_root
            / "state"
            / "current.json"
        ).is_file()

        assert composition_record.read_only is True
        assert composition_record.alerts_allowed is False

        assert (
            composition_record.qseries_intake_allowed
            is False
        )

        assert (
            composition_record.canonical_handoff_published
            is False
        )

        assert (
            composition_record.execution_allowed
            is False
        )

        assert (
            composition_record.execution_adapter_resolved
            is False
        )

        assert (
            composition_record.execution_adapter_invoked
            is False
        )

        assert (
            composition_record.trade_authorization_allowed
            is False
        )

        assert (
            composition_record.order_placement_allowed
            is False
        )

        assert composition_record.funds_moved is False

        assert (
            composition_record.portfolio_mutated
            is False
        )

        assert composition_record.immutable is True
        assert composition_record.replayable is True
        assert composition_record.auditable is True
        assert composition_record.explainable is True

        assert (
            composition_record.verify_composition_hash()
            is True
        )

        mismatched_runtime_root = (
            root
            / "wrong-runtime"
        )

        mismatch_blocked = False

        try:
            run_oracle_production_shadow_launch(
                runtime_root=mismatched_runtime_root,
                readiness_store=readiness_store,
                runner=runner,
                production_binding=production_binding,
                stop_controller=stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
            )

        except OracleProductionShadowLaunchCompositionBlocked:
            mismatch_blocked = True

        assert mismatch_blocked is True

        override_runtime_root = (
            root
            / "override-runtime"
        )

        override_store = (
            OracleLaunchReadinessArtifactStore(
                runtime_root=override_runtime_root
            )
        )

        override_store.persist(
            readiness_record=readiness_record
        )

        override_stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=override_runtime_root
            )
        )

        (
            override_runner,
            override_binding,
        ) = _build_runner_composition(
            runtime_root=override_runtime_root,
            stop_controller=override_stop_controller,
        )

        authority_override_blocked = False

        try:
            run_oracle_production_shadow_launch(
                runtime_root=override_runtime_root,
                readiness_store=override_store,
                runner=override_runner,
                production_binding=override_binding,
                stop_controller=override_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
                service_metadata={
                    "execution_allowed": True,
                },
            )

        except OracleProductionShadowLaunchCompositionBlocked:
            authority_override_blocked = True

        assert authority_override_blocked is True

        blocked_runtime_root = (
            root
            / "blocked-runtime"
        )

        blocked_store = (
            OracleLaunchReadinessArtifactStore(
                runtime_root=blocked_runtime_root
            )
        )

        blocked_readiness = replace(
            readiness_record,
            launch_ready=False,
            readiness_status="blocked",
        )

        blocked_persist = False

        try:
            blocked_store.persist(
                readiness_record=blocked_readiness
            )

        except Exception:
            blocked_persist = True

        assert blocked_persist is True

        assert composition_record.controlled_run_hash

        result = {
            "schema_version": "OLA-029",
            "engine_id": "OLA-029",
            "status": "passed",
            "ola_028_readiness_artifact_loaded": True,
            "ola_026_readiness_hash_verified": True,
            "synthetic_launch_authorization_created": False,
            "actual_ola_023_runner_required": True,
            "ola_025_production_binding_required": True,
            "ola_024_production_writer_required": True,
            "ola_027_bounded_entrypoint_invoked": True,
            "single_runtime_root_identity_required": True,
            "exact_runner_stop_callable_required": True,
            "stop_path_confinement_preserved": True,
            "bounded_run_iteration_count": 3,
            "exactly_one_state_write_per_iteration": True,
            "exactly_one_log_write_per_iteration": True,
            "current_state_pointer_present": True,
            "runtime_root_mismatch_fails_closed": True,
            "authority_metadata_override_fails_closed": True,
            "blocked_readiness_cannot_be_persisted": True,
            "composition_hash_valid": True,
            "read_only": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "canonical_handoff_published": False,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        print(
            "[PASS] OLA-029 Oracle Production "
            "Shadow Launch Composition"
        )

        print(result)


if __name__ == "__main__":
    main()
