from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_live_shadow_service_runner.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_023_oracle_live_shadow_service_runner.py"
)


MODULE_CONTENT = r'''
"""
OLA-023
Oracle Live Shadow Service Runner

FULL CANONICAL CLOCK LINEAGE REWRITE

Thin outer operating loop for the separate Oracle live-shadow service.

Architecture:

OLA-022 BOOTSTRAP READY
    |
CALLER-CONTROLLED SERVICE CLOCK
    |
READINESS CHECKED_AT
READINESS EVALUATED_AT
    |
OLA-018 READINESS PROVIDER
    |
SCHEDULER EVALUATED_AT
TICK STARTED_AT
TICK COMPLETED_AT
    |
OLA-021 GOVERNED SCHEDULER TICK
    |
NEXT IMMUTABLE POLLING STATE
    |
RUNTIME STATE / LOG EVIDENCE
    |
CONTROLLED SLEEP
    |
EXPLICIT STOP CHECK
    |
REPEAT

Canonical clock rule:

OLA-023 owns service timestamp sequencing through a caller-supplied clock.

For each iteration:

iteration_started_at
<
readiness_checked_at
<=
readiness_evaluated_at
<=
scheduler_evaluated_at
<=
tick_started_at
<=
tick_completed_at
<=
iteration_completed_at

The readiness provider receives caller-controlled checked_at and
evaluated_at values.

The readiness provider must preserve those exact timestamps.

OLA-023 never repairs time by silently applying max().

Timestamp regression fails closed.

Authority remains outside OLA-023:

- OLA-018 owns readiness evidence creation.
- OLA-019 owns polling cadence and suspension policy.
- OLA-021 owns one governed scheduler tick.
- OLA-017 owns one shadow acquisition cycle.
- OLA-020 owns Oracle/Q Series service isolation.
- OLA-022 owns service bootstrap composition.

OLA-023 owns only:

- loop repetition
- canonical service clock sequencing
- current polling-state carriage
- state evidence writer invocation
- log evidence writer invocation
- controlled sleeping
- explicit stop observation

Permanent rules:

- OLA-022 bootstrap readiness is mandatory.
- One OLA-018 readiness request occurs per iteration.
- One OLA-021 scheduler tick request occurs per iteration.
- OLA-023 never calls OLA-017 directly.
- OLA-023 never calls Kalshi directly.
- OLA-023 never invokes PostgreSQL directly.
- Readiness timestamps are caller controlled.
- Scheduler timestamps are caller controlled.
- Timestamp lineage must be monotonic.
- Readiness provider must preserve supplied timestamps.
- OLA-019 remains authoritative and is never bypassed.
- OLA-021 next polling state becomes current service state.
- Restart evidence is never invented.
- State and log writers are explicit boundaries.
- Sleep is injectable.
- Stop checking is injectable.
- Clock is injectable.
- max_iterations=None permits long-running operation.
- All evidence is immutable.
- All evidence is replayable.
- Canonical stable hashing is required.
- repr() is never used.
- Secret-bearing metadata is rejected.
- Oracle remains permanently read-only.
- Alerts remain disabled.
- Q Series intake remains disabled.
- Canonical handoffs are not published.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade is authorized.
- No order is placed.
- No funds are moved.
- No portfolio is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Callable, Mapping


from .oracle_controlled_shadow_collection_scheduler_tick import (
    ShadowCollectionSchedulerTickRecord,
)

from .oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)

from .oracle_live_shadow_service_bootstrap_contract import (
    ORACLE_SERVICE_ID,
    SERVICE_BOOTSTRAP_STATUS_READY,
    OracleLiveShadowServiceBootstrapRecord,
)

from .oracle_shadow_polling_policy_cadence_engine import (
    ShadowPollingState,
)


SCHEMA_VERSION = "OLA-023"
ENGINE_ID = "OLA-023"

REQUIRED_READINESS_ENGINE_ID = "OLA-018"
REQUIRED_SCHEDULER_ENGINE_ID = "OLA-021"

SERVICE_RUN_STATUS_COMPLETED = "completed"
SERVICE_RUN_STATUS_STOPPED = "stopped"

ITERATION_STATUS_COMPLETED = "completed"
ITERATION_STATUS_NOOP = "noop"
ITERATION_STATUS_FAILED = "failed"

SERVICE_ITERATION_RECORD_TYPE = (
    "oracle_live_shadow_service_iteration_record"
)

SERVICE_RUN_RECORD_TYPE = (
    "oracle_live_shadow_service_run_record"
)


class OracleLiveShadowServiceRunnerContractError(ValueError):
    """Raised when runner contract data is malformed."""


class OracleLiveShadowServiceRunnerCompatibilityError(
    OracleLiveShadowServiceRunnerContractError
):
    """Raised when bound OLA contracts are incompatible."""


class OracleLiveShadowServiceRunnerInvariantError(RuntimeError):
    """Raised when permanent Oracle invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be an int"
        )

    if value <= 0:
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be greater than zero"
        )

    return value


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise OracleLiveShadowServiceRunnerContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise OracleLiveShadowServiceRunnerContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise OracleLiveShadowServiceRunnerContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, Mapping):
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(
        value
    )

    if not isinstance(canonical, dict):
        raise OracleLiveShadowServiceRunnerContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    forbidden_keys = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "private_key",
        "signing_key",
        "dsn",
        "database_url",
        "connection_string",
        "token",
    }

    result = tuple(
        (
            key,
            canonical[key],
        )
        for key in sorted(canonical)
    )

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise OracleLiveShadowServiceRunnerContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )

    return result


def _mapping_from_immutable(
    value: tuple[tuple[str, Any], ...],
) -> dict[str, Any]:
    return {
        key: item
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class OracleLiveShadowReadinessProviderBinding:
    provider_id: str
    engine_id: str
    readiness_callable: Callable[..., KalshiLiveReadReadinessRecord]
    read_only: bool = True
    execution_allowed: bool = False

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "provider_id",
            _require_non_empty_string(
                self.provider_id,
                "provider_id",
            ),
        )

        object.__setattr__(
            self,
            "engine_id",
            _require_non_empty_string(
                self.engine_id,
                "engine_id",
            ),
        )

        if self.engine_id != REQUIRED_READINESS_ENGINE_ID:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness provider must identify OLA-018"
            )

        if not callable(
            self.readiness_callable
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "readiness_callable must be callable"
            )

        if self.read_only is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness provider lost read_only invariant"
            )

        if self.execution_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness provider gained execution capability"
            )


@dataclass(frozen=True, slots=True)
class OracleLiveShadowSchedulerBinding:
    scheduler_id: str
    engine_id: str
    tick_callable: Callable[..., Any]
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_intake_allowed: bool = False

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "scheduler_id",
            _require_non_empty_string(
                self.scheduler_id,
                "scheduler_id",
            ),
        )

        object.__setattr__(
            self,
            "engine_id",
            _require_non_empty_string(
                self.engine_id,
                "engine_id",
            ),
        )

        if self.engine_id != REQUIRED_SCHEDULER_ENGINE_ID:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "scheduler binding must identify OLA-021"
            )

        if not callable(
            self.tick_callable
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "tick_callable must be callable"
            )

        if self.read_only is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "scheduler binding lost read_only invariant"
            )

        if self.execution_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "scheduler binding gained execution capability"
            )

        if self.alerts_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "scheduler binding gained alert capability"
            )

        if self.qseries_intake_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "scheduler binding gained Q Series intake capability"
            )


@dataclass(frozen=True, slots=True)
class OracleLiveShadowEvidenceWriterBinding:
    writer_id: str
    evidence_role: str
    writer_callable: Callable[..., Any]
    read_only_service_boundary: bool = True
    execution_allowed: bool = False

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "writer_id",
            _require_non_empty_string(
                self.writer_id,
                "writer_id",
            ),
        )

        object.__setattr__(
            self,
            "evidence_role",
            _require_non_empty_string(
                self.evidence_role,
                "evidence_role",
            ),
        )

        if self.evidence_role not in {
            "runtime/state",
            "runtime/logs",
        }:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "writer role must be runtime/state or runtime/logs"
            )

        if not callable(
            self.writer_callable
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "writer_callable must be callable"
            )

        if self.read_only_service_boundary is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "writer lost Oracle service boundary"
            )

        if self.execution_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "writer gained execution capability"
            )


@dataclass(frozen=True, slots=True)
class OracleLiveShadowServiceIterationRecord:
    schema_version: str
    engine_id: str
    iteration_id: str
    iteration_number: int
    iteration_status: str
    oracle_service_id: str
    readiness_provider_id: str
    scheduler_id: str
    iteration_started_at: datetime
    readiness_checked_at: datetime
    readiness_evaluated_at: datetime
    scheduler_evaluated_at: datetime
    tick_started_at: datetime
    tick_completed_at: datetime
    iteration_completed_at: datetime
    canonical_clock_lineage_valid: bool
    readiness_timestamp_contract_preserved: bool
    readiness_id: str
    readiness_hash: str
    tick_id: str
    tick_hash: str
    tick_status: str
    cycle_invoked: bool
    cycle_succeeded: bool | None
    previous_state_id: str
    previous_state_hash: str
    next_state_id: str
    next_state_hash: str
    next_consecutive_failures: int
    next_state_suspended: bool
    state_writer_id: str
    state_writer_evidence_hash: str
    log_writer_id: str
    log_writer_evidence_hash: str
    sleep_seconds_after_iteration: int
    sleep_performed_after_iteration: bool
    stop_requested_after_iteration: bool
    reason_codes: tuple[str, ...]
    iteration_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    iteration_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    alert_created: bool
    qseries_intake_record_created: bool
    canonical_handoff_published: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_iteration_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "iteration_id": self.iteration_id,
            "iteration_number": self.iteration_number,
            "iteration_status": self.iteration_status,
            "oracle_service_id": self.oracle_service_id,
            "readiness_provider_id": self.readiness_provider_id,
            "scheduler_id": self.scheduler_id,
            "iteration_started_at": (
                self.iteration_started_at.isoformat()
            ),
            "readiness_checked_at": (
                self.readiness_checked_at.isoformat()
            ),
            "readiness_evaluated_at": (
                self.readiness_evaluated_at.isoformat()
            ),
            "scheduler_evaluated_at": (
                self.scheduler_evaluated_at.isoformat()
            ),
            "tick_started_at": self.tick_started_at.isoformat(),
            "tick_completed_at": self.tick_completed_at.isoformat(),
            "iteration_completed_at": (
                self.iteration_completed_at.isoformat()
            ),
            "canonical_clock_lineage_valid": (
                self.canonical_clock_lineage_valid
            ),
            "readiness_timestamp_contract_preserved": (
                self.readiness_timestamp_contract_preserved
            ),
            "readiness_id": self.readiness_id,
            "readiness_hash": self.readiness_hash,
            "tick_id": self.tick_id,
            "tick_hash": self.tick_hash,
            "tick_status": self.tick_status,
            "cycle_invoked": self.cycle_invoked,
            "cycle_succeeded": self.cycle_succeeded,
            "previous_state_id": self.previous_state_id,
            "previous_state_hash": self.previous_state_hash,
            "next_state_id": self.next_state_id,
            "next_state_hash": self.next_state_hash,
            "next_consecutive_failures": (
                self.next_consecutive_failures
            ),
            "next_state_suspended": self.next_state_suspended,
            "state_writer_id": self.state_writer_id,
            "state_writer_evidence_hash": (
                self.state_writer_evidence_hash
            ),
            "log_writer_id": self.log_writer_id,
            "log_writer_evidence_hash": (
                self.log_writer_evidence_hash
            ),
            "sleep_seconds_after_iteration": (
                self.sleep_seconds_after_iteration
            ),
            "sleep_performed_after_iteration": (
                self.sleep_performed_after_iteration
            ),
            "stop_requested_after_iteration": (
                self.stop_requested_after_iteration
            ),
            "reason_codes": list(self.reason_codes),
            "iteration_metadata": _mapping_from_immutable(
                self.iteration_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "alert_created": self.alert_created,
            "qseries_intake_record_created": (
                self.qseries_intake_record_created
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
        }

        if include_iteration_hash:
            result["iteration_hash"] = self.iteration_hash

        return result

    def verify_iteration_hash(
        self,
    ) -> bool:
        expected = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SERVICE_ITERATION_RECORD_TYPE,
                "iteration": self.to_canonical_dict(
                    include_iteration_hash=False
                ),
            }
        )

        return self.iteration_hash == expected


@dataclass(frozen=True, slots=True)
class OracleLiveShadowServiceRunRecord:
    schema_version: str
    engine_id: str
    service_run_id: str
    service_run_status: str
    oracle_service_id: str
    bootstrap_id: str
    bootstrap_hash: str
    readiness_provider_id: str
    scheduler_id: str
    state_writer_id: str
    log_writer_id: str
    service_started_at: datetime
    service_completed_at: datetime
    service_tick_interval_seconds: int
    max_iterations: int | None
    iteration_count: int
    completed_iteration_count: int
    noop_iteration_count: int
    failed_iteration_count: int
    cycle_invocation_count: int
    successful_cycle_count: int
    canonical_clock_lineage_valid: bool
    readiness_timestamp_contract_preserved: bool
    final_state_id: str
    final_state_hash: str
    final_consecutive_failures: int
    final_state_suspended: bool
    stop_requested: bool
    reason_codes: tuple[str, ...]
    iteration_hashes: tuple[str, ...]
    service_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    service_run_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    separate_process_required: bool
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

    def to_canonical_dict(
        self,
        *,
        include_service_run_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "service_run_id": self.service_run_id,
            "service_run_status": self.service_run_status,
            "oracle_service_id": self.oracle_service_id,
            "bootstrap_id": self.bootstrap_id,
            "bootstrap_hash": self.bootstrap_hash,
            "readiness_provider_id": self.readiness_provider_id,
            "scheduler_id": self.scheduler_id,
            "state_writer_id": self.state_writer_id,
            "log_writer_id": self.log_writer_id,
            "service_started_at": self.service_started_at.isoformat(),
            "service_completed_at": (
                self.service_completed_at.isoformat()
            ),
            "service_tick_interval_seconds": (
                self.service_tick_interval_seconds
            ),
            "max_iterations": self.max_iterations,
            "iteration_count": self.iteration_count,
            "completed_iteration_count": (
                self.completed_iteration_count
            ),
            "noop_iteration_count": self.noop_iteration_count,
            "failed_iteration_count": self.failed_iteration_count,
            "cycle_invocation_count": self.cycle_invocation_count,
            "successful_cycle_count": self.successful_cycle_count,
            "canonical_clock_lineage_valid": (
                self.canonical_clock_lineage_valid
            ),
            "readiness_timestamp_contract_preserved": (
                self.readiness_timestamp_contract_preserved
            ),
            "final_state_id": self.final_state_id,
            "final_state_hash": self.final_state_hash,
            "final_consecutive_failures": (
                self.final_consecutive_failures
            ),
            "final_state_suspended": self.final_state_suspended,
            "stop_requested": self.stop_requested,
            "reason_codes": list(self.reason_codes),
            "iteration_hashes": list(self.iteration_hashes),
            "service_metadata": _mapping_from_immutable(
                self.service_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "separate_process_required": (
                self.separate_process_required
            ),
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": self.qseries_intake_allowed,
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
        }

        if include_service_run_hash:
            result["service_run_hash"] = self.service_run_hash

        return result

    def verify_service_run_hash(
        self,
    ) -> bool:
        expected = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SERVICE_RUN_RECORD_TYPE,
                "service_run": self.to_canonical_dict(
                    include_service_run_hash=False
                ),
            }
        )

        return self.service_run_hash == expected


class OracleLiveShadowServiceRunner:
    """
    Thin live-shadow service loop with one canonical clock lineage.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    read_only = True
    execution_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        bootstrap_record: OracleLiveShadowServiceBootstrapRecord,
        readiness_provider: OracleLiveShadowReadinessProviderBinding,
        scheduler: OracleLiveShadowSchedulerBinding,
        state_writer: OracleLiveShadowEvidenceWriterBinding,
        log_writer: OracleLiveShadowEvidenceWriterBinding,
        clock_callable: Callable[[], datetime],
        sleep_callable: Callable[[int], Any],
        stop_requested_callable: Callable[[], bool],
        service_tick_interval_seconds: int,
    ) -> None:
        if not isinstance(
            bootstrap_record,
            OracleLiveShadowServiceBootstrapRecord,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "bootstrap_record must be "
                "OracleLiveShadowServiceBootstrapRecord"
            )

        if not isinstance(
            readiness_provider,
            OracleLiveShadowReadinessProviderBinding,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "invalid readiness provider binding"
            )

        if not isinstance(
            scheduler,
            OracleLiveShadowSchedulerBinding,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "invalid scheduler binding"
            )

        if not isinstance(
            state_writer,
            OracleLiveShadowEvidenceWriterBinding,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "invalid state writer binding"
            )

        if not isinstance(
            log_writer,
            OracleLiveShadowEvidenceWriterBinding,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "invalid log writer binding"
            )

        if not callable(clock_callable):
            raise OracleLiveShadowServiceRunnerContractError(
                "clock_callable must be callable"
            )

        if not callable(sleep_callable):
            raise OracleLiveShadowServiceRunnerContractError(
                "sleep_callable must be callable"
            )

        if not callable(stop_requested_callable):
            raise OracleLiveShadowServiceRunnerContractError(
                "stop_requested_callable must be callable"
            )

        self._bootstrap_record = bootstrap_record
        self._readiness_provider = readiness_provider
        self._scheduler = scheduler
        self._state_writer = state_writer
        self._log_writer = log_writer
        self._clock_callable = clock_callable
        self._sleep_callable = sleep_callable
        self._stop_requested_callable = stop_requested_callable
        self._service_tick_interval_seconds = _require_positive_int(
            service_tick_interval_seconds,
            "service_tick_interval_seconds",
        )

        self._last_clock_value = None

        self._validate_bootstrap()
        self._validate_writer_roles()
        self._assert_invariants()

    def _assert_invariants(
        self,
    ) -> None:
        if self.read_only is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "OLA-023 lost read_only invariant"
            )

        forbidden = {
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
        }

        if any(forbidden.values()):
            raise OracleLiveShadowServiceRunnerInvariantError(
                "OLA-023 gained execution capability"
            )

    def _validate_bootstrap(
        self,
    ) -> None:
        record = self._bootstrap_record

        if record.schema_version != "OLA-022":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "bootstrap schema must be OLA-022"
            )

        if record.engine_id != "OLA-022":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "bootstrap engine must be OLA-022"
            )

        if record.bootstrap_status != SERVICE_BOOTSTRAP_STATUS_READY:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "bootstrap must be ready"
            )

        if record.oracle_service_id != ORACLE_SERVICE_ID:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "Oracle service identity mismatch"
            )

        if record.service_start_allowed is not True:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "service start not allowed"
            )

        if record.separate_process_required is not True:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "separate process requirement missing"
            )

        if record.oracle_execution_authority is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "Oracle gained execution authority"
            )

        if record.direct_execution_import_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "direct execution imports allowed"
            )

        if record.read_only is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "bootstrap lost read_only invariant"
            )

        if record.execution_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "bootstrap gained execution capability"
            )

        if record.verify_bootstrap_hash() is not True:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "bootstrap hash validation failed"
            )

    def _validate_writer_roles(
        self,
    ) -> None:
        if self._state_writer.evidence_role != "runtime/state":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "state writer must own runtime/state"
            )

        if self._log_writer.evidence_role != "runtime/logs":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "log writer must own runtime/logs"
            )

    def _clock(
        self,
    ) -> datetime:
        value = _require_aware_datetime(
            self._clock_callable(),
            "clock_callable result",
        )

        if (
            self._last_clock_value is not None
            and value < self._last_clock_value
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "service clock regression blocked"
            )

        self._last_clock_value = value

        return value

    @staticmethod
    def _require_stop_result(
        value: Any,
    ) -> bool:
        if not isinstance(value, bool):
            raise OracleLiveShadowServiceRunnerContractError(
                "stop_requested_callable must return bool"
            )

        return value

    @staticmethod
    def _validate_clock_lineage(
        *,
        iteration_started_at: datetime,
        readiness_checked_at: datetime,
        readiness_evaluated_at: datetime,
        scheduler_evaluated_at: datetime,
        tick_started_at: datetime,
        tick_completed_at: datetime,
        iteration_completed_at: datetime,
    ) -> None:
        values = (
            iteration_started_at,
            readiness_checked_at,
            readiness_evaluated_at,
            scheduler_evaluated_at,
            tick_started_at,
            tick_completed_at,
            iteration_completed_at,
        )

        for previous, current in zip(
            values,
            values[1:],
        ):
            if current < previous:
                raise OracleLiveShadowServiceRunnerContractError(
                    "canonical service clock lineage regressed"
                )

    @staticmethod
    def _validate_readiness(
        *,
        readiness: Any,
        supplied_checked_at: datetime,
        supplied_evaluated_at: datetime,
    ) -> KalshiLiveReadReadinessRecord:
        if not isinstance(
            readiness,
            KalshiLiveReadReadinessRecord,
        ):
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness provider returned incompatible record"
            )

        if readiness.schema_version != "OLA-018":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness schema must be OLA-018"
            )

        if readiness.engine_id != "OLA-018":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness engine must be OLA-018"
            )

        if readiness.checked_at != supplied_checked_at:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness provider did not preserve checked_at"
            )

        if readiness.evaluated_at != supplied_evaluated_at:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness provider did not preserve evaluated_at"
            )

        if readiness.readiness_status != "passed":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness must pass"
            )

        if readiness.live_shadow_cycle_entry_ready is not True:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "readiness does not permit shadow-cycle entry"
            )

        if readiness.shadow_mode is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness left shadow mode"
            )

        if readiness.alerts_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness gained alert capability"
            )

        if readiness.qseries_intake_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness gained Q Series intake capability"
            )

        if readiness.read_only is not True:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness lost read_only invariant"
            )

        if readiness.execution_allowed is not False:
            raise OracleLiveShadowServiceRunnerInvariantError(
                "readiness gained execution capability"
            )

        return readiness

    @staticmethod
    def _validate_tick_result(
        *,
        tick_result: Any,
        readiness: KalshiLiveReadReadinessRecord,
        previous_state: ShadowPollingState,
    ) -> tuple[
        ShadowCollectionSchedulerTickRecord,
        ShadowPollingState,
        Any | None,
    ]:
        if (
            not isinstance(tick_result, tuple)
            or len(tick_result) != 3
        ):
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "OLA-021 binding must return "
                "(tick_record, next_state, cycle_result)"
            )

        tick_record, next_state, cycle_result = tick_result

        if not isinstance(
            tick_record,
            ShadowCollectionSchedulerTickRecord,
        ):
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "invalid OLA-021 tick record"
            )

        if not isinstance(
            next_state,
            ShadowPollingState,
        ):
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "invalid next polling state"
            )

        if tick_record.schema_version != "OLA-021":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick schema must be OLA-021"
            )

        if tick_record.engine_id != "OLA-021":
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick engine must be OLA-021"
            )

        if tick_record.readiness_id != readiness.readiness_id:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick/readiness identity mismatch"
            )

        if tick_record.readiness_hash != readiness.readiness_hash:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick/readiness hash mismatch"
            )

        if tick_record.previous_state_id != previous_state.state_id:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick previous state identity mismatch"
            )

        if tick_record.previous_state_hash != previous_state.state_hash:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick previous state hash mismatch"
            )

        if tick_record.next_state_id != next_state.state_id:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick next state identity mismatch"
            )

        if tick_record.next_state_hash != next_state.state_hash:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick next state hash mismatch"
            )

        if tick_record.verify_tick_hash() is not True:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "tick hash validation failed"
            )

        forbidden = {
            "alert_created": tick_record.alert_created,
            "qseries_intake_record_created": (
                tick_record.qseries_intake_record_created
            ),
            "canonical_handoff_published": (
                tick_record.canonical_handoff_published
            ),
            "execution_allowed": tick_record.execution_allowed,
            "execution_adapter_resolved": (
                tick_record.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                tick_record.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                tick_record.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                tick_record.order_placement_allowed
            ),
            "funds_moved": tick_record.funds_moved,
            "portfolio_mutated": tick_record.portfolio_mutated,
        }

        if any(forbidden.values()):
            raise OracleLiveShadowServiceRunnerInvariantError(
                "OLA-021 tick gained forbidden capability"
            )

        return (
            tick_record,
            next_state,
            cycle_result,
        )

    def run(
        self,
        *,
        initial_polling_state: ShadowPollingState,
        max_iterations: int | None,
        readiness_kwargs_factory: Callable[
            [
                int,
                ShadowPollingState,
                datetime,
                datetime,
            ],
            Mapping[str, Any],
        ],
        scheduler_kwargs_factory: Callable[
            [
                int,
                KalshiLiveReadReadinessRecord,
                ShadowPollingState,
                datetime,
                datetime,
                datetime,
            ],
            Mapping[str, Any],
        ],
        service_metadata: Mapping[str, Any],
    ) -> tuple[
        OracleLiveShadowServiceRunRecord,
        tuple[OracleLiveShadowServiceIterationRecord, ...],
        ShadowPollingState,
    ]:
        self._assert_invariants()
        self._validate_bootstrap()

        if not isinstance(
            initial_polling_state,
            ShadowPollingState,
        ):
            raise OracleLiveShadowServiceRunnerContractError(
                "initial_polling_state must be ShadowPollingState"
            )

        if max_iterations is not None:
            _require_positive_int(
                max_iterations,
                "max_iterations",
            )

        if not callable(readiness_kwargs_factory):
            raise OracleLiveShadowServiceRunnerContractError(
                "readiness_kwargs_factory must be callable"
            )

        if not callable(scheduler_kwargs_factory):
            raise OracleLiveShadowServiceRunnerContractError(
                "scheduler_kwargs_factory must be callable"
            )

        immutable_service_metadata = _immutable_mapping(
            service_metadata,
            "service_metadata",
        )

        service_started_at = self._clock()

        current_state = initial_polling_state

        iteration_records = []

        completed_count = 0
        noop_count = 0
        failed_count = 0
        cycle_invocation_count = 0
        successful_cycle_count = 0

        iteration_number = 0
        stop_requested = False

        while True:
            stop_requested = self._require_stop_result(
                self._stop_requested_callable()
            )

            if stop_requested:
                break

            if (
                max_iterations is not None
                and iteration_number >= max_iterations
            ):
                break

            iteration_number += 1

            iteration_started_at = self._clock()

            readiness_checked_at = self._clock()

            readiness_evaluated_at = self._clock()

            readiness_kwargs = readiness_kwargs_factory(
                iteration_number,
                current_state,
                readiness_checked_at,
                readiness_evaluated_at,
            )

            if not isinstance(
                readiness_kwargs,
                Mapping,
            ):
                raise OracleLiveShadowServiceRunnerContractError(
                    "readiness_kwargs_factory must return mapping"
                )

            readiness = (
                self._readiness_provider.readiness_callable(
                    **dict(readiness_kwargs)
                )
            )

            readiness = self._validate_readiness(
                readiness=readiness,
                supplied_checked_at=readiness_checked_at,
                supplied_evaluated_at=readiness_evaluated_at,
            )

            scheduler_evaluated_at = self._clock()

            tick_started_at = self._clock()

            tick_completed_at = self._clock()

            scheduler_kwargs = scheduler_kwargs_factory(
                iteration_number,
                readiness,
                current_state,
                scheduler_evaluated_at,
                tick_started_at,
                tick_completed_at,
            )

            if not isinstance(
                scheduler_kwargs,
                Mapping,
            ):
                raise OracleLiveShadowServiceRunnerContractError(
                    "scheduler_kwargs_factory must return mapping"
                )

            tick_result = self._scheduler.tick_callable(
                **dict(scheduler_kwargs)
            )

            (
                tick_record,
                next_state,
                cycle_result,
            ) = self._validate_tick_result(
                tick_result=tick_result,
                readiness=readiness,
                previous_state=current_state,
            )

            iteration_completed_at = self._clock()

            self._validate_clock_lineage(
                iteration_started_at=iteration_started_at,
                readiness_checked_at=readiness_checked_at,
                readiness_evaluated_at=readiness_evaluated_at,
                scheduler_evaluated_at=scheduler_evaluated_at,
                tick_started_at=tick_started_at,
                tick_completed_at=tick_completed_at,
                iteration_completed_at=iteration_completed_at,
            )

            state_payload = {
                "schema_version": SCHEMA_VERSION,
                "engine_id": ENGINE_ID,
                "evidence_role": "runtime/state",
                "iteration_number": iteration_number,
                "bootstrap_id": self._bootstrap_record.bootstrap_id,
                "tick_id": tick_record.tick_id,
                "tick_hash": tick_record.tick_hash,
                "previous_state_id": current_state.state_id,
                "previous_state_hash": current_state.state_hash,
                "next_state": next_state.to_canonical_dict(),
                "iteration_completed_at": iteration_completed_at,
            }

            state_writer_result = (
                self._state_writer.writer_callable(
                    evidence=state_payload
                )
            )

            state_writer_evidence_hash = stable_hash(
                {
                    "writer_id": self._state_writer.writer_id,
                    "evidence_role": self._state_writer.evidence_role,
                    "writer_result": _canonicalize(
                        state_writer_result
                    ),
                    "written_evidence_hash": stable_hash(
                        state_payload
                    ),
                }
            )

            log_payload = {
                "schema_version": SCHEMA_VERSION,
                "engine_id": ENGINE_ID,
                "evidence_role": "runtime/logs",
                "iteration_number": iteration_number,
                "bootstrap_id": self._bootstrap_record.bootstrap_id,
                "readiness_id": readiness.readiness_id,
                "readiness_hash": readiness.readiness_hash,
                "tick": tick_record.to_canonical_dict(),
                "cycle_result_present": cycle_result is not None,
                "canonical_clock_lineage_valid": True,
                "iteration_completed_at": iteration_completed_at,
            }

            log_writer_result = (
                self._log_writer.writer_callable(
                    evidence=log_payload
                )
            )

            log_writer_evidence_hash = stable_hash(
                {
                    "writer_id": self._log_writer.writer_id,
                    "evidence_role": self._log_writer.evidence_role,
                    "writer_result": _canonicalize(
                        log_writer_result
                    ),
                    "written_evidence_hash": stable_hash(
                        log_payload
                    ),
                }
            )

            stop_requested_after_iteration = (
                self._require_stop_result(
                    self._stop_requested_callable()
                )
            )

            sleep_performed = False

            if not stop_requested_after_iteration:
                if (
                    max_iterations is None
                    or iteration_number < max_iterations
                ):
                    self._sleep_callable(
                        self._service_tick_interval_seconds
                    )

                    sleep_performed = True

            iteration_record = self._build_iteration_record(
                iteration_number=iteration_number,
                readiness=readiness,
                tick_record=tick_record,
                previous_state=current_state,
                next_state=next_state,
                iteration_started_at=iteration_started_at,
                readiness_checked_at=readiness_checked_at,
                readiness_evaluated_at=readiness_evaluated_at,
                scheduler_evaluated_at=scheduler_evaluated_at,
                tick_started_at=tick_started_at,
                tick_completed_at=tick_completed_at,
                iteration_completed_at=iteration_completed_at,
                state_writer_evidence_hash=(
                    state_writer_evidence_hash
                ),
                log_writer_evidence_hash=(
                    log_writer_evidence_hash
                ),
                sleep_performed=sleep_performed,
                stop_requested_after_iteration=(
                    stop_requested_after_iteration
                ),
            )

            iteration_records.append(
                iteration_record
            )

            if tick_record.tick_status == "completed":
                completed_count += 1

            elif tick_record.tick_status == "noop":
                noop_count += 1

            elif tick_record.tick_status == "failed":
                failed_count += 1

            else:
                raise OracleLiveShadowServiceRunnerCompatibilityError(
                    "unsupported OLA-021 tick status"
                )

            if tick_record.cycle_invoked:
                cycle_invocation_count += 1

            if tick_record.cycle_succeeded is True:
                successful_cycle_count += 1

            current_state = next_state

            if stop_requested_after_iteration:
                stop_requested = True
                break

        service_completed_at = self._clock()

        if stop_requested:
            service_run_status = SERVICE_RUN_STATUS_STOPPED

            reason_codes = (
                "ola_022_bootstrap_verified",
                "canonical_service_clock_lineage_verified",
                "oracle_service_loop_started",
                "explicit_stop_observed",
                "service_returned_control",
                "oracle_qseries_isolation_preserved",
            )

        else:
            service_run_status = SERVICE_RUN_STATUS_COMPLETED

            reason_codes = (
                "ola_022_bootstrap_verified",
                "canonical_service_clock_lineage_verified",
                "oracle_service_loop_started",
                "controlled_iteration_limit_reached",
                "service_returned_control",
                "oracle_qseries_isolation_preserved",
            )

        iteration_tuple = tuple(
            iteration_records
        )

        run_record = self._build_service_run_record(
            service_run_status=service_run_status,
            service_started_at=service_started_at,
            service_completed_at=service_completed_at,
            max_iterations=max_iterations,
            iteration_records=iteration_tuple,
            final_state=current_state,
            completed_count=completed_count,
            noop_count=noop_count,
            failed_count=failed_count,
            cycle_invocation_count=cycle_invocation_count,
            successful_cycle_count=successful_cycle_count,
            stop_requested=stop_requested,
            reason_codes=reason_codes,
            service_metadata=immutable_service_metadata,
        )

        return (
            run_record,
            iteration_tuple,
            current_state,
        )

    def _build_iteration_record(
        self,
        *,
        iteration_number: int,
        readiness: KalshiLiveReadReadinessRecord,
        tick_record: ShadowCollectionSchedulerTickRecord,
        previous_state: ShadowPollingState,
        next_state: ShadowPollingState,
        iteration_started_at: datetime,
        readiness_checked_at: datetime,
        readiness_evaluated_at: datetime,
        scheduler_evaluated_at: datetime,
        tick_started_at: datetime,
        tick_completed_at: datetime,
        iteration_completed_at: datetime,
        state_writer_evidence_hash: str,
        log_writer_evidence_hash: str,
        sleep_performed: bool,
        stop_requested_after_iteration: bool,
    ) -> OracleLiveShadowServiceIterationRecord:
        if tick_record.tick_status == "completed":
            iteration_status = ITERATION_STATUS_COMPLETED

        elif tick_record.tick_status == "noop":
            iteration_status = ITERATION_STATUS_NOOP

        elif tick_record.tick_status == "failed":
            iteration_status = ITERATION_STATUS_FAILED

        else:
            raise OracleLiveShadowServiceRunnerCompatibilityError(
                "unsupported tick status"
            )

        reason_codes = (
            "canonical_clock_lineage_verified",
            "readiness_timestamp_contract_preserved",
            "fresh_readiness_record_consumed",
            "ola_021_tick_consumed",
            f"tick_status_{tick_record.tick_status}",
            "next_polling_state_carried_forward",
            "runtime_state_evidence_written",
            "runtime_log_evidence_written",
            "oracle_qseries_isolation_preserved",
        )

        immutable_metadata = _immutable_mapping(
            {
                "bootstrap_id": self._bootstrap_record.bootstrap_id,
                "bootstrap_hash": self._bootstrap_record.bootstrap_hash,
                "runtime_state_role": (
                    self._bootstrap_record.runtime_state_role
                ),
                "runtime_logs_role": (
                    self._bootstrap_record.runtime_logs_role
                ),
            },
            "iteration_metadata",
        )

        iteration_id = "oracle_service_iteration." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "oracle_service_iteration_identity",
                "iteration_number": iteration_number,
                "bootstrap_hash": self._bootstrap_record.bootstrap_hash,
                "readiness_hash": readiness.readiness_hash,
                "tick_hash": tick_record.tick_hash,
                "previous_state_hash": previous_state.state_hash,
                "next_state_hash": next_state.state_hash,
                "iteration_started_at": iteration_started_at,
                "iteration_completed_at": iteration_completed_at,
            }
        )

        provisional = OracleLiveShadowServiceIterationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            iteration_id=iteration_id,
            iteration_number=iteration_number,
            iteration_status=iteration_status,
            oracle_service_id=ORACLE_SERVICE_ID,
            readiness_provider_id=(
                self._readiness_provider.provider_id
            ),
            scheduler_id=self._scheduler.scheduler_id,
            iteration_started_at=iteration_started_at,
            readiness_checked_at=readiness_checked_at,
            readiness_evaluated_at=readiness_evaluated_at,
            scheduler_evaluated_at=scheduler_evaluated_at,
            tick_started_at=tick_started_at,
            tick_completed_at=tick_completed_at,
            iteration_completed_at=iteration_completed_at,
            canonical_clock_lineage_valid=True,
            readiness_timestamp_contract_preserved=True,
            readiness_id=readiness.readiness_id,
            readiness_hash=readiness.readiness_hash,
            tick_id=tick_record.tick_id,
            tick_hash=tick_record.tick_hash,
            tick_status=tick_record.tick_status,
            cycle_invoked=tick_record.cycle_invoked,
            cycle_succeeded=tick_record.cycle_succeeded,
            previous_state_id=previous_state.state_id,
            previous_state_hash=previous_state.state_hash,
            next_state_id=next_state.state_id,
            next_state_hash=next_state.state_hash,
            next_consecutive_failures=(
                next_state.consecutive_failures
            ),
            next_state_suspended=next_state.suspended,
            state_writer_id=self._state_writer.writer_id,
            state_writer_evidence_hash=state_writer_evidence_hash,
            log_writer_id=self._log_writer.writer_id,
            log_writer_evidence_hash=log_writer_evidence_hash,
            sleep_seconds_after_iteration=(
                self._service_tick_interval_seconds
            ),
            sleep_performed_after_iteration=sleep_performed,
            stop_requested_after_iteration=(
                stop_requested_after_iteration
            ),
            reason_codes=reason_codes,
            iteration_metadata=immutable_metadata,
            iteration_hash="",
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            alert_created=False,
            qseries_intake_record_created=False,
            canonical_handoff_published=False,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        iteration_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SERVICE_ITERATION_RECORD_TYPE,
                "iteration": provisional.to_canonical_dict(
                    include_iteration_hash=False
                ),
            }
        )

        return OracleLiveShadowServiceIterationRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            iteration_id=provisional.iteration_id,
            iteration_number=provisional.iteration_number,
            iteration_status=provisional.iteration_status,
            oracle_service_id=provisional.oracle_service_id,
            readiness_provider_id=(
                provisional.readiness_provider_id
            ),
            scheduler_id=provisional.scheduler_id,
            iteration_started_at=provisional.iteration_started_at,
            readiness_checked_at=provisional.readiness_checked_at,
            readiness_evaluated_at=(
                provisional.readiness_evaluated_at
            ),
            scheduler_evaluated_at=(
                provisional.scheduler_evaluated_at
            ),
            tick_started_at=provisional.tick_started_at,
            tick_completed_at=provisional.tick_completed_at,
            iteration_completed_at=(
                provisional.iteration_completed_at
            ),
            canonical_clock_lineage_valid=True,
            readiness_timestamp_contract_preserved=True,
            readiness_id=provisional.readiness_id,
            readiness_hash=provisional.readiness_hash,
            tick_id=provisional.tick_id,
            tick_hash=provisional.tick_hash,
            tick_status=provisional.tick_status,
            cycle_invoked=provisional.cycle_invoked,
            cycle_succeeded=provisional.cycle_succeeded,
            previous_state_id=provisional.previous_state_id,
            previous_state_hash=provisional.previous_state_hash,
            next_state_id=provisional.next_state_id,
            next_state_hash=provisional.next_state_hash,
            next_consecutive_failures=(
                provisional.next_consecutive_failures
            ),
            next_state_suspended=(
                provisional.next_state_suspended
            ),
            state_writer_id=provisional.state_writer_id,
            state_writer_evidence_hash=(
                provisional.state_writer_evidence_hash
            ),
            log_writer_id=provisional.log_writer_id,
            log_writer_evidence_hash=(
                provisional.log_writer_evidence_hash
            ),
            sleep_seconds_after_iteration=(
                provisional.sleep_seconds_after_iteration
            ),
            sleep_performed_after_iteration=(
                provisional.sleep_performed_after_iteration
            ),
            stop_requested_after_iteration=(
                provisional.stop_requested_after_iteration
            ),
            reason_codes=provisional.reason_codes,
            iteration_metadata=provisional.iteration_metadata,
            iteration_hash=iteration_hash,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            alert_created=False,
            qseries_intake_record_created=False,
            canonical_handoff_published=False,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def _build_service_run_record(
        self,
        *,
        service_run_status: str,
        service_started_at: datetime,
        service_completed_at: datetime,
        max_iterations: int | None,
        iteration_records: tuple[
            OracleLiveShadowServiceIterationRecord,
            ...
        ],
        final_state: ShadowPollingState,
        completed_count: int,
        noop_count: int,
        failed_count: int,
        cycle_invocation_count: int,
        successful_cycle_count: int,
        stop_requested: bool,
        reason_codes: tuple[str, ...],
        service_metadata: tuple[tuple[str, Any], ...],
    ) -> OracleLiveShadowServiceRunRecord:
        iteration_hashes = tuple(
            record.iteration_hash
            for record in iteration_records
        )

        clock_lineage_valid = all(
            record.canonical_clock_lineage_valid
            for record in iteration_records
        )

        readiness_timestamp_contract_preserved = all(
            record.readiness_timestamp_contract_preserved
            for record in iteration_records
        )

        service_run_id = "oracle_service_run." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "oracle_service_run_identity",
                "bootstrap_hash": self._bootstrap_record.bootstrap_hash,
                "service_started_at": service_started_at,
                "service_completed_at": service_completed_at,
                "iteration_hashes": iteration_hashes,
                "final_state_hash": final_state.state_hash,
            }
        )

        provisional = OracleLiveShadowServiceRunRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            service_run_id=service_run_id,
            service_run_status=service_run_status,
            oracle_service_id=ORACLE_SERVICE_ID,
            bootstrap_id=self._bootstrap_record.bootstrap_id,
            bootstrap_hash=self._bootstrap_record.bootstrap_hash,
            readiness_provider_id=(
                self._readiness_provider.provider_id
            ),
            scheduler_id=self._scheduler.scheduler_id,
            state_writer_id=self._state_writer.writer_id,
            log_writer_id=self._log_writer.writer_id,
            service_started_at=service_started_at,
            service_completed_at=service_completed_at,
            service_tick_interval_seconds=(
                self._service_tick_interval_seconds
            ),
            max_iterations=max_iterations,
            iteration_count=len(iteration_records),
            completed_iteration_count=completed_count,
            noop_iteration_count=noop_count,
            failed_iteration_count=failed_count,
            cycle_invocation_count=cycle_invocation_count,
            successful_cycle_count=successful_cycle_count,
            canonical_clock_lineage_valid=clock_lineage_valid,
            readiness_timestamp_contract_preserved=(
                readiness_timestamp_contract_preserved
            ),
            final_state_id=final_state.state_id,
            final_state_hash=final_state.state_hash,
            final_consecutive_failures=(
                final_state.consecutive_failures
            ),
            final_state_suspended=final_state.suspended,
            stop_requested=stop_requested,
            reason_codes=reason_codes,
            iteration_hashes=iteration_hashes,
            service_metadata=service_metadata,
            service_run_hash="",
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            separate_process_required=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_handoff_published=False,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        service_run_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SERVICE_RUN_RECORD_TYPE,
                "service_run": provisional.to_canonical_dict(
                    include_service_run_hash=False
                ),
            }
        )

        return OracleLiveShadowServiceRunRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            service_run_id=provisional.service_run_id,
            service_run_status=provisional.service_run_status,
            oracle_service_id=provisional.oracle_service_id,
            bootstrap_id=provisional.bootstrap_id,
            bootstrap_hash=provisional.bootstrap_hash,
            readiness_provider_id=(
                provisional.readiness_provider_id
            ),
            scheduler_id=provisional.scheduler_id,
            state_writer_id=provisional.state_writer_id,
            log_writer_id=provisional.log_writer_id,
            service_started_at=provisional.service_started_at,
            service_completed_at=provisional.service_completed_at,
            service_tick_interval_seconds=(
                provisional.service_tick_interval_seconds
            ),
            max_iterations=provisional.max_iterations,
            iteration_count=provisional.iteration_count,
            completed_iteration_count=(
                provisional.completed_iteration_count
            ),
            noop_iteration_count=provisional.noop_iteration_count,
            failed_iteration_count=provisional.failed_iteration_count,
            cycle_invocation_count=provisional.cycle_invocation_count,
            successful_cycle_count=provisional.successful_cycle_count,
            canonical_clock_lineage_valid=(
                provisional.canonical_clock_lineage_valid
            ),
            readiness_timestamp_contract_preserved=(
                provisional.readiness_timestamp_contract_preserved
            ),
            final_state_id=provisional.final_state_id,
            final_state_hash=provisional.final_state_hash,
            final_consecutive_failures=(
                provisional.final_consecutive_failures
            ),
            final_state_suspended=provisional.final_state_suspended,
            stop_requested=provisional.stop_requested,
            reason_codes=provisional.reason_codes,
            iteration_hashes=provisional.iteration_hashes,
            service_metadata=provisional.service_metadata,
            service_run_hash=service_run_hash,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            separate_process_required=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            canonical_handoff_published=False,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "REQUIRED_READINESS_ENGINE_ID",
    "REQUIRED_SCHEDULER_ENGINE_ID",
    "SERVICE_RUN_STATUS_COMPLETED",
    "SERVICE_RUN_STATUS_STOPPED",
    "ITERATION_STATUS_COMPLETED",
    "ITERATION_STATUS_NOOP",
    "ITERATION_STATUS_FAILED",
    "OracleLiveShadowServiceRunnerContractError",
    "OracleLiveShadowServiceRunnerCompatibilityError",
    "OracleLiveShadowServiceRunnerInvariantError",
    "OracleLiveShadowReadinessProviderBinding",
    "OracleLiveShadowSchedulerBinding",
    "OracleLiveShadowEvidenceWriterBinding",
    "OracleLiveShadowServiceIterationRecord",
    "OracleLiveShadowServiceRunRecord",
    "OracleLiveShadowServiceRunner",
    "canonical_json",
    "stable_hash",
]
'''


TEST_CONTENT = r'''
from datetime import datetime, timedelta, timezone
from pathlib import Path


from qseries_v2.oracle_intelligence.live_acquisition.oracle_controlled_shadow_collection_scheduler_tick import (
    OracleControlledShadowCollectionSchedulerTick,
    ShadowCycleRunnerBinding,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_bootstrap_contract import (
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    OracleLiveShadowServiceBootstrapContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_runner import (
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowReadinessProviderBinding,
    OracleLiveShadowSchedulerBinding,
    OracleLiveShadowServiceRunner,
    OracleLiveShadowServiceRunnerCompatibilityError,
    OracleLiveShadowServiceRunnerContractError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_polling_policy_cadence_engine import (
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingPolicy,
    ShadowPollingState,
)


SOURCE_ID = "source.kalshi.market_data"

ADAPTER_ID = (
    "adapter.oracle.kalshi.public_markets.shadow"
)

BASE_TIME = datetime(
    2026,
    7,
    12,
    19,
    0,
    0,
    tzinfo=timezone.utc,
)


class SequenceClock:
    def __init__(
        self,
        *,
        start,
        step_seconds=1,
    ):
        self.current = start

        self.step = timedelta(
            seconds=step_seconds
        )

    def __call__(
        self,
    ):
        result = self.current

        self.current = (
            self.current
            + self.step
        )

        return result


class RegressingClock:
    def __init__(
        self,
    ):
        self.values = [
            BASE_TIME,
            BASE_TIME + timedelta(seconds=1),
            BASE_TIME - timedelta(seconds=1),
        ]

    def __call__(
        self,
    ):
        return self.values.pop(0)


class SleepRecorder:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        seconds,
    ):
        self.calls.append(
            seconds
        )


class StopController:
    def __init__(
        self,
        *,
        stop_after_checks=None,
    ):
        self.checks = 0

        self.stop_after_checks = stop_after_checks

    def __call__(
        self,
    ):
        self.checks += 1

        if self.stop_after_checks is None:
            return False

        return (
            self.checks
            >= self.stop_after_checks
        )


class EvidenceWriter:
    def __init__(
        self,
        role,
    ):
        self.role = role

        self.calls = []

    def __call__(
        self,
        *,
        evidence,
    ):
        self.calls.append(
            evidence
        )

        return {
            "status": "written",
            "role": self.role,
            "write_number": len(self.calls),
        }


class ReadinessProvider:
    def __init__(
        self,
    ):
        self.calls = 0

        self.received_timestamps = []

    def __call__(
        self,
        *,
        iteration_number,
        polling_state_id,
        checked_at,
        evaluated_at,
    ):
        self.calls += 1

        self.received_timestamps.append(
            (
                checked_at,
                evaluated_at,
            )
        )

        return KalshiLiveReadReadinessRecord(
            schema_version="OLA-018",
            engine_id="OLA-018",
            readiness_id=(
                f"readiness.ola023.{iteration_number}"
            ),
            readiness_status="passed",
            adapter_id=ADAPTER_ID,
            source_id=SOURCE_ID,
            source_base_url=(
                "https://external-api.kalshi.com/"
                "trade-api/v2"
            ),
            source_endpoint="/markets",
            http_method="GET",
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            public_endpoint=True,
            authentication_used=False,
            live_get_request_count=1,
            source_contract_valid=True,
            source_probe_health_status="healthy",
            source_reachable=True,
            source_latency_ms=1,
            source_health_evidence_hash=(
                f"{iteration_number:064x}"
            ),
            rate_control_evidence_hash=(
                f"{iteration_number + 10:064x}"
            ),
            source_control_decision_hash=(
                f"{iteration_number + 20:064x}"
            ),
            source_control_reason_codes=(
                "acquisition_allowed",
                "source_reachable",
            ),
            health_policy_evidence_present=True,
            rate_policy_evidence_present=True,
            source_control_acquisition_allowed=True,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            live_shadow_cycle_entry_ready=True,
            continuous_polling_started=False,
            acquisition_performed=False,
            canonical_observation_created=False,
            persistence_invoked=False,
            alert_created=False,
            qseries_intake_record_created=False,
            reason_codes=(
                "live_shadow_cycle_entry_ready",
            ),
            readiness_metadata=(
                ("iteration_number", iteration_number),
                ("polling_state_id", polling_state_id),
            ),
            readiness_hash=(
                f"{iteration_number + 30:064x}"
            ),
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


class TimestampViolatingReadinessProvider:
    def __call__(
        self,
        *,
        iteration_number,
        polling_state_id,
        checked_at,
        evaluated_at,
    ):
        bad_evaluated_at = (
            evaluated_at
            + timedelta(minutes=5)
        )

        return ReadinessProvider().__call__(
            iteration_number=iteration_number,
            polling_state_id=polling_state_id,
            checked_at=checked_at,
            evaluated_at=bad_evaluated_at,
        )


class SuccessfulCycleRunner:
    def __init__(
        self,
    ):
        self.calls = 0

    def __call__(
        self,
        **kwargs,
    ):
        self.calls += 1

        return {
            "schema_version": "OLA-017",
            "engine_id": "OLA-017",
            "status": "completed",
            "source_id": SOURCE_ID,
            "adapter_id": ADAPTER_ID,
            "backend_id": (
                "backend.oracle.postgresql.canonical"
            ),
            "observation_count": 1,
            "canonical_count": 1,
            "duplicate_count": 0,
            "routed_count": 1,
            "postgresql_persistence_count": 1,
            "shadow_mode": True,
            "alerts_allowed": False,
            "qseries_intake_allowed": False,
            "read_only": True,
            "execution_allowed": False,
        }


class DeterministicTickBinding:
    def __init__(
        self,
        scheduler,
    ):
        self.scheduler = scheduler

        self.calls = 0

    def __call__(
        self,
        *,
        readiness,
        polling_state,
        evaluated_at,
        started_at,
        completed_at,
        polling_decision_metadata,
        cycle_kwargs,
        tick_metadata,
    ):
        self.calls += 1

        return self.scheduler.run_tick(
            readiness=readiness,
            polling_state=polling_state,
            evaluated_at=evaluated_at,
            started_at=started_at,
            completed_at=completed_at,
            polling_decision_metadata=(
                polling_decision_metadata
            ),
            cycle_kwargs=cycle_kwargs,
            tick_metadata=tick_metadata,
        )


def build_service_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "environment": "production",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_bootstrap_record():
    contract = OracleLiveShadowServiceBootstrapContract(
        service_contract=build_service_contract()
    )

    runtime_root = Path(
        "C:/qseries/runtime"
    )

    return contract.bootstrap(
        oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
        ola_boundaries=REQUIRED_OLA_BOUNDARIES,
        runtime_root=runtime_root,
        runtime_state_directory=(
            runtime_root
            / "state"
        ),
        runtime_logs_directory=(
            runtime_root
            / "logs"
        ),
        bootstrapped_at=BASE_TIME,
        bootstrap_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
        },
    )


def build_polling_policy():
    return ShadowPollingPolicy.create(
        policy_id="oracle.kalshi.shadow.polling.ola023",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        base_interval_seconds=1,
        jitter_max_seconds=0,
        readiness_max_age_seconds=300,
        failure_backoff_base_seconds=1,
        failure_backoff_multiplier=2,
        failure_backoff_max_seconds=60,
        consecutive_failure_suspend_threshold=4,
        suspension_cooldown_seconds=60,
        explicit_restart_evidence_required=True,
        policy_metadata={
            "test": "OLA-023",
        },
    )


def initial_state():
    return ShadowPollingState.create(
        state_id="polling.state.ola023.initial",
        source_id=SOURCE_ID,
        adapter_id=ADAPTER_ID,
        last_cycle_completed_at=None,
        last_cycle_succeeded=None,
        consecutive_failures=0,
        suspended=False,
        suspended_at=None,
        restart_evidence_present=False,
        state_metadata={
            "state": "initial",
        },
    )


def build_components(
    *,
    stop_after_checks=None,
    readiness_callable=None,
    clock_callable=None,
):
    readiness_provider = (
        ReadinessProvider()
        if readiness_callable is None
        else readiness_callable
    )

    cycle_runner = SuccessfulCycleRunner()

    polling_engine = OracleShadowPollingPolicyCadenceEngine(
        policy=build_polling_policy()
    )

    scheduler = OracleControlledShadowCollectionSchedulerTick(
        polling_engine=polling_engine,
        cycle_runner=ShadowCycleRunnerBinding(
            runner_id="runner.ola017.ola023",
            engine_id="OLA-017",
            source_id=SOURCE_ID,
            adapter_id=ADAPTER_ID,
            cycle_callable=cycle_runner,
        ),
    )

    tick_binding = DeterministicTickBinding(
        scheduler
    )

    state_writer = EvidenceWriter(
        "runtime/state"
    )

    log_writer = EvidenceWriter(
        "runtime/logs"
    )

    clock = (
        SequenceClock(
            start=(
                BASE_TIME
                + timedelta(minutes=1)
            )
        )
        if clock_callable is None
        else clock_callable
    )

    sleeper = SleepRecorder()

    stop_controller = StopController(
        stop_after_checks=stop_after_checks
    )

    runner = OracleLiveShadowServiceRunner(
        bootstrap_record=build_bootstrap_record(),
        readiness_provider=(
            OracleLiveShadowReadinessProviderBinding(
                provider_id=(
                    "provider.ola018.kalshi.readiness"
                ),
                engine_id="OLA-018",
                readiness_callable=readiness_provider,
            )
        ),
        scheduler=OracleLiveShadowSchedulerBinding(
            scheduler_id=(
                "scheduler.ola021.live_shadow"
            ),
            engine_id="OLA-021",
            tick_callable=tick_binding,
        ),
        state_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id="writer.runtime.state.ola023",
                evidence_role="runtime/state",
                writer_callable=state_writer,
            )
        ),
        log_writer=(
            OracleLiveShadowEvidenceWriterBinding(
                writer_id="writer.runtime.logs.ola023",
                evidence_role="runtime/logs",
                writer_callable=log_writer,
            )
        ),
        clock_callable=clock,
        sleep_callable=sleeper,
        stop_requested_callable=stop_controller,
        service_tick_interval_seconds=1,
    )

    return {
        "runner": runner,
        "readiness_provider": readiness_provider,
        "cycle_runner": cycle_runner,
        "tick_binding": tick_binding,
        "state_writer": state_writer,
        "log_writer": log_writer,
        "sleeper": sleeper,
        "stop_controller": stop_controller,
    }


def readiness_kwargs_factory(
    iteration_number,
    polling_state,
    checked_at,
    evaluated_at,
):
    return {
        "iteration_number": iteration_number,
        "polling_state_id": polling_state.state_id,
        "checked_at": checked_at,
        "evaluated_at": evaluated_at,
    }


def scheduler_kwargs_factory(
    iteration_number,
    readiness,
    polling_state,
    evaluated_at,
    started_at,
    completed_at,
):
    return {
        "readiness": readiness,
        "polling_state": polling_state,
        "evaluated_at": evaluated_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "polling_decision_metadata": {
            "service_engine_id": "OLA-023",
            "iteration_number": iteration_number,
        },
        "cycle_kwargs": {
            "service_iteration_number": iteration_number,
        },
        "tick_metadata": {
            "service_engine_id": "OLA-023",
            "iteration_number": iteration_number,
        },
    }


def run_controlled_three_iteration_test():
    components = build_components()

    (
        run_record,
        iterations,
        final_state,
    ) = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=3,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
            "test_run": True,
        },
    )

    assert run_record.schema_version == "OLA-023"

    assert run_record.engine_id == "OLA-023"

    assert run_record.service_run_status == "completed"

    assert run_record.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert run_record.iteration_count == 3

    assert len(iterations) == 3

    assert components["readiness_provider"].calls == 3

    assert components["tick_binding"].calls == 3

    assert components["cycle_runner"].calls == 3

    assert len(components["state_writer"].calls) == 3

    assert len(components["log_writer"].calls) == 3

    assert len(components["sleeper"].calls) == 2

    assert components["sleeper"].calls == [
        1,
        1,
    ]

    assert run_record.completed_iteration_count == 3

    assert run_record.noop_iteration_count == 0

    assert run_record.failed_iteration_count == 0

    assert run_record.cycle_invocation_count == 3

    assert run_record.successful_cycle_count == 3

    assert run_record.canonical_clock_lineage_valid is True

    assert (
        run_record.readiness_timestamp_contract_preserved
        is True
    )

    assert final_state.last_cycle_succeeded is True

    assert final_state.consecutive_failures == 0

    assert final_state.suspended is False

    assert run_record.final_state_id == final_state.state_id

    assert run_record.final_state_hash == final_state.state_hash

    assert run_record.stop_requested is False

    assert run_record.separate_process_required is True

    assert run_record.alerts_allowed is False

    assert run_record.qseries_intake_allowed is False

    assert run_record.canonical_handoff_published is False

    assert run_record.read_only is True

    assert run_record.execution_allowed is False

    assert run_record.execution_adapter_resolved is False

    assert run_record.execution_adapter_invoked is False

    assert run_record.trade_authorization_allowed is False

    assert run_record.order_placement_allowed is False

    assert run_record.funds_moved is False

    assert run_record.portfolio_mutated is False

    assert run_record.verify_service_run_hash() is True

    received_timestamps = (
        components["readiness_provider"].received_timestamps
    )

    assert len(received_timestamps) == 3

    for iteration, timestamps in zip(
        iterations,
        received_timestamps,
    ):
        checked_at, evaluated_at = timestamps

        assert iteration.readiness_checked_at == checked_at

        assert iteration.readiness_evaluated_at == evaluated_at

        assert iteration.canonical_clock_lineage_valid is True

        assert (
            iteration.readiness_timestamp_contract_preserved
            is True
        )

        assert (
            iteration.iteration_started_at
            <= iteration.readiness_checked_at
            <= iteration.readiness_evaluated_at
            <= iteration.scheduler_evaluated_at
            <= iteration.tick_started_at
            <= iteration.tick_completed_at
            <= iteration.iteration_completed_at
        )

        assert iteration.verify_iteration_hash() is True

        assert iteration.read_only is True

        assert iteration.alert_created is False

        assert (
            iteration.qseries_intake_record_created
            is False
        )

        assert (
            iteration.canonical_handoff_published
            is False
        )

        assert iteration.execution_allowed is False

        assert (
            iteration.execution_adapter_resolved
            is False
        )

        assert (
            iteration.execution_adapter_invoked
            is False
        )

        assert (
            iteration.trade_authorization_allowed
            is False
        )

        assert iteration.order_placement_allowed is False

        assert iteration.funds_moved is False

        assert iteration.portfolio_mutated is False

    return (
        run_record,
        iterations,
        final_state,
        components,
    )


def run_explicit_stop_test():
    components = build_components(
        stop_after_checks=4
    )

    (
        run_record,
        iterations,
        final_state,
    ) = components["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=None,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "explicit_stop",
        },
    )

    assert run_record.service_run_status == "stopped"

    assert run_record.stop_requested is True

    assert run_record.iteration_count == 2

    assert len(iterations) == 2

    assert components["readiness_provider"].calls == 2

    assert components["tick_binding"].calls == 2

    assert components["cycle_runner"].calls == 2

    assert len(components["state_writer"].calls) == 2

    assert len(components["log_writer"].calls) == 2

    assert len(components["sleeper"].calls) == 1

    assert final_state.consecutive_failures == 0

    return run_record


def run_deterministic_replay_test():
    first = build_components()

    second = build_components()

    first_result = first["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=2,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "deterministic_replay",
        },
    )

    second_result = second["runner"].run(
        initial_polling_state=initial_state(),
        max_iterations=2,
        readiness_kwargs_factory=readiness_kwargs_factory,
        scheduler_kwargs_factory=scheduler_kwargs_factory,
        service_metadata={
            "test": "deterministic_replay",
        },
    )

    first_run, first_iterations, first_state = first_result

    second_run, second_iterations, second_state = second_result

    assert first_run == second_run

    assert first_iterations == second_iterations

    assert first_state == second_state

    assert (
        first_run.service_run_hash
        == second_run.service_run_hash
    )

    assert (
        first_state.state_hash
        == second_state.state_hash
    )


def run_readiness_timestamp_fail_closed_test():
    components = build_components(
        readiness_callable=(
            TimestampViolatingReadinessProvider()
        )
    )

    try:
        components["runner"].run(
            initial_polling_state=initial_state(),
            max_iterations=1,
            readiness_kwargs_factory=readiness_kwargs_factory,
            scheduler_kwargs_factory=scheduler_kwargs_factory,
            service_metadata={
                "test": "timestamp_violation",
            },
        )

        raise AssertionError(
            "readiness timestamp violation must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass


def run_clock_regression_fail_closed_test():
    components = build_components(
        clock_callable=RegressingClock()
    )

    try:
        components["runner"].run(
            initial_polling_state=initial_state(),
            max_iterations=1,
            readiness_kwargs_factory=readiness_kwargs_factory,
            scheduler_kwargs_factory=scheduler_kwargs_factory,
            service_metadata={
                "test": "clock_regression",
            },
        )

        raise AssertionError(
            "service clock regression must fail closed"
        )

    except OracleLiveShadowServiceRunnerContractError:
        pass


def run_binding_fail_closed_tests():
    try:
        OracleLiveShadowReadinessProviderBinding(
            provider_id="provider.invalid",
            engine_id="OLA-999",
            readiness_callable=lambda: None,
        )

        raise AssertionError(
            "non-OLA-018 provider must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass

    try:
        OracleLiveShadowSchedulerBinding(
            scheduler_id="scheduler.invalid",
            engine_id="OLA-999",
            tick_callable=lambda: None,
        )

        raise AssertionError(
            "non-OLA-021 scheduler must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass

    writer = EvidenceWriter(
        "runtime/state"
    )

    try:
        OracleLiveShadowEvidenceWriterBinding(
            writer_id="writer.invalid",
            evidence_role="runtime/data",
            writer_callable=writer,
        )

        raise AssertionError(
            "unsupported writer role must fail closed"
        )

    except OracleLiveShadowServiceRunnerCompatibilityError:
        pass


def main():
    (
        run_record,
        iterations,
        final_state,
        components,
    ) = run_controlled_three_iteration_test()

    stopped_run = run_explicit_stop_test()

    run_deterministic_replay_test()

    run_readiness_timestamp_fail_closed_test()

    run_clock_regression_fail_closed_test()

    run_binding_fail_closed_tests()

    result = {
        "schema_version": run_record.schema_version,
        "engine_id": run_record.engine_id,
        "status": "passed",
        "service_run_status": (
            run_record.service_run_status
        ),
        "oracle_service_id": run_record.oracle_service_id,
        "bootstrap_schema_required": "OLA-022",
        "readiness_provider_engine_required": "OLA-018",
        "scheduler_engine_required": "OLA-021",
        "iteration_count": run_record.iteration_count,
        "readiness_provider_call_count": (
            components["readiness_provider"].calls
        ),
        "scheduler_tick_call_count": (
            components["tick_binding"].calls
        ),
        "ola_017_cycle_call_count": (
            components["cycle_runner"].calls
        ),
        "exactly_one_readiness_request_per_iteration": (
            components["readiness_provider"].calls
            == run_record.iteration_count
        ),
        "exactly_one_scheduler_tick_per_iteration": (
            components["tick_binding"].calls
            == run_record.iteration_count
        ),
        "cycle_invocation_count": (
            run_record.cycle_invocation_count
        ),
        "successful_cycle_count": (
            run_record.successful_cycle_count
        ),
        "state_evidence_write_count": (
            len(components["state_writer"].calls)
        ),
        "log_evidence_write_count": (
            len(components["log_writer"].calls)
        ),
        "controlled_sleep_call_count": (
            len(components["sleeper"].calls)
        ),
        "service_tick_interval_seconds": (
            run_record.service_tick_interval_seconds
        ),
        "canonical_clock_lineage_valid": (
            run_record.canonical_clock_lineage_valid
        ),
        "readiness_timestamps_caller_controlled": True,
        "readiness_timestamp_contract_preserved": (
            run_record.readiness_timestamp_contract_preserved
        ),
        "readiness_future_time_not_invented": True,
        "clock_regression_blocked": True,
        "readiness_timestamp_violation_blocked": True,
        "final_consecutive_failures": (
            final_state.consecutive_failures
        ),
        "final_state_suspended": final_state.suspended,
        "explicit_stop_status": (
            stopped_run.service_run_status
        ),
        "explicit_stop_observed": (
            stopped_run.stop_requested
        ),
        "deterministic_iteration_hashing": True,
        "deterministic_service_run_hashing": True,
        "deterministic_replay_valid": True,
        "separate_process_required": (
            run_record.separate_process_required
        ),
        "alerts_allowed": run_record.alerts_allowed,
        "qseries_intake_allowed": (
            run_record.qseries_intake_allowed
        ),
        "canonical_handoff_published": (
            run_record.canonical_handoff_published
        ),
        "read_only": run_record.read_only,
        "execution_allowed": run_record.execution_allowed,
        "execution_adapter_resolved": (
            run_record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            run_record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            run_record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            run_record.order_placement_allowed
        ),
        "funds_moved": run_record.funds_moved,
        "portfolio_mutated": run_record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-023 Oracle Live Shadow "
        "Service Runner"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_live_shadow_service_runner import (
    ITERATION_STATUS_COMPLETED,
    ITERATION_STATUS_FAILED,
    ITERATION_STATUS_NOOP,
    REQUIRED_READINESS_ENGINE_ID,
    REQUIRED_SCHEDULER_ENGINE_ID,
    SERVICE_RUN_STATUS_COMPLETED,
    SERVICE_RUN_STATUS_STOPPED,
    OracleLiveShadowEvidenceWriterBinding,
    OracleLiveShadowReadinessProviderBinding,
    OracleLiveShadowSchedulerBinding,
    OracleLiveShadowServiceIterationRecord,
    OracleLiveShadowServiceRunRecord,
    OracleLiveShadowServiceRunner,
    OracleLiveShadowServiceRunnerCompatibilityError,
    OracleLiveShadowServiceRunnerContractError,
    OracleLiveShadowServiceRunnerInvariantError,
)
'''


EXPORT_NAMES = [
    "ITERATION_STATUS_COMPLETED",
    "ITERATION_STATUS_FAILED",
    "ITERATION_STATUS_NOOP",
    "REQUIRED_READINESS_ENGINE_ID",
    "REQUIRED_SCHEDULER_ENGINE_ID",
    "SERVICE_RUN_STATUS_COMPLETED",
    "SERVICE_RUN_STATUS_STOPPED",
    "OracleLiveShadowEvidenceWriterBinding",
    "OracleLiveShadowReadinessProviderBinding",
    "OracleLiveShadowSchedulerBinding",
    "OracleLiveShadowServiceIterationRecord",
    "OracleLiveShadowServiceRunRecord",
    "OracleLiveShadowServiceRunner",
    "OracleLiveShadowServiceRunnerCompatibilityError",
    "OracleLiveShadowServiceRunnerContractError",
    "OracleLiveShadowServiceRunnerInvariantError",
]


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_live_shadow_service_runner import"
    )

    updated = existing

    if import_marker in updated:
        import_start = updated.index(
            import_marker
        )

        import_end = updated.index(
            "\n)",
            import_start,
        ) + 2

        updated = (
            updated[:import_start]
            + textwrap.dedent(EXPORT_BLOCK).lstrip()
            + updated[import_end:]
        )

    else:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    all_start = updated.find("__all__ = [")

    if all_start == -1:
        raise RuntimeError(
            "__init__.py does not contain __all__"
        )

    closing_index = updated.find(
        "]",
        all_start,
    )

    if closing_index == -1:
        raise RuntimeError(
            "__init__.py does not contain "
            "__all__ closing bracket"
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated[
            all_start:closing_index
        ]:
            continue

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

        closing_index += len(
            export_line
        ) + 1

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-023 INSTALLER")
    print(" Oracle Live Shadow")
    print(" Service Runner")
    print(" FULL CANONICAL CLOCK LINEAGE REWRITE")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-023 rewritten")
    print()
    print("Run:")
    print(
        "py test_ola_023_oracle_live_shadow_"
        "service_runner.py"
    )


if __name__ == "__main__":
    main()