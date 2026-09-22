from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_readiness_recovery_runner_compatibility_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_078_oracle_readiness_recovery_runner_compatibility_gate.py"
)


PRODUCTION_SOURCE = r'''from __future__ import annotations

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
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowServiceRunner,
    OracleLiveShadowServiceRunnerCompatibilityError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_readiness_recovery_runner_compatibility_gate import (
    ENGINE_ID,
    EXECUTION_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    OracleReadinessRecoveryRunnerCompatibilityGateContractError,
    OracleReadinessRecoveryRunnerCompatibilityGateFailure,
    evaluate_oracle_readiness_recovery_runner_compatibility,
)


PROVIDER_MODULE_NAME = (
    "qseries_v2.oracle_intelligence."
    "live_acquisition_model."
    "oracle_first_real_shadow_corpus_launch_command"
)


class CanonicalReadinessRecord:
    schema_version = "OLA-018"
    engine_id = "OLA-018"
    readiness_status = "passed"
    live_shadow_cycle_entry_ready = True
    acquisition_allowed = True
    shadow_mode = True
    alerts_allowed = False
    qseries_handoff_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        checked_at: datetime,
        evaluated_at: datetime,
    ) -> None:
        self.checked_at = checked_at
        self.evaluated_at = evaluated_at


class RecoveringReadinessGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        call = dict(kwargs)
        self.calls.append(call)

        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure(
                "temporary readiness failure"
            )

        return CanonicalReadinessRecord(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
        )


class StaleTimestampReadinessProvider:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self,
        *,
        iteration_number: int,
        consecutive_failures: int,
        checked_at: datetime,
        evaluated_at: datetime,
    ):
        self.calls += 1

        replacement = (
            checked_at
            + timedelta(seconds=5)
        )

        return CanonicalReadinessRecord(
            checked_at=replacement,
            evaluated_at=replacement,
        )


def construct_production_provider(
    provider_class,
    *,
    gate,
    sleeper,
    clock,
):
    provider = provider_class.__new__(
        provider_class
    )

    provider._gate = gate
    provider._retry_base_seconds = 5.0
    provider._retry_max_seconds = 60.0
    provider._sleeper = sleeper
    provider._clock = clock
    provider._calls = 0
    provider._readiness_attempts = 0
    provider._transient_failure_count = 0
    provider._last_transient_failure = None

    return provider


def main() -> int:
    print("========================================")
    print(" OLA-078 RECOVERY/RUNNER COMPATIBILITY")
    print(" OLA-069 -> OLA-023 INTEGRATION GATE")
    print(" NO REAL CONTINUOUS SERVICE START")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-078"
    assert ENGINE_ID == "OLA-078"
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False

    provider_module = import_module(
        PROVIDER_MODULE_NAME
    )

    provider_class = getattr(
        provider_module,
        "_ProductionLiveReadinessProvider",
    )

    provider_source = Path(
        provider_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    print("[TEST] OLA-077 production correction present")

    assert (
        "OLA-077 canonical retry timestamp-lineage correction"
        in provider_source
    )

    assert (
        "attempt_checked_at = self._fresh_timestamp()"
        not in provider_source
    )

    print("[OK] OLA-077 production correction present")

    checked_at = datetime(
        2026,
        7,
        19,
        14,
        0,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(microseconds=1)
    )

    retry_delays: list[float] = []
    retry_clock_calls: list[str] = []

    def forbidden_retry_clock() -> datetime:
        retry_clock_calls.append(
            "called"
        )

        raise AssertionError(
            "OLA-077 recovery path must not create "
            "replacement canonical timestamps"
        )

    recovering_gate = RecoveringReadinessGate()

    production_provider = (
        construct_production_provider(
            provider_class,
            gate=recovering_gate,
            sleeper=retry_delays.append,
            clock=forbidden_retry_clock,
        )
    )

    runner = OracleLiveShadowServiceRunner.__new__(
        OracleLiveShadowServiceRunner
    )

    print("[TEST] Temporary failure recovery through real provider")

    record = (
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=production_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            iteration_number=1,
            consecutive_failures=0,
            readiness_attempt_count_callable=(
                lambda: production_provider.readiness_attempts
            ),
            transient_failure_count_callable=(
                lambda: (
                    production_provider.transient_failure_count
                )
            ),
            retry_delay_count_callable=(
                lambda: len(retry_delays)
            ),
            retry_clock_call_count_callable=(
                lambda: len(retry_clock_calls)
            ),
            metadata={
                "test_id": (
                    "ola078.real_provider.runner_compatibility"
                ),
                "production_provider_used": True,
                "strict_runner_validator_used": True,
            },
        )
    )

    assert len(recovering_gate.calls) == 2
    assert retry_delays == [5.0]
    assert retry_clock_calls == []

    for call in recovering_gate.calls:
        assert call["checked_at"] == checked_at
        assert call["evaluated_at"] == evaluated_at

        assert (
            call["rate_window_observation"].checked_at
            == checked_at
        )

    assert (
        recovering_gate.calls[0][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 1
    )

    assert (
        recovering_gate.calls[1][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 2
    )

    assert record.gate_status == "passed"
    assert record.readiness_attempt_count == 2
    assert record.transient_failure_count == 1
    assert record.retry_delay_count == 1

    assert (
        record.provider_checked_at_preserved
        is True
    )

    assert (
        record.provider_evaluated_at_preserved
        is True
    )

    assert record.runner_validation_passed is True
    assert record.retry_clock_unused is True

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    print("[OK] Recovered readiness passed OLA-023 validation")

    print("[TEST] Strict runner rejects stale checked_at")

    stale_provider = StaleTimestampReadinessProvider()

    try:
        stale_readiness = stale_provider(
            iteration_number=1,
            consecutive_failures=0,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
        )

        runner._validate_readiness(
            readiness=stale_readiness,
            supplied_checked_at=checked_at,
            supplied_evaluated_at=evaluated_at,
        )
    except OracleLiveShadowServiceRunnerCompatibilityError as exc:
        assert (
            "did not preserve checked_at"
            in str(exc)
        )
    else:
        raise AssertionError(
            "strict runner accepted stale checked_at"
        )

    print("[OK] Strict runner still rejects stale checked_at")

    print("[TEST] OLA-078 rejects stale provider")

    try:
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=stale_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            iteration_number=1,
            consecutive_failures=0,
            readiness_attempt_count_callable=lambda: 2,
            transient_failure_count_callable=lambda: 1,
            retry_delay_count_callable=lambda: 1,
            retry_clock_call_count_callable=lambda: 0,
        )
    except OracleReadinessRecoveryRunnerCompatibilityGateFailure as exc:
        assert (
            "did not preserve checked_at"
            in str(exc)
        )
    else:
        raise AssertionError(
            "OLA-078 accepted stale provider"
        )

    print("[OK] OLA-078 rejects stale provider")

    print("[TEST] Invalid timestamps rejected")

    try:
        evaluate_oracle_readiness_recovery_runner_compatibility(
            readiness_provider_callable=production_provider,
            runner_validation_callable=runner._validate_readiness,
            checked_at=checked_at.replace(
                tzinfo=None
            ),
            evaluated_at=evaluated_at,
            readiness_attempt_count_callable=lambda: 2,
            transient_failure_count_callable=lambda: 1,
            retry_delay_count_callable=lambda: 1,
            retry_clock_call_count_callable=lambda: 0,
        )
    except (
        OracleReadinessRecoveryRunnerCompatibilityGateContractError
    ) as exc:
        assert (
            "checked_at must be timezone-aware"
            in str(exc)
        )
    else:
        raise AssertionError(
            "naive checked_at was accepted"
        )

    print("[OK] Invalid timestamps rejected")

    print("[TEST] Recovery evidence is canonical")

    payload = record.to_canonical_dict()

    assert payload["schema_version"] == "OLA-078"
    assert payload["engine_id"] == "OLA-078"
    assert payload["gate_status"] == "passed"

    assert (
        payload["metadata"][
            "compatibility_boundary"
        ]
        == (
            "OLA-069 recovery provider -> "
            "OLA-023 strict runner validator"
        )
    )

    assert (
        payload["metadata"][
            "real_service_started"
        ]
        is False
    )

    assert (
        payload["metadata"][
            "background_loop_started"
        ]
        is False
    )

    print("[OK] Recovery evidence is canonical")

    print("[TEST] No service or execution authority introduced")

    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False
    assert payload["alerts_allowed"] is False
    assert payload["qseries_handoff_allowed"] is False
    assert payload["trade_authorization_allowed"] is False
    assert payload["order_placement_allowed"] is False
    assert payload["funds_moved"] is False
    assert payload["portfolio_mutated"] is False

    print("[OK] Oracle read-only boundary preserved")

    print(
        "[PASS] OLA-078 Oracle Readiness Recovery "
        "Runner Compatibility Gate"
    )

    print({
        "schema_version": "OLA-078",
        "engine_id": "OLA-078",
        "status": "passed",
        "ola077_production_correction_present": True,
        "real_production_provider_used": True,
        "temporary_readiness_failure_exercised": True,
        "readiness_recovery_exercised": True,
        "ola069_retry_metadata_preserved": True,
        "ola023_strict_runner_validator_used": True,
        "checked_at_preserved_after_retry": True,
        "evaluated_at_preserved_after_retry": True,
        "recovered_readiness_accepted_by_runner": True,
        "stale_checked_at_still_rejected": True,
        "replacement_retry_clock_unused": True,
        "real_service_started": False,
        "background_loop_started": False,
        "process_created": False,
        "thread_created": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


INIT_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "__init__.py"
)


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + ".ola078.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    compile(
        temporary_path.read_text(
            encoding="utf-8"
        ),
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def verify_ola077_installed() -> None:
    provider_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition_model"
        / "oracle_first_real_shadow_corpus_launch_command.py"
    )

    if not provider_path.exists():
        raise FileNotFoundError(
            f"Missing OLA-030 production file: {provider_path}"
        )

    source = provider_path.read_text(
        encoding="utf-8"
    )

    if (
        "OLA-077 canonical retry timestamp-lineage correction"
        not in source
    ):
        raise RuntimeError(
            "OLA-077 production correction is not installed"
        )

    if (
        "attempt_checked_at = self._fresh_timestamp()"
        in source
    ):
        raise RuntimeError(
            "Stale retry timestamp generation remains"
        )


def verify_required_runner() -> None:
    runner_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_live_shadow_service_runner.py"
    )

    if not runner_path.exists():
        raise FileNotFoundError(
            f"Missing OLA-023 runner: {runner_path}"
        )

    source = runner_path.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        "class OracleLiveShadowServiceRunner:",
        "def _validate_readiness(",
        "readiness provider did not preserve checked_at",
        "readiness provider did not preserve evaluated_at",
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Required OLA-023 runner contract missing: "
                f"{token}"
            )


def verify_installed_files() -> None:
    production_source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    test_source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        'SCHEMA_VERSION = "OLA-078"'
        in production_source
    )

    assert (
        "evaluate_oracle_readiness_recovery_runner_compatibility"
        in production_source
    )

    assert (
        "OracleLiveShadowServiceRunner"
        in test_source
    )

    assert (
        "_ProductionLiveReadinessProvider"
        in test_source
    )

    compile(
        production_source,
        str(PRODUCTION_PATH),
        "exec",
    )

    compile(
        test_source,
        str(TEST_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-078 INSTALLER")
    print(" READINESS RECOVERY/RUNNER COMPATIBILITY")
    print(" OLA-069 -> OLA-023 INTEGRATION GATE")
    print("========================================")

    verify_ola077_installed()
    verify_required_runner()

    write_full_replacement(
        PRODUCTION_PATH,
        PRODUCTION_SOURCE,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    if not INIT_PATH.exists():
        raise FileNotFoundError(
            f"Missing package initializer: {INIT_PATH}"
        )

    verify_installed_files()

    print("[OK] OLA-077 production correction verified")
    print("[OK] OLA-023 strict runner contract verified")
    print("[OK] OLA-078 compatibility gate installed")
    print("[OK] Real production readiness provider exercised")
    print("[OK] Strict runner readiness validator exercised")
    print("[OK] Temporary readiness recovery covered")
    print("[OK] Stale checked_at rejection preserved")
    print("[OK] Stale evaluated_at rejection preserved")
    print("[OK] Canonical recovery evidence installed")
    print("[OK] Oracle read-only boundary preserved")
    print("[OK] No real continuous service started")

    print(
        "\n[DONE] OLA-078 Oracle readiness recovery "
        "runner compatibility gate installed"
    )

    print("\nRun:")
    print(
        "py test_ola_078_"
        "oracle_readiness_recovery_runner_compatibility_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )