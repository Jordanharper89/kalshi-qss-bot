"""
OLA-027 Oracle Controlled First Unattended Shadow Run Entrypoint.

Corrected stop-controller contract boundary.

The first unattended Oracle shadow run must remain bounded.

Stop control is validated by contract:
- callable
- exposes absolute stop_signal_path
- stop path is exactly runtime/state/STOP_ORACLE_SHADOW
- exposes stop_observed
- exact validated stop-controller callable is bound to OLA-023

This permits controlled composition wrappers without weakening path
confinement or stop observability.

Oracle remains read-only.
No execution.
No alerts.
No Q Series intake.
No canonical handoff publication.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowServiceRunner,
)

from .oracle_shadow_launch_readiness_gate import (
    OracleShadowLaunchReadinessRecord,
)

from .production_evidence_service_runner_binding import (
    OracleProductionEvidenceServiceRunnerBinding,
)

from .production_runtime_evidence_writer_bindings import (
    stable_hash,
)


SCHEMA_VERSION = "OLA-027"
ENGINE_ID = "OLA-027"

MIN_CONTROLLED_ITERATIONS = 1
MAX_CONTROLLED_ITERATIONS = 1000

STOP_SIGNAL_FILENAME = "STOP_ORACLE_SHADOW"


class OracleControlledUnattendedShadowRunError(
    ValueError
):
    pass


class OracleControlledUnattendedShadowRunBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleControlledUnattendedShadowRunRecord:
    schema_version: str
    engine_id: str
    run_status: str
    controlled_unattended_run_started: bool
    controlled_unattended_run_completed: bool
    launch_readiness_schema_version: str
    launch_readiness_hash: str
    launch_ready_at_entry: bool
    runner_engine_id: str
    production_binding_engine_id: str
    production_writer_engine_id: str
    runtime_root: str
    stop_signal_path: str
    max_iterations: int
    completed_iteration_count: int
    service_run_status: str
    service_run_id: str
    service_run_hash: str
    final_state_id: str
    final_state_hash: str
    final_consecutive_failures: int
    final_state_suspended: bool
    explicit_stop_observed: bool
    iteration_limit_observed: bool
    state_write_count: int
    log_write_count: int
    exactly_one_state_write_per_iteration: bool
    exactly_one_log_write_per_iteration: bool
    current_state_pointer_present: bool
    read_only: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    canonical_handoff_published: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    reason_codes: tuple[str, ...]
    run_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool

    def to_dict(
        self,
        *,
        include_run_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "run_status": self.run_status,
            "controlled_unattended_run_started": (
                self.controlled_unattended_run_started
            ),
            "controlled_unattended_run_completed": (
                self.controlled_unattended_run_completed
            ),
            "launch_readiness_schema_version": (
                self.launch_readiness_schema_version
            ),
            "launch_readiness_hash": (
                self.launch_readiness_hash
            ),
            "launch_ready_at_entry": (
                self.launch_ready_at_entry
            ),
            "runner_engine_id": self.runner_engine_id,
            "production_binding_engine_id": (
                self.production_binding_engine_id
            ),
            "production_writer_engine_id": (
                self.production_writer_engine_id
            ),
            "runtime_root": self.runtime_root,
            "stop_signal_path": self.stop_signal_path,
            "max_iterations": self.max_iterations,
            "completed_iteration_count": (
                self.completed_iteration_count
            ),
            "service_run_status": self.service_run_status,
            "service_run_id": self.service_run_id,
            "service_run_hash": self.service_run_hash,
            "final_state_id": self.final_state_id,
            "final_state_hash": self.final_state_hash,
            "final_consecutive_failures": (
                self.final_consecutive_failures
            ),
            "final_state_suspended": (
                self.final_state_suspended
            ),
            "explicit_stop_observed": (
                self.explicit_stop_observed
            ),
            "iteration_limit_observed": (
                self.iteration_limit_observed
            ),
            "state_write_count": self.state_write_count,
            "log_write_count": self.log_write_count,
            "exactly_one_state_write_per_iteration": (
                self.exactly_one_state_write_per_iteration
            ),
            "exactly_one_log_write_per_iteration": (
                self.exactly_one_log_write_per_iteration
            ),
            "current_state_pointer_present": (
                self.current_state_pointer_present
            ),
            "read_only": self.read_only,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
            "reason_codes": list(self.reason_codes),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
        }

        if include_run_hash:
            result["run_hash"] = self.run_hash

        return result

    def to_canonical_dict(
        self,
        *,
        include_run_hash: bool = True,
    ) -> dict[str, Any]:
        return self.to_dict(
            include_run_hash=include_run_hash
        )

    def verify_run_hash(self) -> bool:
        return self.run_hash == stable_hash(
            self.to_dict(
                include_run_hash=False
            )
        )


class OracleFilesystemStopController:
    """
    Read-only filesystem stop observer.

    The controller never creates, removes, or mutates the stop file.
    """

    def __init__(
        self,
        *,
        stop_signal_path: str | Path,
    ) -> None:
        raw_path = Path(
            stop_signal_path
        )

        if not raw_path.is_absolute():
            raise OracleControlledUnattendedShadowRunError(
                "stop_signal_path must be absolute"
            )

        self._stop_signal_path = raw_path.resolve(
            strict=False
        )

        self._check_count = 0
        self._stop_observed = False

    @property
    def stop_signal_path(self) -> Path:
        return self._stop_signal_path

    @property
    def check_count(self) -> int:
        return self._check_count

    @property
    def stop_observed(self) -> bool:
        return self._stop_observed

    def __call__(self) -> bool:
        self._check_count += 1

        observed = (
            self._stop_signal_path.exists()
            and self._stop_signal_path.is_file()
        )

        if observed:
            self._stop_observed = True

        return observed


def create_oracle_filesystem_stop_controller(
    *,
    runtime_root: str | Path,
) -> OracleFilesystemStopController:
    root = Path(
        runtime_root
    )

    if not root.is_absolute():
        raise OracleControlledUnattendedShadowRunError(
            "runtime_root must be absolute"
        )

    resolved_root = root.resolve(
        strict=False
    )

    return OracleFilesystemStopController(
        stop_signal_path=(
            resolved_root
            / "state"
            / STOP_SIGNAL_FILENAME
        )
    )


def _validate_launch_readiness(
    readiness: OracleShadowLaunchReadinessRecord,
) -> None:
    if not isinstance(
        readiness,
        OracleShadowLaunchReadinessRecord,
    ):
        raise OracleControlledUnattendedShadowRunError(
            "launch_readiness_record must be an "
            "OracleShadowLaunchReadinessRecord"
        )

    if readiness.schema_version != "OLA-026":
        raise OracleControlledUnattendedShadowRunBlocked(
            "launch readiness schema must be OLA-026"
        )

    if readiness.engine_id != "OLA-026":
        raise OracleControlledUnattendedShadowRunBlocked(
            "launch readiness engine must be OLA-026"
        )

    if readiness.readiness_status != "ready":
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-026 readiness_status is not ready"
        )

    if readiness.launch_ready is not True:
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-026 launch_ready is not true"
        )

    if (
        readiness.unattended_collection_started
        is not False
    ):
        raise OracleControlledUnattendedShadowRunBlocked(
            "launch readiness evidence indicates unattended "
            "collection already started"
        )

    if readiness.verify_readiness_hash() is not True:
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-026 readiness hash is invalid"
        )

    if readiness.read_only is not True:
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-026 read_only invariant is invalid"
        )

    forbidden_values = (
        readiness.alerts_allowed,
        readiness.qseries_intake_allowed,
        readiness.canonical_handoff_published,
        readiness.execution_allowed,
        readiness.execution_adapter_resolved,
        readiness.execution_adapter_invoked,
        readiness.trade_authorization_allowed,
        readiness.order_placement_allowed,
        readiness.funds_moved,
        readiness.portfolio_mutated,
    )

    if any(
        value is not False
        for value in forbidden_values
    ):
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-026 authority restrictions are invalid"
        )


def _validate_iteration_limit(
    max_iterations: Any,
) -> int:
    if (
        isinstance(max_iterations, bool)
        or not isinstance(max_iterations, int)
    ):
        raise OracleControlledUnattendedShadowRunError(
            "max_iterations must be an int"
        )

    if max_iterations < MIN_CONTROLLED_ITERATIONS:
        raise OracleControlledUnattendedShadowRunError(
            "max_iterations must be greater than zero"
        )

    if max_iterations > MAX_CONTROLLED_ITERATIONS:
        raise OracleControlledUnattendedShadowRunBlocked(
            "max_iterations exceeds first controlled "
            "unattended run safety limit"
        )

    return max_iterations


def _resolve_stop_signal_path(
    stop_controller: Any,
) -> Path:
    if not callable(stop_controller):
        raise OracleControlledUnattendedShadowRunError(
            "stop_controller must be callable"
        )

    if not hasattr(
        stop_controller,
        "stop_signal_path",
    ):
        raise OracleControlledUnattendedShadowRunError(
            "stop_controller must expose stop_signal_path"
        )

    stop_signal_path = Path(
        stop_controller.stop_signal_path
    )

    if not stop_signal_path.is_absolute():
        raise OracleControlledUnattendedShadowRunBlocked(
            "stop controller path must be absolute"
        )

    if not hasattr(
        stop_controller,
        "stop_observed",
    ):
        raise OracleControlledUnattendedShadowRunError(
            "stop_controller must expose stop_observed"
        )

    return stop_signal_path.resolve(
        strict=False
    )


def _validate_runtime_boundary(
    *,
    runtime_root: Path,
    production_binding: (
        OracleProductionEvidenceServiceRunnerBinding
    ),
    stop_controller: Any,
) -> Path:
    if not runtime_root.is_absolute():
        raise OracleControlledUnattendedShadowRunError(
            "runtime_root must be absolute"
        )

    if not isinstance(
        production_binding,
        OracleProductionEvidenceServiceRunnerBinding,
    ):
        raise OracleControlledUnattendedShadowRunError(
            "production_binding must be OLA-025"
        )

    production_writer = (
        production_binding.production_writer
    )

    if production_writer.engine_id != "OLA-024":
        raise OracleControlledUnattendedShadowRunBlocked(
            "production writer engine must be OLA-024"
        )

    if (
        production_writer.runtime_root
        != runtime_root
    ):
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-024 runtime root does not match "
            "OLA-027 runtime root"
        )

    stop_signal_path = _resolve_stop_signal_path(
        stop_controller
    )

    expected_stop_path = (
        runtime_root
        / "state"
        / STOP_SIGNAL_FILENAME
    )

    if stop_signal_path != expected_stop_path:
        raise OracleControlledUnattendedShadowRunBlocked(
            "stop controller is not confined to "
            "runtime/state"
        )

    return stop_signal_path


def run_controlled_unattended_shadow_collection(
    *,
    launch_readiness_record: (
        OracleShadowLaunchReadinessRecord
    ),
    runner: OracleLiveShadowServiceRunner,
    production_binding: (
        OracleProductionEvidenceServiceRunnerBinding
    ),
    runtime_root: str | Path,
    stop_controller: Any,
    initial_polling_state: Any,
    readiness_kwargs_factory: Callable[
        ...,
        Mapping[str, Any],
    ],
    scheduler_kwargs_factory: Callable[
        ...,
        Mapping[str, Any],
    ],
    max_iterations: int,
    service_metadata: Mapping[str, Any] | None = None,
) -> OracleControlledUnattendedShadowRunRecord:
    _validate_launch_readiness(
        launch_readiness_record
    )

    if not isinstance(
        runner,
        OracleLiveShadowServiceRunner,
    ):
        raise OracleControlledUnattendedShadowRunError(
            "runner must be an OLA-023 "
            "OracleLiveShadowServiceRunner"
        )

    if runner.engine_id != "OLA-023":
        raise OracleControlledUnattendedShadowRunBlocked(
            "runner engine must be OLA-023"
        )

    if not callable(
        readiness_kwargs_factory
    ):
        raise OracleControlledUnattendedShadowRunError(
            "readiness_kwargs_factory must be callable"
        )

    if not callable(
        scheduler_kwargs_factory
    ):
        raise OracleControlledUnattendedShadowRunError(
            "scheduler_kwargs_factory must be callable"
        )

    bounded_iterations = _validate_iteration_limit(
        max_iterations
    )

    resolved_runtime_root = Path(
        runtime_root
    ).resolve(
        strict=False
    )

    stop_signal_path = _validate_runtime_boundary(
        runtime_root=resolved_runtime_root,
        production_binding=production_binding,
        stop_controller=stop_controller,
    )

    if (
        runner._stop_requested_callable
        is not stop_controller
    ):
        raise OracleControlledUnattendedShadowRunBlocked(
            "OLA-023 runner is not bound to the exact "
            "validated OLA-027 stop-controller callable"
        )

    metadata = {
        "environment": "production",
        "service_mode": "live_shadow",
        "launch_boundary": SCHEMA_VERSION,
        "launch_readiness_schema_version": (
            launch_readiness_record.schema_version
        ),
        "launch_readiness_hash": (
            launch_readiness_record.readiness_hash
        ),
        "controlled_unattended_run": True,
        "bounded_run": True,
        "configured_max_iterations": (
            bounded_iterations
        ),
        "stop_signal_path": (
            stop_signal_path.as_posix()
        ),
        "alerts_allowed": False,
        "qseries_intake_allowed": False,
        "canonical_handoff_published": False,
        "execution_allowed": False,
    }

    if service_metadata is not None:
        if not isinstance(
            service_metadata,
            Mapping,
        ):
            raise OracleControlledUnattendedShadowRunError(
                "service_metadata must be a mapping"
            )

        forbidden_metadata_keys = {
            "alerts_allowed",
            "qseries_intake_allowed",
            "canonical_handoff_published",
            "execution_allowed",
            "trade_authorization_allowed",
            "order_placement_allowed",
        }

        if (
            forbidden_metadata_keys
            & set(service_metadata)
        ):
            raise OracleControlledUnattendedShadowRunBlocked(
                "service_metadata may not override "
                "authority restrictions"
            )

        for key, value in service_metadata.items():
            metadata[str(key)] = value

    (
        service_run_record,
        iteration_records,
        final_state,
    ) = runner.run(
        initial_polling_state=initial_polling_state,
        max_iterations=bounded_iterations,
        readiness_kwargs_factory=(
            readiness_kwargs_factory
        ),
        scheduler_kwargs_factory=(
            scheduler_kwargs_factory
        ),
        service_metadata=metadata,
    )

    iteration_count = (
        service_run_record.iteration_count
    )

    state_write_count = (
        production_binding.state_write_count
    )

    log_write_count = (
        production_binding.log_write_count
    )

    exactly_one_state_write_per_iteration = (
        state_write_count == iteration_count
    )

    exactly_one_log_write_per_iteration = (
        log_write_count == iteration_count
    )

    current_state_pointer = (
        resolved_runtime_root
        / "state"
        / "current.json"
    )

    explicit_stop_observed = (
        service_run_record.stop_requested is True
        and service_run_record.service_run_status
        == "stopped"
        and stop_controller.stop_observed is True
    )

    iteration_limit_observed = (
        service_run_record.service_run_status
        == "completed"
        and service_run_record.stop_requested is False
        and iteration_count == bounded_iterations
    )

    authority_valid = (
        service_run_record.read_only is True
        and service_run_record.alerts_allowed is False
        and (
            service_run_record.qseries_intake_allowed
            is False
        )
        and (
            service_run_record.canonical_handoff_published
            is False
        )
        and service_run_record.execution_allowed is False
        and (
            service_run_record.execution_adapter_resolved
            is False
        )
        and (
            service_run_record.execution_adapter_invoked
            is False
        )
        and (
            service_run_record.trade_authorization_allowed
            is False
        )
        and (
            service_run_record.order_placement_allowed
            is False
        )
        and service_run_record.funds_moved is False
        and service_run_record.portfolio_mutated is False
    )

    successful_boundary = (
        service_run_record.schema_version == "OLA-023"
        and service_run_record.engine_id == "OLA-023"
        and service_run_record.verify_service_run_hash()
        is True
        and len(iteration_records) == iteration_count
        and all(
            iteration.verify_iteration_hash()
            is True
            for iteration in iteration_records
        )
        and final_state.state_hash
        == service_run_record.final_state_hash
        and exactly_one_state_write_per_iteration
        and exactly_one_log_write_per_iteration
        and current_state_pointer.exists()
        and authority_valid
        and (
            explicit_stop_observed
            or iteration_limit_observed
        )
    )

    if not successful_boundary:
        raise OracleControlledUnattendedShadowRunBlocked(
            "controlled unattended shadow run failed "
            "post-run invariant validation"
        )

    reason_codes = (
        (
            "controlled_unattended_shadow_run_stopped",
            "explicit_filesystem_stop_observed",
            "control_returned_to_caller",
        )
        if explicit_stop_observed
        else (
            "controlled_unattended_shadow_run_completed",
            "bounded_iteration_limit_observed",
            "control_returned_to_caller",
        )
    )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "run_status": (
            "stopped"
            if explicit_stop_observed
            else "completed"
        ),
        "controlled_unattended_run_started": True,
        "controlled_unattended_run_completed": True,
        "launch_readiness_schema_version": (
            launch_readiness_record.schema_version
        ),
        "launch_readiness_hash": (
            launch_readiness_record.readiness_hash
        ),
        "launch_ready_at_entry": True,
        "runner_engine_id": "OLA-023",
        "production_binding_engine_id": "OLA-025",
        "production_writer_engine_id": "OLA-024",
        "runtime_root": (
            resolved_runtime_root.as_posix()
        ),
        "stop_signal_path": (
            stop_signal_path.as_posix()
        ),
        "max_iterations": bounded_iterations,
        "completed_iteration_count": iteration_count,
        "service_run_status": (
            service_run_record.service_run_status
        ),
        "service_run_id": (
            service_run_record.service_run_id
        ),
        "service_run_hash": (
            service_run_record.service_run_hash
        ),
        "final_state_id": (
            service_run_record.final_state_id
        ),
        "final_state_hash": (
            service_run_record.final_state_hash
        ),
        "final_consecutive_failures": (
            service_run_record.final_consecutive_failures
        ),
        "final_state_suspended": (
            service_run_record.final_state_suspended
        ),
        "explicit_stop_observed": (
            explicit_stop_observed
        ),
        "iteration_limit_observed": (
            iteration_limit_observed
        ),
        "state_write_count": state_write_count,
        "log_write_count": log_write_count,
        "exactly_one_state_write_per_iteration": (
            exactly_one_state_write_per_iteration
        ),
        "exactly_one_log_write_per_iteration": (
            exactly_one_log_write_per_iteration
        ),
        "current_state_pointer_present": True,
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
        "reason_codes": reason_codes,
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
    }

    return OracleControlledUnattendedShadowRunRecord(
        **record_without_hash,
        run_hash=stable_hash(
            {
                **record_without_hash,
                "reason_codes": list(
                    reason_codes
                ),
            }
        ),
    )
