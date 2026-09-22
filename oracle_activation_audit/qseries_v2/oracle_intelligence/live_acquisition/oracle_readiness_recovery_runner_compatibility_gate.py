from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "OLA-078"
ENGINE_ID = "OLA-078"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class OracleReadinessRecoveryRunnerCompatibilityGateError(
    RuntimeError
):
    """Base OLA-078 compatibility-gate failure."""


class OracleReadinessRecoveryRunnerCompatibilityGateContractError(
    OracleReadinessRecoveryRunnerCompatibilityGateError
):
    """Raised when a supplied dependency violates the gate contract."""


class OracleReadinessRecoveryRunnerCompatibilityGateFailure(
    OracleReadinessRecoveryRunnerCompatibilityGateError
):
    """Raised when recovered readiness fails runner compatibility."""


@dataclass(frozen=True)
class OracleReadinessRecoveryRunnerCompatibilityRecord:
    schema_version: str
    engine_id: str
    gate_status: str

    checked_at: datetime
    evaluated_at: datetime

    readiness_attempt_count: int
    transient_failure_count: int
    retry_delay_count: int

    provider_checked_at_preserved: bool
    provider_evaluated_at_preserved: bool
    runner_validation_passed: bool
    retry_clock_unused: bool

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
            "checked_at": self.checked_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat(),
            "readiness_attempt_count": (
                self.readiness_attempt_count
            ),
            "transient_failure_count": (
                self.transient_failure_count
            ),
            "retry_delay_count": self.retry_delay_count,
            "provider_checked_at_preserved": (
                self.provider_checked_at_preserved
            ),
            "provider_evaluated_at_preserved": (
                self.provider_evaluated_at_preserved
            ),
            "runner_validation_passed": (
                self.runner_validation_passed
            ),
            "retry_clock_unused": self.retry_clock_unused,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
            "metadata": dict(self.metadata),
        }


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                f"{field_name} must be a datetime"
            )
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                f"{field_name} must be timezone-aware"
            )
        )

    return value


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                f"{field_name} must be a non-negative int"
            )
        )

    return value


def evaluate_oracle_readiness_recovery_runner_compatibility(
    *,
    readiness_provider_callable: Callable[..., Any],
    runner_validation_callable: Callable[..., Any],
    checked_at: datetime,
    evaluated_at: datetime,
    iteration_number: int = 1,
    consecutive_failures: int = 0,
    readiness_attempt_count_callable: (
        Callable[[], int] | None
    ) = None,
    transient_failure_count_callable: (
        Callable[[], int] | None
    ) = None,
    retry_delay_count_callable: (
        Callable[[], int] | None
    ) = None,
    retry_clock_call_count_callable: (
        Callable[[], int] | None
    ) = None,
    metadata: Mapping[str, Any] | None = None,
) -> OracleReadinessRecoveryRunnerCompatibilityRecord:
    if not callable(readiness_provider_callable):
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                "readiness_provider_callable must be callable"
            )
        )

    if not callable(runner_validation_callable):
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                "runner_validation_callable must be callable"
            )
        )

    checked_at = _require_aware_datetime(
        checked_at,
        "checked_at",
    )

    evaluated_at = _require_aware_datetime(
        evaluated_at,
        "evaluated_at",
    )

    if evaluated_at < checked_at:
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                "evaluated_at cannot precede checked_at"
            )
        )

    if (
        isinstance(iteration_number, bool)
        or not isinstance(iteration_number, int)
        or iteration_number <= 0
    ):
        raise (
            OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                "iteration_number must be a positive int"
            )
        )

    consecutive_failures = _require_non_negative_int(
        consecutive_failures,
        "consecutive_failures",
    )

    for callable_value, field_name in (
        (
            readiness_attempt_count_callable,
            "readiness_attempt_count_callable",
        ),
        (
            transient_failure_count_callable,
            "transient_failure_count_callable",
        ),
        (
            retry_delay_count_callable,
            "retry_delay_count_callable",
        ),
        (
            retry_clock_call_count_callable,
            "retry_clock_call_count_callable",
        ),
    ):
        if (
            callable_value is not None
            and not callable(callable_value)
        ):
            raise (
                OracleReadinessRecoveryRunnerCompatibilityGateContractError(
                    f"{field_name} must be callable or None"
                )
            )

    readiness = readiness_provider_callable(
        iteration_number=iteration_number,
        consecutive_failures=consecutive_failures,
        checked_at=checked_at,
        evaluated_at=evaluated_at,
    )

    provider_checked_at = getattr(
        readiness,
        "checked_at",
        None,
    )

    provider_evaluated_at = getattr(
        readiness,
        "evaluated_at",
        None,
    )

    checked_at_preserved = (
        provider_checked_at == checked_at
    )

    evaluated_at_preserved = (
        provider_evaluated_at == evaluated_at
    )

    if not checked_at_preserved:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovered readiness did not preserve checked_at"
        )

    if not evaluated_at_preserved:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovered readiness did not preserve evaluated_at"
        )

    try:
        validated_readiness = runner_validation_callable(
            readiness=readiness,
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
    except Exception as exc:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovered readiness failed strict runner validation: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    if validated_readiness is not readiness:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "runner validation did not preserve readiness identity"
        )

    readiness_read_only = getattr(
        validated_readiness,
        "read_only",
        None,
    )

    readiness_execution_allowed = getattr(
        validated_readiness,
        "execution_allowed",
        None,
    )

    if readiness_read_only is not True:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovered readiness lost read_only invariant"
        )

    if readiness_execution_allowed is not False:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovered readiness gained execution authority"
        )

    readiness_attempt_count = 0

    if readiness_attempt_count_callable is not None:
        readiness_attempt_count = (
            _require_non_negative_int(
                readiness_attempt_count_callable(),
                "readiness_attempt_count",
            )
        )

    transient_failure_count = 0

    if transient_failure_count_callable is not None:
        transient_failure_count = (
            _require_non_negative_int(
                transient_failure_count_callable(),
                "transient_failure_count",
            )
        )

    retry_delay_count = 0

    if retry_delay_count_callable is not None:
        retry_delay_count = (
            _require_non_negative_int(
                retry_delay_count_callable(),
                "retry_delay_count",
            )
        )

    retry_clock_call_count = 0

    if retry_clock_call_count_callable is not None:
        retry_clock_call_count = (
            _require_non_negative_int(
                retry_clock_call_count_callable(),
                "retry_clock_call_count",
            )
        )

    if readiness_attempt_count < 2:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovery gate requires at least two readiness attempts"
        )

    if transient_failure_count < 1:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovery gate requires at least one transient failure"
        )

    if retry_delay_count < 1:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovery gate requires at least one retry delay"
        )

    if retry_clock_call_count != 0:
        raise OracleReadinessRecoveryRunnerCompatibilityGateFailure(
            "recovery path created replacement canonical timestamps"
        )

    normalized_metadata = dict(
        metadata or {}
    )

    normalized_metadata.update({
        "compatibility_boundary": (
            "OLA-069 recovery provider -> "
            "OLA-023 strict runner validator"
        ),
        "iteration_number": iteration_number,
        "scheduler_consecutive_failures": (
            consecutive_failures
        ),
        "real_service_started": False,
        "background_loop_started": False,
        "process_created": False,
        "thread_created": False,
    })

    return OracleReadinessRecoveryRunnerCompatibilityRecord(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        gate_status="passed",
        checked_at=checked_at,
        evaluated_at=evaluated_at,
        readiness_attempt_count=readiness_attempt_count,
        transient_failure_count=transient_failure_count,
        retry_delay_count=retry_delay_count,
        provider_checked_at_preserved=True,
        provider_evaluated_at_preserved=True,
        runner_validation_passed=True,
        retry_clock_unused=True,
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
        "OLA-078 is a callable integration gate and does not "
        "start the Oracle service."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
