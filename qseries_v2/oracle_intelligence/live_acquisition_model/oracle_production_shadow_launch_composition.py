"""
OLA-029 Oracle Production Shadow Launch Composition.

Production composition boundary for Oracle's first bounded unattended
live-shadow collection.

Launch chain:

OLA-028 durable launch-readiness artifact
    ->
OLA-026 verified launch decision
    ->
OLA-023 actual service runner
    ->
OLA-025 production evidence binding
    ->
OLA-024 production filesystem writer
    ->
OLA-027 bounded unattended entrypoint

OLA-029 does not recreate or infer launch authorization.

It loads the persisted OLA-026 record through OLA-028 and fails closed
unless all production component identities and runtime roots match.

Oracle remains permanently read-only.
No alerts.
No Q Series intake.
No canonical handoff publication.
No execution capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowServiceRunner,
)

from .oracle_controlled_unattended_shadow_run_entrypoint import (
    OracleControlledUnattendedShadowRunRecord,
    run_controlled_unattended_shadow_collection,
)

from .oracle_launch_readiness_artifact_store import (
    OracleLaunchReadinessArtifactStore,
)

from .production_evidence_service_runner_binding import (
    OracleProductionEvidenceServiceRunnerBinding,
)

from .production_runtime_evidence_writer_bindings import (
    stable_hash,
)


SCHEMA_VERSION = "OLA-029"
ENGINE_ID = "OLA-029"


class OracleProductionShadowLaunchCompositionError(
    ValueError
):
    pass


class OracleProductionShadowLaunchCompositionBlocked(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleProductionShadowLaunchCompositionRecord:
    schema_version: str
    engine_id: str
    composition_status: str
    launch_invoked: bool
    readiness_store_engine_id: str
    readiness_schema_version: str
    readiness_hash: str
    launch_ready: bool
    runner_engine_id: str
    production_binding_engine_id: str
    production_writer_engine_id: str
    entrypoint_engine_id: str
    runtime_root: str
    stop_signal_path: str
    configured_max_iterations: int
    completed_iteration_count: int
    controlled_run_status: str
    service_run_status: str
    state_write_count: int
    log_write_count: int
    runtime_root_identity_match: bool
    exact_runner_stop_callable_bound: bool
    readiness_artifact_loaded: bool
    readiness_hash_verified: bool
    bounded_entrypoint_invoked: bool
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
    controlled_run_hash: str
    composition_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool

    def to_dict(
        self,
        *,
        include_composition_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "composition_status": self.composition_status,
            "launch_invoked": self.launch_invoked,
            "readiness_store_engine_id": (
                self.readiness_store_engine_id
            ),
            "readiness_schema_version": (
                self.readiness_schema_version
            ),
            "readiness_hash": self.readiness_hash,
            "launch_ready": self.launch_ready,
            "runner_engine_id": self.runner_engine_id,
            "production_binding_engine_id": (
                self.production_binding_engine_id
            ),
            "production_writer_engine_id": (
                self.production_writer_engine_id
            ),
            "entrypoint_engine_id": (
                self.entrypoint_engine_id
            ),
            "runtime_root": self.runtime_root,
            "stop_signal_path": self.stop_signal_path,
            "configured_max_iterations": (
                self.configured_max_iterations
            ),
            "completed_iteration_count": (
                self.completed_iteration_count
            ),
            "controlled_run_status": (
                self.controlled_run_status
            ),
            "service_run_status": self.service_run_status,
            "state_write_count": self.state_write_count,
            "log_write_count": self.log_write_count,
            "runtime_root_identity_match": (
                self.runtime_root_identity_match
            ),
            "exact_runner_stop_callable_bound": (
                self.exact_runner_stop_callable_bound
            ),
            "readiness_artifact_loaded": (
                self.readiness_artifact_loaded
            ),
            "readiness_hash_verified": (
                self.readiness_hash_verified
            ),
            "bounded_entrypoint_invoked": (
                self.bounded_entrypoint_invoked
            ),
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
            "controlled_run_hash": self.controlled_run_hash,
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
        }

        if include_composition_hash:
            result["composition_hash"] = (
                self.composition_hash
            )

        return result

    def to_canonical_dict(
        self,
        *,
        include_composition_hash: bool = True,
    ) -> dict[str, Any]:
        return self.to_dict(
            include_composition_hash=(
                include_composition_hash
            )
        )

    def verify_composition_hash(self) -> bool:
        return self.composition_hash == stable_hash(
            self.to_dict(
                include_composition_hash=False
            )
        )


def _validate_runtime_root(
    runtime_root: str | Path,
) -> Path:
    root = Path(
        runtime_root
    )

    if not root.is_absolute():
        raise OracleProductionShadowLaunchCompositionError(
            "runtime_root must be absolute"
        )

    return root.resolve(
        strict=False
    )


def _validate_composition_components(
    *,
    runtime_root: Path,
    readiness_store: OracleLaunchReadinessArtifactStore,
    runner: OracleLiveShadowServiceRunner,
    production_binding: (
        OracleProductionEvidenceServiceRunnerBinding
    ),
    stop_controller: Any,
) -> Path:
    if not isinstance(
        readiness_store,
        OracleLaunchReadinessArtifactStore,
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "readiness_store must be OLA-028"
        )

    if readiness_store.engine_id != "OLA-028":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "readiness store engine must be OLA-028"
        )

    if (
        readiness_store.runtime_root
        != runtime_root
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-028 runtime root does not match "
            "OLA-029 runtime root"
        )

    if not isinstance(
        runner,
        OracleLiveShadowServiceRunner,
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "runner must be OLA-023"
        )

    if runner.engine_id != "OLA-023":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "runner engine must be OLA-023"
        )

    if not isinstance(
        production_binding,
        OracleProductionEvidenceServiceRunnerBinding,
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "production_binding must be OLA-025"
        )

    if production_binding.engine_id != "OLA-025":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "production binding engine must be OLA-025"
        )

    production_writer = (
        production_binding.production_writer
    )

    if production_writer.engine_id != "OLA-024":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "production writer engine must be OLA-024"
        )

    if (
        production_writer.runtime_root
        != runtime_root
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-024 runtime root does not match "
            "OLA-029 runtime root"
        )

    if not callable(
        stop_controller
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "stop_controller must be callable"
        )

    if not hasattr(
        stop_controller,
        "stop_signal_path",
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "stop_controller must expose stop_signal_path"
        )

    if not hasattr(
        stop_controller,
        "stop_observed",
    ):
        raise OracleProductionShadowLaunchCompositionError(
            "stop_controller must expose stop_observed"
        )

    stop_signal_path = Path(
        stop_controller.stop_signal_path
    )

    if not stop_signal_path.is_absolute():
        raise OracleProductionShadowLaunchCompositionBlocked(
            "stop signal path must be absolute"
        )

    stop_signal_path = stop_signal_path.resolve(
        strict=False
    )

    expected_stop_signal_path = (
        runtime_root
        / "state"
        / "STOP_ORACLE_SHADOW"
    )

    if (
        stop_signal_path
        != expected_stop_signal_path
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "stop signal path is not confined to "
            "runtime/state/STOP_ORACLE_SHADOW"
        )

    if (
        runner._stop_requested_callable
        is not stop_controller
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-023 runner is not bound to the exact "
            "validated stop-controller callable"
        )

    return stop_signal_path


def run_oracle_production_shadow_launch(
    *,
    runtime_root: str | Path,
    readiness_store: OracleLaunchReadinessArtifactStore,
    runner: OracleLiveShadowServiceRunner,
    production_binding: (
        OracleProductionEvidenceServiceRunnerBinding
    ),
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
) -> OracleProductionShadowLaunchCompositionRecord:
    """
    Load persisted launch readiness and invoke OLA-027.

    OLA-029 never constructs a synthetic launch-readiness decision.
    """
    resolved_runtime_root = _validate_runtime_root(
        runtime_root
    )

    stop_signal_path = (
        _validate_composition_components(
            runtime_root=resolved_runtime_root,
            readiness_store=readiness_store,
            runner=runner,
            production_binding=production_binding,
            stop_controller=stop_controller,
        )
    )

    readiness_record = (
        readiness_store.load_current()
    )

    if readiness_record.schema_version != "OLA-026":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness schema must be OLA-026"
        )

    if readiness_record.engine_id != "OLA-026":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness engine must be OLA-026"
        )

    if readiness_record.readiness_status != "ready":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness status is not ready"
        )

    if readiness_record.launch_ready is not True:
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted launch_ready is not true"
        )

    if (
        readiness_record.verify_readiness_hash()
        is not True
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness hash verification failed"
        )

    if readiness_record.read_only is not True:
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness violates Oracle "
            "read-only authority"
        )

    forbidden_readiness_authority = (
        readiness_record.alerts_allowed,
        readiness_record.qseries_intake_allowed,
        readiness_record.canonical_handoff_published,
        readiness_record.execution_allowed,
        readiness_record.execution_adapter_resolved,
        readiness_record.execution_adapter_invoked,
        readiness_record.trade_authorization_allowed,
        readiness_record.order_placement_allowed,
        readiness_record.funds_moved,
        readiness_record.portfolio_mutated,
    )

    if any(
        value is not False
        for value in forbidden_readiness_authority
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "persisted readiness contains forbidden authority"
        )

    metadata = {
        "production_composition": SCHEMA_VERSION,
        "readiness_store_engine_id": "OLA-028",
        "readiness_hash": (
            readiness_record.readiness_hash
        ),
        "runtime_root": (
            resolved_runtime_root.as_posix()
        ),
        "controlled_first_corpus_run": True,
        "unbounded_daemon": False,
    }

    if service_metadata is not None:
        if not isinstance(
            service_metadata,
            Mapping,
        ):
            raise OracleProductionShadowLaunchCompositionError(
                "service_metadata must be a mapping"
            )

        forbidden_keys = {
            "alerts_allowed",
            "qseries_intake_allowed",
            "canonical_handoff_published",
            "execution_allowed",
            "execution_adapter_resolved",
            "execution_adapter_invoked",
            "trade_authorization_allowed",
            "order_placement_allowed",
            "funds_moved",
            "portfolio_mutated",
        }

        if (
            forbidden_keys
            & set(service_metadata)
        ):
            raise OracleProductionShadowLaunchCompositionBlocked(
                "service_metadata may not override "
                "Oracle authority restrictions"
            )

        for key, value in service_metadata.items():
            metadata[str(key)] = value

    controlled_run_record = (
        run_controlled_unattended_shadow_collection(
            launch_readiness_record=readiness_record,
            runner=runner,
            production_binding=production_binding,
            runtime_root=resolved_runtime_root,
            stop_controller=stop_controller,
            initial_polling_state=initial_polling_state,
            readiness_kwargs_factory=(
                readiness_kwargs_factory
            ),
            scheduler_kwargs_factory=(
                scheduler_kwargs_factory
            ),
            max_iterations=max_iterations,
            service_metadata=metadata,
        )
    )

    if not isinstance(
        controlled_run_record,
        OracleControlledUnattendedShadowRunRecord,
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-027 did not return its canonical run record"
        )

    if controlled_run_record.schema_version != "OLA-027":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "controlled run schema must be OLA-027"
        )

    if controlled_run_record.engine_id != "OLA-027":
        raise OracleProductionShadowLaunchCompositionBlocked(
            "controlled run engine must be OLA-027"
        )

    if (
        controlled_run_record.verify_run_hash()
        is not True
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-027 run hash verification failed"
        )

    if (
        controlled_run_record.launch_readiness_hash
        != readiness_record.readiness_hash
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-027 readiness lineage does not match "
            "the persisted OLA-028 artifact"
        )

    if (
        controlled_run_record.runtime_root
        != resolved_runtime_root.as_posix()
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-027 runtime root does not match "
            "OLA-029 composition root"
        )

    if (
        controlled_run_record.stop_signal_path
        != stop_signal_path.as_posix()
    ):
        raise OracleProductionShadowLaunchCompositionBlocked(
            "OLA-027 stop path does not match "
            "OLA-029 composition stop path"
        )

    completed_iteration_count = (
        controlled_run_record.completed_iteration_count
    )

    state_write_count = (
        controlled_run_record.state_write_count
    )

    log_write_count = (
        controlled_run_record.log_write_count
    )

    exactly_one_state_write_per_iteration = (
        state_write_count
        == completed_iteration_count
        and controlled_run_record
        .exactly_one_state_write_per_iteration
        is True
    )

    exactly_one_log_write_per_iteration = (
        log_write_count
        == completed_iteration_count
        and controlled_run_record
        .exactly_one_log_write_per_iteration
        is True
    )

    current_state_pointer = (
        resolved_runtime_root
        / "state"
        / "current.json"
    )

    current_state_pointer_present = (
        current_state_pointer.is_file()
        and controlled_run_record
        .current_state_pointer_present
        is True
    )

    authority_valid = (
        controlled_run_record.read_only is True
        and controlled_run_record.alerts_allowed is False
        and (
            controlled_run_record.qseries_intake_allowed
            is False
        )
        and (
            controlled_run_record.canonical_handoff_published
            is False
        )
        and (
            controlled_run_record.execution_allowed
            is False
        )
        and (
            controlled_run_record.execution_adapter_resolved
            is False
        )
        and (
            controlled_run_record.execution_adapter_invoked
            is False
        )
        and (
            controlled_run_record.trade_authorization_allowed
            is False
        )
        and (
            controlled_run_record.order_placement_allowed
            is False
        )
        and controlled_run_record.funds_moved is False
        and (
            controlled_run_record.portfolio_mutated
            is False
        )
    )

    composition_valid = (
        controlled_run_record
        .controlled_unattended_run_started
        is True
        and controlled_run_record
        .controlled_unattended_run_completed
        is True
        and controlled_run_record.launch_ready_at_entry
        is True
        and controlled_run_record.runner_engine_id
        == "OLA-023"
        and controlled_run_record
        .production_binding_engine_id
        == "OLA-025"
        and controlled_run_record
        .production_writer_engine_id
        == "OLA-024"
        and exactly_one_state_write_per_iteration
        and exactly_one_log_write_per_iteration
        and current_state_pointer_present
        and authority_valid
    )

    if not composition_valid:
        raise OracleProductionShadowLaunchCompositionBlocked(
            "post-launch production composition "
            "invariants failed"
        )

    reason_codes = (
        "persisted_launch_readiness_loaded",
        "persisted_readiness_hash_verified",
        "production_runtime_identity_chain_valid",
        "bounded_ola027_entrypoint_invoked",
        "control_returned_to_production_composition",
    )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "composition_status": "completed",
        "launch_invoked": True,
        "readiness_store_engine_id": "OLA-028",
        "readiness_schema_version": "OLA-026",
        "readiness_hash": (
            readiness_record.readiness_hash
        ),
        "launch_ready": True,
        "runner_engine_id": "OLA-023",
        "production_binding_engine_id": "OLA-025",
        "production_writer_engine_id": "OLA-024",
        "entrypoint_engine_id": "OLA-027",
        "runtime_root": (
            resolved_runtime_root.as_posix()
        ),
        "stop_signal_path": (
            stop_signal_path.as_posix()
        ),
        "configured_max_iterations": max_iterations,
        "completed_iteration_count": (
            completed_iteration_count
        ),
        "controlled_run_status": (
            controlled_run_record.run_status
        ),
        "service_run_status": (
            controlled_run_record.service_run_status
        ),
        "state_write_count": state_write_count,
        "log_write_count": log_write_count,
        "runtime_root_identity_match": True,
        "exact_runner_stop_callable_bound": True,
        "readiness_artifact_loaded": True,
        "readiness_hash_verified": True,
        "bounded_entrypoint_invoked": True,
        "exactly_one_state_write_per_iteration": (
            exactly_one_state_write_per_iteration
        ),
        "exactly_one_log_write_per_iteration": (
            exactly_one_log_write_per_iteration
        ),
        "current_state_pointer_present": (
            current_state_pointer_present
        ),
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
        "controlled_run_hash": (
            controlled_run_record.run_hash
        ),
        "immutable": True,
        "replayable": True,
        "auditable": True,
        "explainable": True,
    }

    return OracleProductionShadowLaunchCompositionRecord(
        **record_without_hash,
        composition_hash=stable_hash(
            {
                **record_without_hash,
                "reason_codes": list(
                    reason_codes
                ),
            }
        ),
    )
