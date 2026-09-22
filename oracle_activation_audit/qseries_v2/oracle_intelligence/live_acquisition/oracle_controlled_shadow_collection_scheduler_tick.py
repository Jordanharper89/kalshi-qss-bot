"""
OLA-021
Oracle Controlled Shadow Collection Scheduler Tick

Controlled one-tick scheduling boundary.

Architecture:

OLA-018 READINESS EVIDENCE
    |
OLA-019 POLLING POLICY DECISION
    |
OLA-021 SCHEDULER TICK
    |
    +-- NOT ELIGIBLE
    |       |
    |       CONTROLLED NO-OP RECORD
    |       NEXT POLLING STATE PRESERVED
    |
    +-- ELIGIBLE
            |
            EXACTLY ONE BOUND OLA-017 CYCLE CALL
            |
            SUCCESS / FAILURE EVIDENCE
            |
            NEXT IMMUTABLE POLLING STATE

Important boundary decision:

OLA-021 binds OLA-017 through an explicit cycle-runner callable.

The callable boundary is intentional.

OLA-021 does not introspect or guess OLA-017 constructor internals or method
names. A service bootstrap layer will bind the proven OLA-017 cycle method
to this scheduler tick.

OLA-021 requires the cycle runner identity:

    OLA-017

This preserves explicit architectural ownership while avoiding hidden
coupling to internal implementation details.

Permanent rules:

- OLA-019 polling decision is authoritative.
- A shadow cycle is invoked only when shadow_cycle_allowed is True.
- Eligible status is required for cycle invocation.
- Exactly one cycle-runner call is allowed per tick.
- Waiting decisions produce controlled no-op evidence.
- Blocked decisions produce controlled no-op evidence.
- Suspended decisions produce controlled no-op evidence.
- Cycle success resets consecutive failures to zero.
- Cycle failure increments consecutive failures by one.
- Reaching the OLA-019 threshold creates suspended next state.
- suspended_at is caller-controlled tick completion time.
- Restart evidence is never invented by OLA-021.
- The next polling state is immutable.
- Scheduler tick records are immutable.
- All timestamps are caller supplied.
- Canonical stable JSON hashing is used.
- repr() is never used.
- No sleep occurs.
- No loop occurs.
- No thread is created.
- No process is created.
- No service daemon is started.
- No alert is created.
- No Q Series intake is created.
- No canonical handoff is published.
- No trade is authorized.
- No execution adapter is resolved.
- No execution adapter is invoked.
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
import re
from typing import Any, Callable, Mapping


from .oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)

from .oracle_shadow_polling_policy_cadence_engine import (
    ELIGIBLE_STATUS,
    OracleShadowPollingPolicyCadenceEngine,
    ShadowPollingDecision,
    ShadowPollingState,
)


SCHEMA_VERSION = "OLA-021"
ENGINE_ID = "OLA-021"

REQUIRED_CYCLE_RUNNER_ENGINE_ID = "OLA-017"

TICK_COMPLETED_STATUS = "completed"
TICK_NOOP_STATUS = "noop"
TICK_FAILED_STATUS = "failed"

SUPPORTED_TICK_STATUSES = (
    TICK_COMPLETED_STATUS,
    TICK_NOOP_STATUS,
    TICK_FAILED_STATUS,
)

SCHEDULER_TICK_RECORD_TYPE = (
    "oracle_controlled_shadow_collection_scheduler_tick"
)


class ShadowCollectionSchedulerTickContractError(ValueError):
    """Raised when scheduler tick contract data is malformed."""


class ShadowCollectionSchedulerTickCompatibilityError(
    ShadowCollectionSchedulerTickContractError
):
    """Raised when upstream scheduler evidence is incompatible."""


class ShadowCollectionSchedulerTickInvariantError(RuntimeError):
    """Raised when permanent Oracle scheduler invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be non-negative"
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
            raise ShadowCollectionSchedulerTickContractError(
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
                raise ShadowCollectionSchedulerTickContractError(
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

    raise ShadowCollectionSchedulerTickContractError(
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



MAX_FAILURE_MESSAGE_LENGTH = 1000

_SECRET_PATTERNS = (
    re.compile(r"(?i)\bpostgres(?:ql)?://[^\s\"\'<>]+"),
    re.compile(r"(?i)\b(?:https?|postgres(?:ql)?)://[^\s/@:]+:[^\s/@]+@[^\s\"\'<>]+"),
    re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"),
    re.compile(
        r"(?i)(\b(?:database_url|password|passwd|api[_-]?key|token|secret|"
        r"private[_-]?key|signing[_-]?key|dsn|connection_string)\b"
        r"\s*[:=]\s*)(?:\"[^\"]*\"|\'[^\']*\'|[^\s,;]+)"
    ),
)


def _sanitize_failure_type(value: Any) -> str:
    raw = type(value).__name__ if isinstance(value, BaseException) else str(value)
    normalized = re.sub(r"[^A-Za-z0-9_.-]", "_", raw.strip())
    if not normalized:
        return "UnknownCycleFailure"
    return normalized[:200]


def _sanitize_failure_message(value: Any) -> tuple[str, bool]:
    raw = str(value)
    normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", raw)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    redacted = False

    for pattern in _SECRET_PATTERNS:
        if pattern.search(normalized):
            redacted = True
            if pattern.groups:
                normalized = pattern.sub(r"\1[REDACTED]", normalized)
            else:
                normalized = pattern.sub("[REDACTED_DATABASE_URL]", normalized)

    if len(normalized) > MAX_FAILURE_MESSAGE_LENGTH:
        normalized = normalized[:MAX_FAILURE_MESSAGE_LENGTH]
        redacted = True

    if not normalized:
        normalized = "cycle failure message unavailable"

    return normalized, redacted


def _build_failure_diagnostics(
    *,
    failure_type: Any,
    failure_message: Any,
    runner_id: str,
    runner_engine_id: str,
) -> tuple[str, str, str, bool]:
    safe_type = _sanitize_failure_type(failure_type)
    safe_message, redacted = _sanitize_failure_message(failure_message)
    failure_identity_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "record_type": "canonical_cycle_failure_identity",
            "failure_type": safe_type,
            "failure_message": safe_message,
            "runner_id": runner_id,
            "runner_engine_id": runner_engine_id,
        }
    )
    return safe_type, safe_message, failure_identity_hash, redacted


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, Mapping):
        raise ShadowCollectionSchedulerTickContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(
        value
    )

    if not isinstance(canonical, dict):
        raise ShadowCollectionSchedulerTickContractError(
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
            raise ShadowCollectionSchedulerTickContractError(
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


def _read_value(
    value: Any,
    field_name: str,
    default: Any = None,
) -> Any:
    if isinstance(value, Mapping):
        return value.get(
            field_name,
            default,
        )

    return getattr(
        value,
        field_name,
        default,
    )


@dataclass(frozen=True, slots=True)
class ShadowCycleRunnerBinding:
    runner_id: str
    engine_id: str
    source_id: str
    adapter_id: str
    cycle_callable: Callable[..., Any]
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_intake_allowed: bool = False

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "runner_id",
            _require_non_empty_string(
                self.runner_id,
                "runner_id",
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

        object.__setattr__(
            self,
            "source_id",
            _require_non_empty_string(
                self.source_id,
                "source_id",
            ),
        )

        object.__setattr__(
            self,
            "adapter_id",
            _require_non_empty_string(
                self.adapter_id,
                "adapter_id",
            ),
        )

        if self.engine_id != REQUIRED_CYCLE_RUNNER_ENGINE_ID:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "cycle runner must identify OLA-017"
            )

        if not callable(
            self.cycle_callable
        ):
            raise ShadowCollectionSchedulerTickContractError(
                "cycle_callable must be callable"
            )

        if self.read_only is not True:
            raise ShadowCollectionSchedulerTickInvariantError(
                "cycle runner binding lost read_only invariant"
            )

        forbidden_true = {
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
        }

        if any(
            forbidden_true.values()
        ):
            raise ShadowCollectionSchedulerTickInvariantError(
                "cycle runner binding gained forbidden capability"
            )


@dataclass(frozen=True, slots=True)
class ShadowCollectionSchedulerTickRecord:
    schema_version: str
    engine_id: str
    tick_id: str
    tick_status: str
    source_id: str
    adapter_id: str
    readiness_id: str
    readiness_hash: str
    polling_decision_id: str
    polling_decision_hash: str
    polling_decision_status: str
    shadow_cycle_allowed: bool
    runner_id: str
    runner_engine_id: str
    started_at: datetime
    completed_at: datetime
    cycle_invocation_count: int
    cycle_invoked: bool
    cycle_succeeded: bool | None
    cycle_status: str | None
    cycle_evidence_hash: str | None
    cycle_failure_type: str | None
    cycle_failure_message: str | None
    cycle_failure_identity_hash: str | None
    cycle_failure_redacted: bool
    cycle_failure_diagnostics_present: bool
    previous_state_id: str
    previous_state_hash: str
    next_state_id: str
    next_state_hash: str
    previous_consecutive_failures: int
    next_consecutive_failures: int
    next_state_suspended: bool
    next_state_suspended_at: datetime | None
    reason_codes: tuple[str, ...]
    tick_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    tick_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    continuous_polling_started: bool
    loop_started: bool
    sleep_performed: bool
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
        include_tick_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "tick_id": self.tick_id,
            "tick_status": self.tick_status,
            "source_id": self.source_id,
            "adapter_id": self.adapter_id,
            "readiness_id": self.readiness_id,
            "readiness_hash": self.readiness_hash,
            "polling_decision_id": (
                self.polling_decision_id
            ),
            "polling_decision_hash": (
                self.polling_decision_hash
            ),
            "polling_decision_status": (
                self.polling_decision_status
            ),
            "shadow_cycle_allowed": (
                self.shadow_cycle_allowed
            ),
            "runner_id": self.runner_id,
            "runner_engine_id": self.runner_engine_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "cycle_invocation_count": (
                self.cycle_invocation_count
            ),
            "cycle_invoked": self.cycle_invoked,
            "cycle_succeeded": self.cycle_succeeded,
            "cycle_status": self.cycle_status,
            "cycle_evidence_hash": self.cycle_evidence_hash,
            "cycle_failure_type": self.cycle_failure_type,
            "cycle_failure_message": self.cycle_failure_message,
            "cycle_failure_identity_hash": self.cycle_failure_identity_hash,
            "cycle_failure_redacted": self.cycle_failure_redacted,
            "cycle_failure_diagnostics_present": self.cycle_failure_diagnostics_present,
            "previous_state_id": self.previous_state_id,
            "previous_state_hash": self.previous_state_hash,
            "next_state_id": self.next_state_id,
            "next_state_hash": self.next_state_hash,
            "previous_consecutive_failures": (
                self.previous_consecutive_failures
            ),
            "next_consecutive_failures": (
                self.next_consecutive_failures
            ),
            "next_state_suspended": (
                self.next_state_suspended
            ),
            "next_state_suspended_at": (
                None
                if self.next_state_suspended_at is None
                else self.next_state_suspended_at.isoformat()
            ),
            "reason_codes": list(
                self.reason_codes
            ),
            "tick_metadata": _mapping_from_immutable(
                self.tick_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "continuous_polling_started": (
                self.continuous_polling_started
            ),
            "loop_started": self.loop_started,
            "sleep_performed": self.sleep_performed,
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

        if include_tick_hash:
            result["tick_hash"] = self.tick_hash

        return result

    def verify_tick_hash(
        self,
    ) -> bool:
        expected = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SCHEDULER_TICK_RECORD_TYPE,
                "tick": self.to_canonical_dict(
                    include_tick_hash=False
                ),
            }
        )

        return self.tick_hash == expected


class OracleControlledShadowCollectionSchedulerTick:
    """
    One governed scheduler tick.

    The scheduler never loops.

    A service runner may repeatedly call this object later.
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
        polling_engine: OracleShadowPollingPolicyCadenceEngine,
        cycle_runner: ShadowCycleRunnerBinding,
    ) -> None:
        if not isinstance(
            polling_engine,
            OracleShadowPollingPolicyCadenceEngine,
        ):
            raise ShadowCollectionSchedulerTickContractError(
                "polling_engine must be "
                "OracleShadowPollingPolicyCadenceEngine"
            )

        if not isinstance(
            cycle_runner,
            ShadowCycleRunnerBinding,
        ):
            raise ShadowCollectionSchedulerTickContractError(
                "cycle_runner must be ShadowCycleRunnerBinding"
            )

        self._polling_engine = polling_engine
        self._cycle_runner = cycle_runner

        self._assert_invariants()

    @property
    def polling_engine(
        self,
    ) -> OracleShadowPollingPolicyCadenceEngine:
        return self._polling_engine

    @property
    def cycle_runner(
        self,
    ) -> ShadowCycleRunnerBinding:
        return self._cycle_runner

    def _assert_invariants(
        self,
    ) -> None:
        expected_false = {
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

        if self.read_only is not True:
            raise ShadowCollectionSchedulerTickInvariantError(
                "scheduler tick lost read_only invariant"
            )

        if any(
            expected_false.values()
        ):
            raise ShadowCollectionSchedulerTickInvariantError(
                "scheduler tick gained execution capability"
            )

        if self._cycle_runner.read_only is not True:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 binding lost read_only invariant"
            )

        if self._cycle_runner.execution_allowed is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 binding gained execution capability"
            )

    def run_tick(
        self,
        *,
        readiness: KalshiLiveReadReadinessRecord,
        polling_state: ShadowPollingState,
        evaluated_at: datetime,
        started_at: datetime,
        completed_at: datetime,
        polling_decision_metadata: Mapping[str, Any],
        cycle_kwargs: Mapping[str, Any],
        tick_metadata: Mapping[str, Any],
    ) -> tuple[
        ShadowCollectionSchedulerTickRecord,
        ShadowPollingState,
        Any | None,
    ]:
        self._assert_invariants()

        normalized_started_at = _require_aware_datetime(
            started_at,
            "started_at",
        )

        normalized_completed_at = _require_aware_datetime(
            completed_at,
            "completed_at",
        )

        if normalized_completed_at < normalized_started_at:
            raise ShadowCollectionSchedulerTickContractError(
                "completed_at cannot be before started_at"
            )

        normalized_evaluated_at = _require_aware_datetime(
            evaluated_at,
            "evaluated_at",
        )

        if normalized_started_at < normalized_evaluated_at:
            raise ShadowCollectionSchedulerTickContractError(
                "started_at cannot be before evaluated_at"
            )

        immutable_tick_metadata = _immutable_mapping(
            tick_metadata,
            "tick_metadata",
        )

        immutable_cycle_kwargs = _immutable_mapping(
            cycle_kwargs,
            "cycle_kwargs",
        )

        decision = self._polling_engine.evaluate(
            readiness=readiness,
            polling_state=polling_state,
            evaluated_at=normalized_evaluated_at,
            decision_metadata=polling_decision_metadata,
        )

        self._validate_decision(
            decision=decision,
            readiness=readiness,
            polling_state=polling_state,
        )

        if decision.shadow_cycle_allowed is not True:
            next_state = polling_state

            return (
                self._build_tick_record(
                    readiness=readiness,
                    decision=decision,
                    previous_state=polling_state,
                    next_state=next_state,
                    started_at=normalized_started_at,
                    completed_at=normalized_completed_at,
                    cycle_invocation_count=0,
                    cycle_invoked=False,
                    cycle_succeeded=None,
                    cycle_status=None,
                    cycle_evidence_hash=None,
                    cycle_failure_type=None,
                    cycle_failure_message=None,
                    cycle_failure_identity_hash=None,
                    cycle_failure_redacted=False,
                    cycle_failure_diagnostics_present=False,
                    reason_codes=(
                        "polling_decision_not_eligible",
                        f"polling_status_{decision.decision_status}",
                        "shadow_cycle_not_invoked",
                        "polling_state_preserved",
                        "continuous_polling_not_started",
                    ),
                    tick_metadata=immutable_tick_metadata,
                    tick_status=TICK_NOOP_STATUS,
                ),
                next_state,
                None,
            )

        if decision.decision_status != ELIGIBLE_STATUS:
            raise ShadowCollectionSchedulerTickInvariantError(
                "shadow_cycle_allowed requires eligible decision status"
            )

        cycle_result = None

        try:
            cycle_result = self._cycle_runner.cycle_callable(
                **_mapping_from_immutable(
                    immutable_cycle_kwargs
                )
            )

            (
                cycle_succeeded,
                cycle_status,
                cycle_evidence_hash,
            ) = self._validate_cycle_result(
                cycle_result
            )

            if cycle_succeeded:
                cycle_failure_type = None
                cycle_failure_message = None
                cycle_failure_identity_hash = None
                cycle_failure_redacted = False
                cycle_failure_diagnostics_present = False
            else:
                (
                    cycle_failure_type,
                    cycle_failure_message,
                    cycle_failure_identity_hash,
                    cycle_failure_redacted,
                ) = _build_failure_diagnostics(
                    failure_type="OLA017CycleStatusFailure",
                    failure_message=(
                        "OLA-017 cycle returned non-success status: "
                        f"{cycle_status}"
                    ),
                    runner_id=self._cycle_runner.runner_id,
                    runner_engine_id=self._cycle_runner.engine_id,
                )
                cycle_failure_diagnostics_present = True

        except Exception as exc:
            cycle_succeeded = False
            cycle_status = "exception"
            (
                cycle_failure_type,
                cycle_failure_message,
                cycle_failure_identity_hash,
                cycle_failure_redacted,
            ) = _build_failure_diagnostics(
                failure_type=exc,
                failure_message=exc,
                runner_id=self._cycle_runner.runner_id,
                runner_engine_id=self._cycle_runner.engine_id,
            )
            cycle_failure_diagnostics_present = True
            cycle_evidence_hash = stable_hash(
                {
                    "schema_version": SCHEMA_VERSION,
                    "record_type": "ola017_cycle_exception_evidence",
                    "failure_type": cycle_failure_type,
                    "failure_message": cycle_failure_message,
                    "failure_identity_hash": cycle_failure_identity_hash,
                    "failure_redacted": cycle_failure_redacted,
                    "runner_id": self._cycle_runner.runner_id,
                    "runner_engine_id": self._cycle_runner.engine_id,
                    "completed_at": normalized_completed_at,
                }
            )

        next_state = self._build_next_state(
            previous_state=polling_state,
            cycle_succeeded=cycle_succeeded,
            completed_at=normalized_completed_at,
        )

        if cycle_succeeded:
            tick_status = TICK_COMPLETED_STATUS

            reason_codes = (
                "polling_decision_eligible",
                "ola_017_runner_identity_verified",
                "exactly_one_shadow_cycle_invoked",
                "shadow_cycle_succeeded",
                "consecutive_failures_reset",
                "next_polling_state_created",
                "continuous_polling_not_started",
            )

        else:
            tick_status = TICK_FAILED_STATUS

            if next_state.suspended:
                reason_codes = (
                    "polling_decision_eligible",
                    "ola_017_runner_identity_verified",
                    "exactly_one_shadow_cycle_invoked",
                    "shadow_cycle_failed",
                    "consecutive_failure_incremented",
                    "failure_suspend_threshold_reached",
                    "next_polling_state_suspended",
                    "continuous_polling_not_started",
                )

            else:
                reason_codes = (
                    "polling_decision_eligible",
                    "ola_017_runner_identity_verified",
                    "exactly_one_shadow_cycle_invoked",
                    "shadow_cycle_failed",
                    "consecutive_failure_incremented",
                    "next_polling_state_created",
                    "continuous_polling_not_started",
                )

        tick_record = self._build_tick_record(
            readiness=readiness,
            decision=decision,
            previous_state=polling_state,
            next_state=next_state,
            started_at=normalized_started_at,
            completed_at=normalized_completed_at,
            cycle_invocation_count=1,
            cycle_invoked=True,
            cycle_succeeded=cycle_succeeded,
            cycle_status=cycle_status,
            cycle_evidence_hash=cycle_evidence_hash,
            cycle_failure_type=cycle_failure_type,
            cycle_failure_message=cycle_failure_message,
            cycle_failure_identity_hash=cycle_failure_identity_hash,
            cycle_failure_redacted=cycle_failure_redacted,
            cycle_failure_diagnostics_present=cycle_failure_diagnostics_present,
            reason_codes=reason_codes,
            tick_metadata=immutable_tick_metadata,
            tick_status=tick_status,
        )

        return (
            tick_record,
            next_state,
            cycle_result,
        )

    def _validate_decision(
        self,
        *,
        decision: ShadowPollingDecision,
        readiness: KalshiLiveReadReadinessRecord,
        polling_state: ShadowPollingState,
    ) -> None:
        if not isinstance(
            decision,
            ShadowPollingDecision,
        ):
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "OLA-019 returned incompatible polling decision"
            )

        if decision.source_id != readiness.source_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision/readiness source identity mismatch"
            )

        if decision.adapter_id != readiness.adapter_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision/readiness adapter identity mismatch"
            )

        if decision.source_id != self._cycle_runner.source_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision/cycle-runner source identity mismatch"
            )

        if decision.adapter_id != self._cycle_runner.adapter_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision/cycle-runner adapter identity mismatch"
            )

        if decision.state_id != polling_state.state_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision polling-state identity mismatch"
            )

        if decision.state_hash != polling_state.state_hash:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision polling-state hash mismatch"
            )

        if decision.readiness_id != readiness.readiness_id:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision readiness identity mismatch"
            )

        if decision.readiness_hash != readiness.readiness_hash:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "decision readiness hash mismatch"
            )

        if decision.read_only is not True:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-019 decision lost read_only invariant"
            )

        if decision.execution_allowed is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-019 decision gained execution capability"
            )

        if decision.continuous_polling_started is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-019 unexpectedly started continuous polling"
            )

        if decision.acquisition_invoked is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-019 unexpectedly invoked acquisition"
            )

        if decision.persistence_invoked is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-019 unexpectedly invoked persistence"
            )

    def _validate_cycle_result(
        self,
        cycle_result: Any,
    ) -> tuple[
        bool,
        str,
        str,
    ]:
        if cycle_result is None:
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "OLA-017 cycle result must not be None"
            )

        schema_version = _read_value(
            cycle_result,
            "schema_version",
        )

        engine_id = _read_value(
            cycle_result,
            "engine_id",
        )

        status = _read_value(
            cycle_result,
            "status",
        )

        read_only = _read_value(
            cycle_result,
            "read_only",
        )

        execution_allowed = _read_value(
            cycle_result,
            "execution_allowed",
        )

        alerts_allowed = _read_value(
            cycle_result,
            "alerts_allowed",
            False,
        )

        qseries_intake_allowed = _read_value(
            cycle_result,
            "qseries_intake_allowed",
            False,
        )

        if schema_version != "OLA-017":
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "cycle result schema_version must be OLA-017"
            )

        if engine_id != "OLA-017":
            raise ShadowCollectionSchedulerTickCompatibilityError(
                "cycle result engine_id must be OLA-017"
            )

        normalized_status = _require_non_empty_string(
            status,
            "cycle_result.status",
        )

        if read_only is not True:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 cycle result lost read_only invariant"
            )

        if execution_allowed is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 cycle result gained execution capability"
            )

        if alerts_allowed is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 cycle result gained alert capability"
            )

        if qseries_intake_allowed is not False:
            raise ShadowCollectionSchedulerTickInvariantError(
                "OLA-017 cycle result gained Q Series intake capability"
            )

        cycle_succeeded = (
            normalized_status == "completed"
        )

        evidence_payload = {
            "schema_version": schema_version,
            "engine_id": engine_id,
            "status": normalized_status,
            "source_id": _read_value(
                cycle_result,
                "source_id",
            ),
            "adapter_id": _read_value(
                cycle_result,
                "adapter_id",
            ),
            "backend_id": _read_value(
                cycle_result,
                "backend_id",
            ),
            "observation_count": _read_value(
                cycle_result,
                "observation_count",
            ),
            "canonical_count": _read_value(
                cycle_result,
                "canonical_count",
            ),
            "duplicate_count": _read_value(
                cycle_result,
                "duplicate_count",
            ),
            "routed_count": _read_value(
                cycle_result,
                "routed_count",
            ),
            "postgresql_persistence_count": _read_value(
                cycle_result,
                "postgresql_persistence_count",
            ),
            "read_only": read_only,
            "execution_allowed": execution_allowed,
            "alerts_allowed": alerts_allowed,
            "qseries_intake_allowed": (
                qseries_intake_allowed
            ),
        }

        return (
            cycle_succeeded,
            normalized_status,
            stable_hash(
                evidence_payload
            ),
        )

    def _build_next_state(
        self,
        *,
        previous_state: ShadowPollingState,
        cycle_succeeded: bool,
        completed_at: datetime,
    ) -> ShadowPollingState:
        threshold = (
            self._polling_engine
            .policy
            .consecutive_failure_suspend_threshold
        )

        if cycle_succeeded:
            next_failures = 0
            suspended = False
            suspended_at = None
            last_cycle_succeeded = True

        else:
            next_failures = (
                previous_state.consecutive_failures
                + 1
            )

            suspended = (
                next_failures
                >= threshold
            )

            suspended_at = (
                completed_at
                if suspended
                else None
            )

            last_cycle_succeeded = False

        next_state_id = "polling.state." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "next_polling_state_identity",
                "previous_state_hash": previous_state.state_hash,
                "completed_at": completed_at,
                "last_cycle_succeeded": last_cycle_succeeded,
                "consecutive_failures": next_failures,
                "suspended": suspended,
                "suspended_at": suspended_at,
            }
        )

        return ShadowPollingState.create(
            state_id=next_state_id,
            source_id=previous_state.source_id,
            adapter_id=previous_state.adapter_id,
            last_cycle_completed_at=completed_at,
            last_cycle_succeeded=last_cycle_succeeded,
            consecutive_failures=next_failures,
            suspended=suspended,
            suspended_at=suspended_at,
            restart_evidence_present=False,
            state_metadata={
                "scheduler_engine_id": ENGINE_ID,
                "previous_state_id": previous_state.state_id,
                "previous_state_hash": previous_state.state_hash,
                "cycle_succeeded": cycle_succeeded,
                "restart_evidence_invented": False,
            },
        )

    def _build_tick_record(
        self,
        *,
        readiness: KalshiLiveReadReadinessRecord,
        decision: ShadowPollingDecision,
        previous_state: ShadowPollingState,
        next_state: ShadowPollingState,
        started_at: datetime,
        completed_at: datetime,
        cycle_invocation_count: int,
        cycle_invoked: bool,
        cycle_succeeded: bool | None,
        cycle_status: str | None,
        cycle_evidence_hash: str | None,
        cycle_failure_type: str | None,
        cycle_failure_message: str | None,
        cycle_failure_identity_hash: str | None,
        cycle_failure_redacted: bool,
        cycle_failure_diagnostics_present: bool,
        reason_codes: tuple[str, ...],
        tick_metadata: tuple[tuple[str, Any], ...],
        tick_status: str,
    ) -> ShadowCollectionSchedulerTickRecord:
        invocation_count = _require_non_negative_int(
            cycle_invocation_count,
            "cycle_invocation_count",
        )

        if invocation_count not in {
            0,
            1,
        }:
            raise ShadowCollectionSchedulerTickInvariantError(
                "one scheduler tick may invoke at most one cycle"
            )

        if cycle_invoked and invocation_count != 1:
            raise ShadowCollectionSchedulerTickInvariantError(
                "invoked cycle requires invocation count 1"
            )

        if not cycle_invoked and invocation_count != 0:
            raise ShadowCollectionSchedulerTickInvariantError(
                "non-invoked cycle requires invocation count 0"
            )

        if tick_status not in SUPPORTED_TICK_STATUSES:
            raise ShadowCollectionSchedulerTickContractError(
                "unsupported tick_status"
            )

        tick_id = "scheduler_tick." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "scheduler_tick_identity",
                "readiness_hash": readiness.readiness_hash,
                "polling_decision_hash": decision.decision_hash,
                "previous_state_hash": previous_state.state_hash,
                "next_state_hash": next_state.state_hash,
                "runner_id": self._cycle_runner.runner_id,
                "started_at": started_at,
                "completed_at": completed_at,
                "cycle_invocation_count": invocation_count,
                "cycle_evidence_hash": cycle_evidence_hash,
            }
        )

        provisional = ShadowCollectionSchedulerTickRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            tick_id=tick_id,
            tick_status=tick_status,
            source_id=decision.source_id,
            adapter_id=decision.adapter_id,
            readiness_id=readiness.readiness_id,
            readiness_hash=readiness.readiness_hash,
            polling_decision_id=decision.decision_id,
            polling_decision_hash=decision.decision_hash,
            polling_decision_status=decision.decision_status,
            shadow_cycle_allowed=decision.shadow_cycle_allowed,
            runner_id=self._cycle_runner.runner_id,
            runner_engine_id=self._cycle_runner.engine_id,
            started_at=started_at,
            completed_at=completed_at,
            cycle_invocation_count=invocation_count,
            cycle_invoked=cycle_invoked,
            cycle_succeeded=cycle_succeeded,
            cycle_status=cycle_status,
            cycle_evidence_hash=cycle_evidence_hash,
            cycle_failure_type=cycle_failure_type,
            cycle_failure_message=cycle_failure_message,
            cycle_failure_identity_hash=cycle_failure_identity_hash,
            cycle_failure_redacted=cycle_failure_redacted,
            cycle_failure_diagnostics_present=cycle_failure_diagnostics_present,
            previous_state_id=previous_state.state_id,
            previous_state_hash=previous_state.state_hash,
            next_state_id=next_state.state_id,
            next_state_hash=next_state.state_hash,
            previous_consecutive_failures=(
                previous_state.consecutive_failures
            ),
            next_consecutive_failures=(
                next_state.consecutive_failures
            ),
            next_state_suspended=next_state.suspended,
            next_state_suspended_at=next_state.suspended_at,
            reason_codes=tuple(
                reason_codes
            ),
            tick_metadata=tick_metadata,
            tick_hash="",
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            continuous_polling_started=False,
            loop_started=False,
            sleep_performed=False,
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

        tick_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": SCHEDULER_TICK_RECORD_TYPE,
                "tick": provisional.to_canonical_dict(
                    include_tick_hash=False
                ),
            }
        )

        return ShadowCollectionSchedulerTickRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            tick_id=provisional.tick_id,
            tick_status=provisional.tick_status,
            source_id=provisional.source_id,
            adapter_id=provisional.adapter_id,
            readiness_id=provisional.readiness_id,
            readiness_hash=provisional.readiness_hash,
            polling_decision_id=(
                provisional.polling_decision_id
            ),
            polling_decision_hash=(
                provisional.polling_decision_hash
            ),
            polling_decision_status=(
                provisional.polling_decision_status
            ),
            shadow_cycle_allowed=(
                provisional.shadow_cycle_allowed
            ),
            runner_id=provisional.runner_id,
            runner_engine_id=provisional.runner_engine_id,
            started_at=provisional.started_at,
            completed_at=provisional.completed_at,
            cycle_invocation_count=(
                provisional.cycle_invocation_count
            ),
            cycle_invoked=provisional.cycle_invoked,
            cycle_succeeded=provisional.cycle_succeeded,
            cycle_status=provisional.cycle_status,
            cycle_evidence_hash=(
                provisional.cycle_evidence_hash
            ),
            cycle_failure_type=provisional.cycle_failure_type,
            cycle_failure_message=provisional.cycle_failure_message,
            cycle_failure_identity_hash=(
                provisional.cycle_failure_identity_hash
            ),
            cycle_failure_redacted=provisional.cycle_failure_redacted,
            cycle_failure_diagnostics_present=(
                provisional.cycle_failure_diagnostics_present
            ),
            previous_state_id=provisional.previous_state_id,
            previous_state_hash=(
                provisional.previous_state_hash
            ),
            next_state_id=provisional.next_state_id,
            next_state_hash=provisional.next_state_hash,
            previous_consecutive_failures=(
                provisional.previous_consecutive_failures
            ),
            next_consecutive_failures=(
                provisional.next_consecutive_failures
            ),
            next_state_suspended=(
                provisional.next_state_suspended
            ),
            next_state_suspended_at=(
                provisional.next_state_suspended_at
            ),
            reason_codes=provisional.reason_codes,
            tick_metadata=provisional.tick_metadata,
            tick_hash=tick_hash,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            continuous_polling_started=False,
            loop_started=False,
            sleep_performed=False,
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


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "REQUIRED_CYCLE_RUNNER_ENGINE_ID",
    "TICK_COMPLETED_STATUS",
    "TICK_NOOP_STATUS",
    "TICK_FAILED_STATUS",
    "SUPPORTED_TICK_STATUSES",
    "ShadowCollectionSchedulerTickContractError",
    "ShadowCollectionSchedulerTickCompatibilityError",
    "ShadowCollectionSchedulerTickInvariantError",
    "ShadowCycleRunnerBinding",
    "ShadowCollectionSchedulerTickRecord",
    "OracleControlledShadowCollectionSchedulerTick",
    "canonical_json",
    "stable_hash",
]
