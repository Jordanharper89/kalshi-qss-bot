from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

MODULE_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_controlled_unattended_shadow_run_entrypoint.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_027_oracle_controlled_unattended_shadow_run_entrypoint.py"
)


TEST = r'''
from __future__ import annotations

from dataclasses import replace
import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowServiceRunner,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_controlled_unattended_shadow_run_entrypoint import (
    MAX_CONTROLLED_ITERATIONS,
    STOP_SIGNAL_FILENAME,
    OracleControlledUnattendedShadowRunBlocked,
    OracleControlledUnattendedShadowRunError,
    create_oracle_filesystem_stop_controller,
    run_controlled_unattended_shadow_collection,
)

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_shadow_launch_readiness_gate import (
    evaluate_oracle_shadow_launch_readiness,
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


class IterationBoundStopController:

    def __init__(
        self,
        *,
        controller,
        stop_after_checks,
    ):
        self.controller = controller
        self.stop_after_checks = stop_after_checks
        self.checks = 0

    @property
    def stop_signal_path(self):
        return self.controller.stop_signal_path

    @property
    def stop_observed(self):
        return self.controller.stop_observed

    def __call__(self):
        self.checks += 1

        if self.checks >= self.stop_after_checks:
            self.stop_signal_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.stop_signal_path.write_text(
                "stop",
                encoding="utf-8",
            )

        return self.controller()


class InvalidStopController:
    pass


class EscapedStopController:

    def __init__(
        self,
        path: Path,
    ):
        self.stop_signal_path = path
        self.stop_observed = False

    def __call__(self):
        return False


def _build_readiness(
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

    bootstrap = build_bootstrap_record()

    (
        readiness_runtime_root,
        production_gate,
    ) = _build_production_gate_record(
        root=root / "readiness"
    )

    readiness = (
        evaluate_oracle_shadow_launch_readiness(
            live_readiness_record=live_readiness,
            service_isolation_contract=(
                service_isolation
            ),
            bootstrap_record=bootstrap,
            production_evidence_gate_record=(
                production_gate
            ),
            runtime_root=(
                readiness_runtime_root
            ),
        )
    )

    assert readiness.launch_ready is True
    assert readiness.verify_readiness_hash() is True

    return readiness


def _build_actual_runner(
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
                "writer.oracle.production.state.ola027"
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
                "writer.oracle.production.logs.ola027"
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


def _semantic_run_projection(
    record,
) -> dict:
    """
    Compare deterministic semantic run outcomes while preserving
    root-bound physical provenance in the actual run records.

    runtime_root, stop_signal_path, service_run_id, service_run_hash,
    and OLA-027 run_hash are intentionally not normalized into equality.
    """
    return {
        "schema_version": record.schema_version,
        "engine_id": record.engine_id,
        "run_status": record.run_status,
        "controlled_unattended_run_started": (
            record.controlled_unattended_run_started
        ),
        "controlled_unattended_run_completed": (
            record.controlled_unattended_run_completed
        ),
        "launch_readiness_schema_version": (
            record.launch_readiness_schema_version
        ),
        "launch_readiness_hash": (
            record.launch_readiness_hash
        ),
        "launch_ready_at_entry": (
            record.launch_ready_at_entry
        ),
        "runner_engine_id": record.runner_engine_id,
        "production_binding_engine_id": (
            record.production_binding_engine_id
        ),
        "production_writer_engine_id": (
            record.production_writer_engine_id
        ),
        "max_iterations": record.max_iterations,
        "completed_iteration_count": (
            record.completed_iteration_count
        ),
        "service_run_status": (
            record.service_run_status
        ),
        "final_state_id": record.final_state_id,
        "final_state_hash": record.final_state_hash,
        "final_consecutive_failures": (
            record.final_consecutive_failures
        ),
        "final_state_suspended": (
            record.final_state_suspended
        ),
        "explicit_stop_observed": (
            record.explicit_stop_observed
        ),
        "iteration_limit_observed": (
            record.iteration_limit_observed
        ),
        "state_write_count": record.state_write_count,
        "log_write_count": record.log_write_count,
        "exactly_one_state_write_per_iteration": (
            record.exactly_one_state_write_per_iteration
        ),
        "exactly_one_log_write_per_iteration": (
            record.exactly_one_log_write_per_iteration
        ),
        "current_state_pointer_present": (
            record.current_state_pointer_present
        ),
        "read_only": record.read_only,
        "alerts_allowed": record.alerts_allowed,
        "qseries_intake_allowed": (
            record.qseries_intake_allowed
        ),
        "canonical_handoff_published": (
            record.canonical_handoff_published
        ),
        "execution_allowed": record.execution_allowed,
        "execution_adapter_resolved": (
            record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            record.order_placement_allowed
        ),
        "funds_moved": record.funds_moved,
        "portfolio_mutated": record.portfolio_mutated,
        "reason_codes": tuple(
            record.reason_codes
        ),
        "immutable": record.immutable,
        "replayable": record.replayable,
        "auditable": record.auditable,
        "explainable": record.explainable,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(
            temporary_directory
        ).resolve()

        readiness = _build_readiness(
            root=root
        )

        runtime_root = (
            root / "runtime-bounded"
        )

        stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=runtime_root
            )
        )

        assert (
            stop_controller.stop_signal_path
            == runtime_root
            / "state"
            / STOP_SIGNAL_FILENAME
        )

        runner, production_binding = (
            _build_actual_runner(
                runtime_root=runtime_root,
                stop_controller=stop_controller,
            )
        )

        run_record = (
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=runner,
                production_binding=production_binding,
                runtime_root=runtime_root,
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
                    "test": "bounded_first_run",
                },
            )
        )

        assert run_record.schema_version == "OLA-027"
        assert run_record.engine_id == "OLA-027"
        assert run_record.run_status == "completed"

        assert (
            run_record.controlled_unattended_run_started
            is True
        )

        assert (
            run_record.controlled_unattended_run_completed
            is True
        )

        assert (
            run_record.launch_readiness_schema_version
            == "OLA-026"
        )

        assert (
            run_record.launch_readiness_hash
            == readiness.readiness_hash
        )

        assert run_record.launch_ready_at_entry is True
        assert run_record.runner_engine_id == "OLA-023"

        assert (
            run_record.production_binding_engine_id
            == "OLA-025"
        )

        assert (
            run_record.production_writer_engine_id
            == "OLA-024"
        )

        assert run_record.max_iterations == 3
        assert run_record.completed_iteration_count == 3
        assert run_record.service_run_status == "completed"
        assert run_record.explicit_stop_observed is False
        assert run_record.iteration_limit_observed is True

        assert run_record.state_write_count == 3
        assert run_record.log_write_count == 3

        assert (
            run_record.exactly_one_state_write_per_iteration
            is True
        )

        assert (
            run_record.exactly_one_log_write_per_iteration
            is True
        )

        assert (
            run_record.current_state_pointer_present
            is True
        )

        assert (
            runtime_root
            / "state"
            / "current.json"
        ).exists()

        assert run_record.verify_run_hash() is True

        stop_runtime_root = (
            root / "runtime-stop"
        )

        base_stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=stop_runtime_root
            )
        )

        composed_stop_controller = (
            IterationBoundStopController(
                controller=base_stop_controller,
                stop_after_checks=4,
            )
        )

        stop_runner, stop_binding = (
            _build_actual_runner(
                runtime_root=stop_runtime_root,
                stop_controller=(
                    composed_stop_controller
                ),
            )
        )

        stop_record = (
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=stop_runner,
                production_binding=stop_binding,
                runtime_root=stop_runtime_root,
                stop_controller=(
                    composed_stop_controller
                ),
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=20,
                service_metadata={
                    "test": "explicit_stop",
                },
            )
        )

        assert stop_record.run_status == "stopped"
        assert stop_record.service_run_status == "stopped"
        assert stop_record.explicit_stop_observed is True
        assert stop_record.iteration_limit_observed is False
        assert stop_record.completed_iteration_count == 2
        assert stop_record.state_write_count == 2
        assert stop_record.log_write_count == 2
        assert stop_record.verify_run_hash() is True

        blocked_readiness = replace(
            readiness,
            launch_ready=False,
            readiness_status="blocked",
        )

        blocked_runtime_root = (
            root / "runtime-blocked"
        )

        blocked_stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=blocked_runtime_root
            )
        )

        blocked_runner, blocked_binding = (
            _build_actual_runner(
                runtime_root=blocked_runtime_root,
                stop_controller=blocked_stop_controller,
            )
        )

        readiness_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=(
                    blocked_readiness
                ),
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=blocked_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
            )
        except OracleControlledUnattendedShadowRunBlocked:
            readiness_blocked = True

        assert readiness_blocked is True
        assert blocked_binding.state_write_count == 0
        assert blocked_binding.log_write_count == 0

        unbounded_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=blocked_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=None,
            )
        except OracleControlledUnattendedShadowRunError:
            unbounded_blocked = True

        assert unbounded_blocked is True
        assert blocked_binding.state_write_count == 0
        assert blocked_binding.log_write_count == 0

        oversized_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=blocked_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=(
                    MAX_CONTROLLED_ITERATIONS + 1
                ),
            )
        except OracleControlledUnattendedShadowRunBlocked:
            oversized_blocked = True

        assert oversized_blocked is True
        assert blocked_binding.state_write_count == 0
        assert blocked_binding.log_write_count == 0

        metadata_override_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=blocked_stop_controller,
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
        except OracleControlledUnattendedShadowRunBlocked:
            metadata_override_blocked = True

        assert metadata_override_blocked is True
        assert blocked_binding.state_write_count == 0
        assert blocked_binding.log_write_count == 0

        invalid_stop_controller_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=InvalidStopController(),
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
            )
        except OracleControlledUnattendedShadowRunError:
            invalid_stop_controller_blocked = True

        assert invalid_stop_controller_blocked is True

        escaped_stop_controller = EscapedStopController(
            root / "STOP_OUTSIDE_RUNTIME"
        )

        escaped_stop_blocked = False

        try:
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=blocked_runner,
                production_binding=blocked_binding,
                runtime_root=blocked_runtime_root,
                stop_controller=escaped_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
            )
        except OracleControlledUnattendedShadowRunBlocked:
            escaped_stop_blocked = True

        assert escaped_stop_blocked is True

        replay_runtime_root = (
            root / "runtime-replay"
        )

        replay_stop_controller = (
            create_oracle_filesystem_stop_controller(
                runtime_root=replay_runtime_root
            )
        )

        replay_runner, replay_binding = (
            _build_actual_runner(
                runtime_root=replay_runtime_root,
                stop_controller=replay_stop_controller,
            )
        )

        replay_record = (
            run_controlled_unattended_shadow_collection(
                launch_readiness_record=readiness,
                runner=replay_runner,
                production_binding=replay_binding,
                runtime_root=replay_runtime_root,
                stop_controller=replay_stop_controller,
                initial_polling_state=initial_state(),
                readiness_kwargs_factory=(
                    readiness_kwargs_factory
                ),
                scheduler_kwargs_factory=(
                    scheduler_kwargs_factory
                ),
                max_iterations=3,
                service_metadata={
                    "test": "bounded_first_run",
                },
            )
        )

        assert (
            replay_record.runtime_root
            != run_record.runtime_root
        )

        assert (
            replay_record.stop_signal_path
            != run_record.stop_signal_path
        )

        assert (
            replay_record.service_run_hash
            != run_record.service_run_hash
        )

        assert (
            replay_record.run_hash
            != run_record.run_hash
        )

        assert (
            replay_record.final_state_hash
            == run_record.final_state_hash
        )

        assert (
            replay_record.final_state_id
            == run_record.final_state_id
        )

        assert (
            replay_record.completed_iteration_count
            == run_record.completed_iteration_count
        )

        assert (
            _semantic_run_projection(
                replay_record
            )
            == _semantic_run_projection(
                run_record
            )
        )

        assert replay_record.verify_run_hash() is True

        for record in (
            run_record,
            stop_record,
            replay_record,
        ):
            assert record.read_only is True
            assert record.alerts_allowed is False

            assert (
                record.qseries_intake_allowed
                is False
            )

            assert (
                record.canonical_handoff_published
                is False
            )

            assert record.execution_allowed is False

            assert (
                record.execution_adapter_resolved
                is False
            )

            assert (
                record.execution_adapter_invoked
                is False
            )

            assert (
                record.trade_authorization_allowed
                is False
            )

            assert (
                record.order_placement_allowed
                is False
            )

            assert record.funds_moved is False
            assert record.portfolio_mutated is False

        result = {
            "schema_version": "OLA-027",
            "engine_id": "OLA-027",
            "status": "passed",
            "ola_026_launch_ready_required": True,
            "actual_ola_023_runner_bound": True,
            "ola_025_production_binding_bound": True,
            "ola_024_production_writer_bound": True,
            "bounded_first_run_required": True,
            "max_iterations_none_allowed": False,
            "maximum_controlled_iterations": (
                MAX_CONTROLLED_ITERATIONS
            ),
            "stop_controller_contract_validated": True,
            "composed_stop_controller_supported": True,
            "exact_bound_stop_callable_required": True,
            "filesystem_stop_control_available": True,
            "stop_signal_role": (
                "runtime/state/"
                + STOP_SIGNAL_FILENAME
            ),
            "stop_path_confinement_validated": True,
            "bounded_run_iteration_count": (
                run_record.completed_iteration_count
            ),
            "bounded_iteration_limit_observed": True,
            "explicit_stop_observed": True,
            "explicit_stop_iteration_count": (
                stop_record.completed_iteration_count
            ),
            "control_returned_to_caller": True,
            "exactly_one_state_write_per_iteration": True,
            "exactly_one_log_write_per_iteration": True,
            "current_state_pointer_present": True,
            "blocked_readiness_prevents_run": True,
            "unbounded_run_fails_closed": True,
            "oversized_first_run_fails_closed": True,
            "authority_metadata_override_fails_closed": True,
            "invalid_stop_controller_fails_closed": True,
            "escaped_stop_path_fails_closed": True,
            "root_bound_service_run_hashes_distinct": True,
            "root_bound_ola_027_run_hashes_distinct": True,
            "physical_provenance_preserved": True,
            "deterministic_semantic_replay": True,
            "deterministic_final_state_replay": True,
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
            "[PASS] OLA-027 Oracle Controlled First "
            "Unattended Shadow Run Entrypoint"
        )

        print(result)


if __name__ == "__main__":
    main()
'''


def main() -> None:
    print("========================================")
    print(" OLA-027 TEST CONTRACT CORRECTION")
    print(" ROOT-BOUND PHYSICAL PROVENANCE")
    print("========================================")

    if not MODULE_PATH.exists():
        raise FileNotFoundError(
            "Existing OLA-027 production module is missing"
        )

    existing_module = MODULE_PATH.read_text(
        encoding="utf-8"
    )

    required_production_markers = (
        'SCHEMA_VERSION = "OLA-027"',
        'ENGINE_ID = "OLA-027"',
        "STOP_SIGNAL_FILENAME = "
        '"STOP_ORACLE_SHADOW"',
        "def run_controlled_unattended_shadow_collection(",
        "def _resolve_stop_signal_path(",
    )

    missing_markers = [
        marker
        for marker in required_production_markers
        if marker not in existing_module
    ]

    if missing_markers:
        raise RuntimeError(
            "Existing OLA-027 production module does not "
            "match the corrected production contract: "
            + ", ".join(missing_markers)
        )

    TEST_PATH.write_text(
        textwrap.dedent(TEST).lstrip(),
        encoding="utf-8",
    )

    print(
        "[OK] VERIFIED UNCHANGED PRODUCTION MODULE: "
        f"{MODULE_PATH}"
    )

    print(
        "[OK] FULL REPLACEMENT TEST: "
        f"{TEST_PATH}"
    )

    print()
    print(
        "[DONE] OLA-027 replay test contract corrected"
    )
    print()
    print("Run:")
    print(
        "py test_ola_027_oracle_controlled_"
        "unattended_shadow_run_entrypoint.py"
    )


if __name__ == "__main__":
    main()