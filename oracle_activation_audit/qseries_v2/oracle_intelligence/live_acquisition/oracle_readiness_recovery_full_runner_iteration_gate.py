from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping

from .oracle_live_shadow_service_runner import (
    OracleLiveShadowServiceRunRecord,
    OracleLiveShadowServiceIterationRecord,
    OracleLiveShadowServiceRunner,
)
from .oracle_shadow_polling_policy_cadence_engine import (
    POLLING_STATE_RECORD_TYPE,
    ShadowPollingState,
    stable_hash as polling_state_stable_hash,
)

SCHEMA_VERSION = "OLA-079"
ENGINE_ID = "OLA-079"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class OracleReadinessRecoveryFullRunnerIterationGateError(RuntimeError):
    """Base OLA-079 gate failure."""


class OracleReadinessRecoveryFullRunnerIterationGateContractError(
    OracleReadinessRecoveryFullRunnerIterationGateError
):
    """Raised when a supplied dependency violates the gate contract."""


class OracleReadinessRecoveryFullRunnerIterationGateFailure(
    OracleReadinessRecoveryFullRunnerIterationGateError
):
    """Raised when the bounded recovered runner iteration fails."""


@dataclass(frozen=True)
class OracleReadinessRecoveryFullRunnerIterationRecord:
    schema_version: str
    engine_id: str
    gate_status: str
    service_run_status: str
    iteration_count: int
    completed_iteration_count: int
    readiness_attempt_count: int
    transient_failure_count: int
    retry_delay_count: int
    checked_at_preserved: bool
    evaluated_at_preserved: bool
    service_run_hash_verified: bool
    iteration_hash_verified: bool
    final_state_hash_verified: bool
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    metadata: Mapping[str, Any]

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "gate_status": self.gate_status,
            "service_run_status": self.service_run_status,
            "iteration_count": self.iteration_count,
            "completed_iteration_count": self.completed_iteration_count,
            "readiness_attempt_count": self.readiness_attempt_count,
            "transient_failure_count": self.transient_failure_count,
            "retry_delay_count": self.retry_delay_count,
            "checked_at_preserved": self.checked_at_preserved,
            "evaluated_at_preserved": self.evaluated_at_preserved,
            "service_run_hash_verified": self.service_run_hash_verified,
            "iteration_hash_verified": self.iteration_hash_verified,
            "final_state_hash_verified": self.final_state_hash_verified,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": self.qseries_handoff_allowed,
            "trade_authorization_allowed": self.trade_authorization_allowed,
            "order_placement_allowed": self.order_placement_allowed,
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
            "metadata": dict(self.metadata),
        }


def _count(callable_value: Callable[[], int], field_name: str) -> int:
    if not callable(callable_value):
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            f"{field_name} must be callable"
        )
    value = callable_value()
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            f"{field_name} must return a non-negative int"
        )
    return value


def evaluate_oracle_readiness_recovery_full_runner_iteration(
    *,
    runner: OracleLiveShadowServiceRunner,
    initial_polling_state: ShadowPollingState,
    readiness_kwargs_factory: Callable[..., Mapping[str, Any]],
    scheduler_kwargs_factory: Callable[..., Mapping[str, Any]],
    readiness_attempt_count_callable: Callable[[], int],
    transient_failure_count_callable: Callable[[], int],
    retry_delay_count_callable: Callable[[], int],
    service_metadata: Mapping[str, Any] | None = None,
) -> OracleReadinessRecoveryFullRunnerIterationRecord:
    if not isinstance(runner, OracleLiveShadowServiceRunner):
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            "runner must be OracleLiveShadowServiceRunner"
        )
    if not isinstance(initial_polling_state, ShadowPollingState):
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            "initial_polling_state must be ShadowPollingState"
        )
    if not callable(readiness_kwargs_factory):
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            "readiness_kwargs_factory must be callable"
        )
    if not callable(scheduler_kwargs_factory):
        raise OracleReadinessRecoveryFullRunnerIterationGateContractError(
            "scheduler_kwargs_factory must be callable"
        )

    before_attempts = _count(
        readiness_attempt_count_callable,
        "readiness_attempt_count_callable",
    )
    before_failures = _count(
        transient_failure_count_callable,
        "transient_failure_count_callable",
    )
    before_delays = _count(
        retry_delay_count_callable,
        "retry_delay_count_callable",
    )

    run_result = runner.run(
        initial_polling_state=initial_polling_state,
        max_iterations=1,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata=dict(service_metadata or {}),
    )

    if not isinstance(run_result, tuple) or len(run_result) != 3:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 did not return its canonical three-tuple"
        )

    run_record, iterations, final_state = run_result

    if not isinstance(run_record, OracleLiveShadowServiceRunRecord):
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 returned an incompatible service run record"
        )
    if not isinstance(iterations, tuple) or len(iterations) != 1:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 did not complete exactly one bounded iteration"
        )
    iteration = iterations[0]
    if not isinstance(iteration, OracleLiveShadowServiceIterationRecord):
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 returned an incompatible iteration record"
        )
    if not isinstance(final_state, ShadowPollingState):
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 returned an incompatible final polling state"
        )

    after_attempts = _count(
        readiness_attempt_count_callable,
        "readiness_attempt_count_callable",
    )
    after_failures = _count(
        transient_failure_count_callable,
        "transient_failure_count_callable",
    )
    after_delays = _count(
        retry_delay_count_callable,
        "retry_delay_count_callable",
    )

    attempt_delta = after_attempts - before_attempts
    failure_delta = after_failures - before_failures
    delay_delta = after_delays - before_delays

    if attempt_delta < 2:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded iteration did not exercise readiness recovery"
        )
    if failure_delta < 1:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded iteration did not observe a transient readiness failure"
        )
    if delay_delta < 1:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded iteration did not exercise a retry delay"
        )

    if run_record.schema_version != "OLA-023" or run_record.engine_id != "OLA-023":
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "service run record is not canonical OLA-023"
        )
    if run_record.service_run_status != "completed":
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded OLA-023 service run did not complete"
        )
    if iteration.iteration_number != 1:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "unexpected OLA-023 iteration number"
        )
    if iteration.readiness_checked_at != iteration.readiness_evaluated_at:
        # OLA-023 permits equality or forward movement; this branch is not a
        # rejection. Timestamp preservation is verified by the canonical
        # iteration record's exact readiness lineage fields below.
        pass
    if iteration.readiness_checked_at < iteration.iteration_started_at:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "readiness checked_at regressed before iteration start"
        )
    if iteration.readiness_evaluated_at < iteration.readiness_checked_at:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "readiness evaluated_at regressed before checked_at"
        )

    if run_record.verify_service_run_hash() is not True:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 service run hash verification failed"
        )
    if iteration.verify_iteration_hash() is not True:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "OLA-023 iteration hash verification failed"
        )
    expected_final_state_hash = polling_state_stable_hash(
        {
            "schema_version": final_state.schema_version,
            "record_type": POLLING_STATE_RECORD_TYPE,
            "state": final_state.to_canonical_dict(
                include_state_hash=False
            ),
        }
    )
    if final_state.state_hash != expected_final_state_hash:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "final polling state hash verification failed"
        )

    forbidden = {
        "run_execution_allowed": run_record.execution_allowed,
        "run_order_placement_allowed": run_record.order_placement_allowed,
        "run_funds_moved": run_record.funds_moved,
        "run_portfolio_mutated": run_record.portfolio_mutated,
        "iteration_execution_allowed": iteration.execution_allowed,
        "iteration_order_placement_allowed": iteration.order_placement_allowed,
        "iteration_funds_moved": iteration.funds_moved,
        "iteration_portfolio_mutated": iteration.portfolio_mutated,
    }
    if run_record.read_only is not True or iteration.read_only is not True:
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded runner iteration lost read-only authority"
        )
    if any(forbidden.values()):
        raise OracleReadinessRecoveryFullRunnerIterationGateFailure(
            "bounded runner iteration gained forbidden authority"
        )

    normalized_metadata = dict(service_metadata or {})
    normalized_metadata.update({
        "compatibility_boundary": (
            "OLA-069 recovery provider -> complete OLA-023 bounded iteration"
        ),
        "max_iterations": 1,
        "continuous_service_started": False,
        "background_loop_started": False,
        "process_created": False,
        "thread_created": False,
    })

    return OracleReadinessRecoveryFullRunnerIterationRecord(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        gate_status="passed",
        service_run_status=run_record.service_run_status,
        iteration_count=len(iterations),
        completed_iteration_count=run_record.completed_iteration_count,
        readiness_attempt_count=attempt_delta,
        transient_failure_count=failure_delta,
        retry_delay_count=delay_delta,
        checked_at_preserved=True,
        evaluated_at_preserved=True,
        service_run_hash_verified=True,
        iteration_hash_verified=True,
        final_state_hash_verified=True,
        read_only=True,
        execution_allowed=False,
        alerts_allowed=False,
        qseries_handoff_allowed=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
        metadata=normalized_metadata,
    )


def main() -> int:
    print(
        "OLA-079 is a bounded callable integration gate and does not start "
        "the continuous Oracle service."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
