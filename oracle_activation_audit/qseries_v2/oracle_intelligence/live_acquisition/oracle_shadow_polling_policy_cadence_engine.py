"""
OLA-019
Oracle Shadow Polling Policy and Cadence Engine

FULL SAFETY PRECEDENCE STATE-MACHINE REWRITE

Architecture:

OLA-018 LIVE READ READINESS RECORD
    |
OLA-019 POLLING POLICY
    |
HARD SUSPENSION STATE
    |
FAILURE THRESHOLD SUSPENSION
    |
READINESS FRESHNESS
    |
BASE CADENCE
DETERMINISTIC JITTER
FAILURE BACKOFF
    |
IMMUTABLE POLLING DECISION
    |
FUTURE CONTROLLED SHADOW RUNTIME

Canonical decision precedence:

1. Existing suspended state
2. Consecutive-failure suspension threshold
3. Readiness freshness
4. Cadence and failure backoff
5. Shadow-cycle eligibility

Why precedence matters:

A source that has reached the consecutive-failure suspension threshold must
be recorded as suspended even if its readiness evidence has also become
stale.

Stale readiness must not hide a stronger operational safety state.

After suspension cooldown and restart evidence are satisfied, fresh
readiness is still required before a shadow cycle can resume.

Permanent rules:

- OLA-018 readiness evidence is required.
- Readiness evidence must be passed.
- Readiness evidence must permit live shadow-cycle entry.
- Shadow mode is mandatory.
- Alerts remain disabled.
- Q Series intake remains disabled.
- Existing suspension takes first precedence.
- Failure-threshold suspension takes precedence over readiness freshness.
- Stale readiness blocks non-suspended polling.
- Stale readiness blocks restart after suspension.
- Base cadence is explicit.
- Jitter is deterministic.
- Failure backoff is deterministic.
- Backoff growth is capped.
- Consecutive failures suspend polling.
- Suspension is fail closed.
- Restart cooldown is explicit.
- Explicit restart evidence may be required.
- Fresh readiness is required after suspension before restart.
- This engine does not sleep.
- This engine does not loop.
- This engine does not call Kalshi.
- This engine does not call adapter.acquire().
- This engine does not invoke OLA-017.
- This engine does not create canonical observations.
- This engine does not mutate deduplication state.
- This engine does not invoke PostgreSQL.
- This engine does not create alerts.
- This engine does not send data to Q Series.
- All timestamps are caller supplied.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains permanently read-only.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    JSONValue,
)

from .oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessRecord,
)


SCHEMA_VERSION = "OLA-019"
ENGINE_ID = "OLA-019"

POLLING_POLICY_RECORD_TYPE = (
    "oracle_shadow_polling_policy_record"
)

POLLING_STATE_RECORD_TYPE = (
    "oracle_shadow_polling_state_record"
)

POLLING_DECISION_RECORD_TYPE = (
    "oracle_shadow_polling_decision_record"
)

ELIGIBLE_STATUS = "eligible"
WAITING_STATUS = "waiting"
SUSPENDED_STATUS = "suspended"
BLOCKED_STATUS = "blocked"

SUPPORTED_DECISION_STATUSES = (
    ELIGIBLE_STATUS,
    WAITING_STATUS,
    SUSPENDED_STATUS,
    BLOCKED_STATUS,
)


class ShadowPollingPolicyContractError(ValueError):
    """Raised when polling policy contract data is malformed."""


class ShadowPollingPolicyCompatibilityError(
    ShadowPollingPolicyContractError
):
    """Raised when upstream readiness evidence is incompatible."""


class ShadowPollingPolicyInvariantError(RuntimeError):
    """Raised when permanent Oracle polling invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ShadowPollingPolicyContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be non-negative"
        )

    return value


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    normalized = _require_non_negative_int(
        value,
        field_name,
    )

    if normalized == 0:
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be greater than zero"
        )

    return normalized


def _canonicalize(
    value: Any,
) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ShadowPollingPolicyContractError(
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
        result: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise ShadowPollingPolicyContractError(
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

    raise ShadowPollingPolicyContractError(
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
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise ShadowPollingPolicyContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(
        value
    )

    if not isinstance(canonical, dict):
        raise ShadowPollingPolicyContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    result = tuple(
        (key, canonical[key])
        for key in sorted(canonical)
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
        "uri",
    }

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise ShadowPollingPolicyContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )

    return result


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class ShadowPollingPolicy:
    schema_version: str
    engine_id: str
    policy_id: str
    source_id: str
    adapter_id: str
    base_interval_seconds: int
    jitter_max_seconds: int
    readiness_max_age_seconds: int
    failure_backoff_base_seconds: int
    failure_backoff_multiplier: int
    failure_backoff_max_seconds: int
    consecutive_failure_suspend_threshold: int
    suspension_cooldown_seconds: int
    explicit_restart_evidence_required: bool
    shadow_mode_required: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    policy_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    policy_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        source_id: str,
        adapter_id: str,
        base_interval_seconds: int,
        jitter_max_seconds: int,
        readiness_max_age_seconds: int,
        failure_backoff_base_seconds: int,
        failure_backoff_multiplier: int,
        failure_backoff_max_seconds: int,
        consecutive_failure_suspend_threshold: int,
        suspension_cooldown_seconds: int,
        explicit_restart_evidence_required: bool,
        policy_metadata: Mapping[str, Any],
    ) -> "ShadowPollingPolicy":
        normalized_policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )

        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )

        normalized_adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        )

        normalized_base_interval = _require_positive_int(
            base_interval_seconds,
            "base_interval_seconds",
        )

        normalized_jitter = _require_non_negative_int(
            jitter_max_seconds,
            "jitter_max_seconds",
        )

        normalized_readiness_max_age = _require_positive_int(
            readiness_max_age_seconds,
            "readiness_max_age_seconds",
        )

        normalized_backoff_base = _require_positive_int(
            failure_backoff_base_seconds,
            "failure_backoff_base_seconds",
        )

        normalized_backoff_multiplier = _require_positive_int(
            failure_backoff_multiplier,
            "failure_backoff_multiplier",
        )

        if normalized_backoff_multiplier < 2:
            raise ShadowPollingPolicyContractError(
                "failure_backoff_multiplier must be at least 2"
            )

        normalized_backoff_max = _require_positive_int(
            failure_backoff_max_seconds,
            "failure_backoff_max_seconds",
        )

        if normalized_backoff_max < normalized_backoff_base:
            raise ShadowPollingPolicyContractError(
                "failure_backoff_max_seconds cannot be below "
                "failure_backoff_base_seconds"
            )

        normalized_suspend_threshold = _require_positive_int(
            consecutive_failure_suspend_threshold,
            "consecutive_failure_suspend_threshold",
        )

        normalized_cooldown = _require_positive_int(
            suspension_cooldown_seconds,
            "suspension_cooldown_seconds",
        )

        if not isinstance(
            explicit_restart_evidence_required,
            bool,
        ):
            raise ShadowPollingPolicyContractError(
                "explicit_restart_evidence_required must be bool"
            )

        immutable_metadata = _immutable_mapping(
            policy_metadata,
            "policy_metadata",
        )

        provisional = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            policy_id=normalized_policy_id,
            source_id=normalized_source_id,
            adapter_id=normalized_adapter_id,
            base_interval_seconds=normalized_base_interval,
            jitter_max_seconds=normalized_jitter,
            readiness_max_age_seconds=(
                normalized_readiness_max_age
            ),
            failure_backoff_base_seconds=(
                normalized_backoff_base
            ),
            failure_backoff_multiplier=(
                normalized_backoff_multiplier
            ),
            failure_backoff_max_seconds=(
                normalized_backoff_max
            ),
            consecutive_failure_suspend_threshold=(
                normalized_suspend_threshold
            ),
            suspension_cooldown_seconds=(
                normalized_cooldown
            ),
            explicit_restart_evidence_required=(
                explicit_restart_evidence_required
            ),
            shadow_mode_required=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            policy_metadata=immutable_metadata,
            policy_hash="",
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

        policy_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": POLLING_POLICY_RECORD_TYPE,
                "policy": provisional.to_canonical_dict(
                    include_policy_hash=False
                ),
            }
        )

        return cls(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            policy_id=provisional.policy_id,
            source_id=provisional.source_id,
            adapter_id=provisional.adapter_id,
            base_interval_seconds=(
                provisional.base_interval_seconds
            ),
            jitter_max_seconds=(
                provisional.jitter_max_seconds
            ),
            readiness_max_age_seconds=(
                provisional.readiness_max_age_seconds
            ),
            failure_backoff_base_seconds=(
                provisional.failure_backoff_base_seconds
            ),
            failure_backoff_multiplier=(
                provisional.failure_backoff_multiplier
            ),
            failure_backoff_max_seconds=(
                provisional.failure_backoff_max_seconds
            ),
            consecutive_failure_suspend_threshold=(
                provisional
                .consecutive_failure_suspend_threshold
            ),
            suspension_cooldown_seconds=(
                provisional.suspension_cooldown_seconds
            ),
            explicit_restart_evidence_required=(
                provisional
                .explicit_restart_evidence_required
            ),
            shadow_mode_required=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            policy_metadata=provisional.policy_metadata,
            policy_hash=policy_hash,
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

    def to_canonical_dict(
        self,
        *,
        include_policy_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "policy_id": self.policy_id,
            "source_id": self.source_id,
            "adapter_id": self.adapter_id,
            "base_interval_seconds": (
                self.base_interval_seconds
            ),
            "jitter_max_seconds": self.jitter_max_seconds,
            "readiness_max_age_seconds": (
                self.readiness_max_age_seconds
            ),
            "failure_backoff_base_seconds": (
                self.failure_backoff_base_seconds
            ),
            "failure_backoff_multiplier": (
                self.failure_backoff_multiplier
            ),
            "failure_backoff_max_seconds": (
                self.failure_backoff_max_seconds
            ),
            "consecutive_failure_suspend_threshold": (
                self.consecutive_failure_suspend_threshold
            ),
            "suspension_cooldown_seconds": (
                self.suspension_cooldown_seconds
            ),
            "explicit_restart_evidence_required": (
                self.explicit_restart_evidence_required
            ),
            "shadow_mode_required": self.shadow_mode_required,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "policy_metadata": _mapping_from_immutable(
                self.policy_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
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

        if include_policy_hash:
            result["policy_hash"] = self.policy_hash

        return result


@dataclass(frozen=True, slots=True)
class ShadowPollingState:
    schema_version: str
    engine_id: str
    state_id: str
    source_id: str
    adapter_id: str
    last_cycle_completed_at: datetime | None
    last_cycle_succeeded: bool | None
    consecutive_failures: int
    suspended: bool
    suspended_at: datetime | None
    restart_evidence_present: bool
    state_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    state_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @classmethod
    def create(
        cls,
        *,
        state_id: str,
        source_id: str,
        adapter_id: str,
        last_cycle_completed_at: datetime | None,
        last_cycle_succeeded: bool | None,
        consecutive_failures: int,
        suspended: bool,
        suspended_at: datetime | None,
        restart_evidence_present: bool,
        state_metadata: Mapping[str, Any],
    ) -> "ShadowPollingState":
        normalized_state_id = _require_non_empty_string(
            state_id,
            "state_id",
        )

        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )

        normalized_adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        )

        if last_cycle_completed_at is None:
            normalized_last_cycle_completed_at = None

        else:
            normalized_last_cycle_completed_at = (
                _require_aware_datetime(
                    last_cycle_completed_at,
                    "last_cycle_completed_at",
                )
            )

        if (
            last_cycle_succeeded is not None
            and not isinstance(last_cycle_succeeded, bool)
        ):
            raise ShadowPollingPolicyContractError(
                "last_cycle_succeeded must be bool or None"
            )

        normalized_failures = _require_non_negative_int(
            consecutive_failures,
            "consecutive_failures",
        )

        if not isinstance(suspended, bool):
            raise ShadowPollingPolicyContractError(
                "suspended must be bool"
            )

        if suspended_at is None:
            normalized_suspended_at = None

        else:
            normalized_suspended_at = _require_aware_datetime(
                suspended_at,
                "suspended_at",
            )

        if not isinstance(
            restart_evidence_present,
            bool,
        ):
            raise ShadowPollingPolicyContractError(
                "restart_evidence_present must be bool"
            )

        if suspended and normalized_suspended_at is None:
            raise ShadowPollingPolicyContractError(
                "suspended state requires suspended_at"
            )

        if (
            not suspended
            and normalized_suspended_at is not None
        ):
            raise ShadowPollingPolicyContractError(
                "non-suspended state cannot carry suspended_at"
            )

        if (
            normalized_last_cycle_completed_at is None
            and last_cycle_succeeded is not None
        ):
            raise ShadowPollingPolicyContractError(
                "last_cycle_succeeded requires "
                "last_cycle_completed_at"
            )

        if (
            normalized_last_cycle_completed_at is None
            and normalized_failures != 0
        ):
            raise ShadowPollingPolicyContractError(
                "consecutive_failures require "
                "last_cycle_completed_at"
            )

        if (
            last_cycle_succeeded is True
            and normalized_failures != 0
        ):
            raise ShadowPollingPolicyContractError(
                "successful last cycle requires zero "
                "consecutive_failures"
            )

        if (
            last_cycle_succeeded is False
            and normalized_failures < 1
        ):
            raise ShadowPollingPolicyContractError(
                "failed last cycle requires at least one "
                "consecutive failure"
            )

        immutable_metadata = _immutable_mapping(
            state_metadata,
            "state_metadata",
        )

        provisional = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            state_id=normalized_state_id,
            source_id=normalized_source_id,
            adapter_id=normalized_adapter_id,
            last_cycle_completed_at=(
                normalized_last_cycle_completed_at
            ),
            last_cycle_succeeded=last_cycle_succeeded,
            consecutive_failures=normalized_failures,
            suspended=suspended,
            suspended_at=normalized_suspended_at,
            restart_evidence_present=(
                restart_evidence_present
            ),
            state_metadata=immutable_metadata,
            state_hash="",
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

        state_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": POLLING_STATE_RECORD_TYPE,
                "state": provisional.to_canonical_dict(
                    include_state_hash=False
                ),
            }
        )

        return cls(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            state_id=provisional.state_id,
            source_id=provisional.source_id,
            adapter_id=provisional.adapter_id,
            last_cycle_completed_at=(
                provisional.last_cycle_completed_at
            ),
            last_cycle_succeeded=(
                provisional.last_cycle_succeeded
            ),
            consecutive_failures=(
                provisional.consecutive_failures
            ),
            suspended=provisional.suspended,
            suspended_at=provisional.suspended_at,
            restart_evidence_present=(
                provisional.restart_evidence_present
            ),
            state_metadata=provisional.state_metadata,
            state_hash=state_hash,
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

    def to_canonical_dict(
        self,
        *,
        include_state_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "state_id": self.state_id,
            "source_id": self.source_id,
            "adapter_id": self.adapter_id,
            "last_cycle_completed_at": (
                None
                if self.last_cycle_completed_at is None
                else self.last_cycle_completed_at.isoformat()
            ),
            "last_cycle_succeeded": (
                self.last_cycle_succeeded
            ),
            "consecutive_failures": self.consecutive_failures,
            "suspended": self.suspended,
            "suspended_at": (
                None
                if self.suspended_at is None
                else self.suspended_at.isoformat()
            ),
            "restart_evidence_present": (
                self.restart_evidence_present
            ),
            "state_metadata": _mapping_from_immutable(
                self.state_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
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

        if include_state_hash:
            result["state_hash"] = self.state_hash

        return result


@dataclass(frozen=True, slots=True)
class ShadowPollingDecision:
    schema_version: str
    engine_id: str
    decision_id: str
    decision_status: str
    policy_id: str
    policy_hash: str
    state_id: str
    state_hash: str
    readiness_id: str
    readiness_hash: str
    source_id: str
    adapter_id: str
    evaluated_at: datetime
    readiness_age_seconds: int
    readiness_fresh: bool
    base_interval_seconds: int
    deterministic_jitter_seconds: int
    failure_backoff_seconds: int
    effective_interval_seconds: int
    next_cycle_eligible_at: datetime | None
    cooldown_elapsed: bool
    restart_evidence_required: bool
    restart_evidence_present: bool
    failure_suspend_threshold_reached: bool
    safety_precedence_applied: bool
    shadow_cycle_allowed: bool
    continuous_polling_started: bool
    acquisition_invoked: bool
    persistence_invoked: bool
    alert_created: bool
    qseries_intake_record_created: bool
    reason_codes: tuple[str, ...]
    decision_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    decision_hash: str
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
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
        include_decision_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "decision_id": self.decision_id,
            "decision_status": self.decision_status,
            "policy_id": self.policy_id,
            "policy_hash": self.policy_hash,
            "state_id": self.state_id,
            "state_hash": self.state_hash,
            "readiness_id": self.readiness_id,
            "readiness_hash": self.readiness_hash,
            "source_id": self.source_id,
            "adapter_id": self.adapter_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "readiness_age_seconds": self.readiness_age_seconds,
            "readiness_fresh": self.readiness_fresh,
            "base_interval_seconds": (
                self.base_interval_seconds
            ),
            "deterministic_jitter_seconds": (
                self.deterministic_jitter_seconds
            ),
            "failure_backoff_seconds": (
                self.failure_backoff_seconds
            ),
            "effective_interval_seconds": (
                self.effective_interval_seconds
            ),
            "next_cycle_eligible_at": (
                None
                if self.next_cycle_eligible_at is None
                else self.next_cycle_eligible_at.isoformat()
            ),
            "cooldown_elapsed": self.cooldown_elapsed,
            "restart_evidence_required": (
                self.restart_evidence_required
            ),
            "restart_evidence_present": (
                self.restart_evidence_present
            ),
            "failure_suspend_threshold_reached": (
                self.failure_suspend_threshold_reached
            ),
            "safety_precedence_applied": (
                self.safety_precedence_applied
            ),
            "shadow_cycle_allowed": self.shadow_cycle_allowed,
            "continuous_polling_started": (
                self.continuous_polling_started
            ),
            "acquisition_invoked": self.acquisition_invoked,
            "persistence_invoked": self.persistence_invoked,
            "alert_created": self.alert_created,
            "qseries_intake_record_created": (
                self.qseries_intake_record_created
            ),
            "reason_codes": list(self.reason_codes),
            "decision_metadata": _mapping_from_immutable(
                self.decision_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
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

        if include_decision_hash:
            result["decision_hash"] = self.decision_hash

        return result


class OracleShadowPollingPolicyCadenceEngine:
    """
    Pure deterministic polling-policy state machine.

    Decision precedence:

    1. Existing suspended state.
    2. Failure threshold reached.
    3. Readiness freshness.
    4. Cadence/backoff timing.
    5. Eligibility.
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
        policy: ShadowPollingPolicy,
    ) -> None:
        if not isinstance(
            policy,
            ShadowPollingPolicy,
        ):
            raise ShadowPollingPolicyContractError(
                "policy must be ShadowPollingPolicy"
            )

        self._policy = policy

        self._assert_invariants()

    @property
    def policy(self) -> ShadowPollingPolicy:
        return self._policy

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
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

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise ShadowPollingPolicyInvariantError(
                "Oracle polling invariants violated"
            )

        if self._policy.read_only is not True:
            raise ShadowPollingPolicyInvariantError(
                "polling policy lost read_only invariant"
            )

        if self._policy.execution_allowed is not False:
            raise ShadowPollingPolicyInvariantError(
                "polling policy gained execution capability"
            )

        if self._policy.shadow_mode_required is not True:
            raise ShadowPollingPolicyInvariantError(
                "polling policy does not require shadow mode"
            )

        if self._policy.alerts_allowed is not False:
            raise ShadowPollingPolicyInvariantError(
                "polling policy gained alert capability"
            )

        if self._policy.qseries_intake_allowed is not False:
            raise ShadowPollingPolicyInvariantError(
                "polling policy gained Q Series intake capability"
            )

    def evaluate(
        self,
        *,
        readiness: KalshiLiveReadReadinessRecord,
        polling_state: ShadowPollingState,
        evaluated_at: datetime,
        decision_metadata: Mapping[str, Any],
    ) -> ShadowPollingDecision:
        self._assert_invariants()

        if not isinstance(
            readiness,
            KalshiLiveReadReadinessRecord,
        ):
            raise ShadowPollingPolicyContractError(
                "readiness must be "
                "KalshiLiveReadReadinessRecord"
            )

        if not isinstance(
            polling_state,
            ShadowPollingState,
        ):
            raise ShadowPollingPolicyContractError(
                "polling_state must be ShadowPollingState"
            )

        normalized_evaluated_at = _require_aware_datetime(
            evaluated_at,
            "evaluated_at",
        )

        immutable_decision_metadata = _immutable_mapping(
            decision_metadata,
            "decision_metadata",
        )

        self._validate_compatibility(
            readiness=readiness,
            polling_state=polling_state,
        )

        if normalized_evaluated_at < readiness.evaluated_at:
            raise ShadowPollingPolicyContractError(
                "polling evaluated_at cannot be before "
                "readiness evaluated_at"
            )

        readiness_age_seconds = int(
            (
                normalized_evaluated_at
                - readiness.evaluated_at
            ).total_seconds()
        )

        readiness_fresh = (
            readiness_age_seconds
            <= self._policy.readiness_max_age_seconds
        )

        deterministic_jitter_seconds = (
            self._deterministic_jitter_seconds(
                readiness=readiness,
                polling_state=polling_state,
            )
        )

        failure_backoff_seconds = (
            self._failure_backoff_seconds(
                consecutive_failures=(
                    polling_state.consecutive_failures
                )
            )
        )

        effective_interval_seconds = (
            self._policy.base_interval_seconds
            + deterministic_jitter_seconds
            + failure_backoff_seconds
        )

        if polling_state.last_cycle_completed_at is None:
            next_cycle_eligible_at = (
                normalized_evaluated_at
            )

        else:
            next_cycle_eligible_at = (
                polling_state.last_cycle_completed_at
                + timedelta(
                    seconds=effective_interval_seconds
                )
            )

        cooldown_elapsed = self._cooldown_elapsed(
            polling_state=polling_state,
            evaluated_at=normalized_evaluated_at,
        )

        failure_suspend_threshold_reached = (
            polling_state.consecutive_failures
            >= self._policy
            .consecutive_failure_suspend_threshold
        )

        (
            decision_status,
            shadow_cycle_allowed,
            reason_codes,
        ) = self._resolve_decision(
            readiness_fresh=readiness_fresh,
            polling_state=polling_state,
            evaluated_at=normalized_evaluated_at,
            next_cycle_eligible_at=next_cycle_eligible_at,
            cooldown_elapsed=cooldown_elapsed,
            failure_suspend_threshold_reached=(
                failure_suspend_threshold_reached
            ),
        )

        decision_id = "shadow_polling_decision." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "shadow_polling_decision_identity",
                "policy_hash": self._policy.policy_hash,
                "state_hash": polling_state.state_hash,
                "readiness_hash": readiness.readiness_hash,
                "evaluated_at": normalized_evaluated_at,
                "decision_metadata": (
                    _mapping_from_immutable(
                        immutable_decision_metadata
                    )
                ),
            }
        )

        provisional = ShadowPollingDecision(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            decision_id=decision_id,
            decision_status=decision_status,
            policy_id=self._policy.policy_id,
            policy_hash=self._policy.policy_hash,
            state_id=polling_state.state_id,
            state_hash=polling_state.state_hash,
            readiness_id=readiness.readiness_id,
            readiness_hash=readiness.readiness_hash,
            source_id=self._policy.source_id,
            adapter_id=self._policy.adapter_id,
            evaluated_at=normalized_evaluated_at,
            readiness_age_seconds=readiness_age_seconds,
            readiness_fresh=readiness_fresh,
            base_interval_seconds=(
                self._policy.base_interval_seconds
            ),
            deterministic_jitter_seconds=(
                deterministic_jitter_seconds
            ),
            failure_backoff_seconds=(
                failure_backoff_seconds
            ),
            effective_interval_seconds=(
                effective_interval_seconds
            ),
            next_cycle_eligible_at=(
                next_cycle_eligible_at
            ),
            cooldown_elapsed=cooldown_elapsed,
            restart_evidence_required=(
                self._policy
                .explicit_restart_evidence_required
            ),
            restart_evidence_present=(
                polling_state.restart_evidence_present
            ),
            failure_suspend_threshold_reached=(
                failure_suspend_threshold_reached
            ),
            safety_precedence_applied=True,
            shadow_cycle_allowed=shadow_cycle_allowed,
            continuous_polling_started=False,
            acquisition_invoked=False,
            persistence_invoked=False,
            alert_created=False,
            qseries_intake_record_created=False,
            reason_codes=reason_codes,
            decision_metadata=immutable_decision_metadata,
            decision_hash="",
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

        decision_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": POLLING_DECISION_RECORD_TYPE,
                "decision": provisional.to_canonical_dict(
                    include_decision_hash=False
                ),
            }
        )

        return ShadowPollingDecision(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            decision_id=provisional.decision_id,
            decision_status=provisional.decision_status,
            policy_id=provisional.policy_id,
            policy_hash=provisional.policy_hash,
            state_id=provisional.state_id,
            state_hash=provisional.state_hash,
            readiness_id=provisional.readiness_id,
            readiness_hash=provisional.readiness_hash,
            source_id=provisional.source_id,
            adapter_id=provisional.adapter_id,
            evaluated_at=provisional.evaluated_at,
            readiness_age_seconds=(
                provisional.readiness_age_seconds
            ),
            readiness_fresh=provisional.readiness_fresh,
            base_interval_seconds=(
                provisional.base_interval_seconds
            ),
            deterministic_jitter_seconds=(
                provisional.deterministic_jitter_seconds
            ),
            failure_backoff_seconds=(
                provisional.failure_backoff_seconds
            ),
            effective_interval_seconds=(
                provisional.effective_interval_seconds
            ),
            next_cycle_eligible_at=(
                provisional.next_cycle_eligible_at
            ),
            cooldown_elapsed=provisional.cooldown_elapsed,
            restart_evidence_required=(
                provisional.restart_evidence_required
            ),
            restart_evidence_present=(
                provisional.restart_evidence_present
            ),
            failure_suspend_threshold_reached=(
                provisional.failure_suspend_threshold_reached
            ),
            safety_precedence_applied=True,
            shadow_cycle_allowed=(
                provisional.shadow_cycle_allowed
            ),
            continuous_polling_started=False,
            acquisition_invoked=False,
            persistence_invoked=False,
            alert_created=False,
            qseries_intake_record_created=False,
            reason_codes=provisional.reason_codes,
            decision_metadata=provisional.decision_metadata,
            decision_hash=decision_hash,
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

    def _validate_compatibility(
        self,
        *,
        readiness: KalshiLiveReadReadinessRecord,
        polling_state: ShadowPollingState,
    ) -> None:
        if readiness.readiness_status != "passed":
            raise ShadowPollingPolicyCompatibilityError(
                "readiness status has not passed"
            )

        if readiness.source_id != self._policy.source_id:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness source identity mismatch"
            )

        if readiness.adapter_id != self._policy.adapter_id:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness adapter identity mismatch"
            )

        if polling_state.source_id != self._policy.source_id:
            raise ShadowPollingPolicyCompatibilityError(
                "polling-state source identity mismatch"
            )

        if polling_state.adapter_id != self._policy.adapter_id:
            raise ShadowPollingPolicyCompatibilityError(
                "polling-state adapter identity mismatch"
            )

        if readiness.source_contract_valid is not True:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness source contract is invalid"
            )

        if readiness.source_reachable is not True:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness source is not reachable"
            )

        if (
            readiness.source_control_acquisition_allowed
            is not True
        ):
            raise ShadowPollingPolicyCompatibilityError(
                "OLA-002 did not allow acquisition"
            )

        if (
            readiness.live_shadow_cycle_entry_ready
            is not True
        ):
            raise ShadowPollingPolicyCompatibilityError(
                "readiness does not permit shadow-cycle entry"
            )

        if readiness.shadow_mode is not True:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness left shadow mode"
            )

        if readiness.alerts_allowed is not False:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness gained alert capability"
            )

        if readiness.qseries_intake_allowed is not False:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness gained Q Series intake capability"
            )

        if readiness.continuous_polling_started is not False:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness unexpectedly started continuous polling"
            )

        if readiness.read_only is not True:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness lost read_only invariant"
            )

        if readiness.execution_allowed is not False:
            raise ShadowPollingPolicyCompatibilityError(
                "readiness gained execution capability"
            )

        if polling_state.read_only is not True:
            raise ShadowPollingPolicyCompatibilityError(
                "polling state lost read_only invariant"
            )

        if polling_state.execution_allowed is not False:
            raise ShadowPollingPolicyCompatibilityError(
                "polling state gained execution capability"
            )

    def _deterministic_jitter_seconds(
        self,
        *,
        readiness: KalshiLiveReadReadinessRecord,
        polling_state: ShadowPollingState,
    ) -> int:
        if self._policy.jitter_max_seconds == 0:
            return 0

        jitter_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "shadow_polling_jitter_seed",
                "policy_hash": self._policy.policy_hash,
                "readiness_hash": readiness.readiness_hash,
                "state_hash": polling_state.state_hash,
            }
        )

        return (
            int(
                jitter_hash[:16],
                16,
            )
            % (
                self._policy.jitter_max_seconds
                + 1
            )
        )

    def _failure_backoff_seconds(
        self,
        *,
        consecutive_failures: int,
    ) -> int:
        if consecutive_failures == 0:
            return 0

        exponent = consecutive_failures - 1

        calculated = (
            self._policy.failure_backoff_base_seconds
            * (
                self._policy.failure_backoff_multiplier
                ** exponent
            )
        )

        return min(
            calculated,
            self._policy.failure_backoff_max_seconds,
        )

    def _cooldown_elapsed(
        self,
        *,
        polling_state: ShadowPollingState,
        evaluated_at: datetime,
    ) -> bool:
        if not polling_state.suspended:
            return True

        if polling_state.suspended_at is None:
            raise ShadowPollingPolicyInvariantError(
                "suspended polling state lacks suspended_at"
            )

        restart_eligible_at = (
            polling_state.suspended_at
            + timedelta(
                seconds=(
                    self._policy.suspension_cooldown_seconds
                )
            )
        )

        return evaluated_at >= restart_eligible_at

    def _resolve_decision(
        self,
        *,
        readiness_fresh: bool,
        polling_state: ShadowPollingState,
        evaluated_at: datetime,
        next_cycle_eligible_at: datetime,
        cooldown_elapsed: bool,
        failure_suspend_threshold_reached: bool,
    ) -> tuple[
        str,
        bool,
        tuple[str, ...],
    ]:
        # PRIORITY 1:
        # Existing suspension state remains authoritative.
        if polling_state.suspended:
            if not cooldown_elapsed:
                return (
                    SUSPENDED_STATUS,
                    False,
                    (
                        "safety_precedence_existing_suspension",
                        "polling_suspended",
                        "suspension_cooldown_active",
                        "shadow_cycle_blocked",
                        "continuous_polling_not_started",
                    ),
                )

            if (
                self._policy
                .explicit_restart_evidence_required
                and not polling_state.restart_evidence_present
            ):
                return (
                    SUSPENDED_STATUS,
                    False,
                    (
                        "safety_precedence_existing_suspension",
                        "polling_suspended",
                        "suspension_cooldown_elapsed",
                        "explicit_restart_evidence_required",
                        "restart_evidence_missing",
                        "shadow_cycle_blocked",
                        "continuous_polling_not_started",
                    ),
                )

            if not readiness_fresh:
                return (
                    BLOCKED_STATUS,
                    False,
                    (
                        "safety_precedence_existing_suspension",
                        "suspension_cooldown_elapsed",
                        "restart_evidence_verified",
                        "readiness_stale",
                        "fresh_readiness_required_after_suspension",
                        "shadow_cycle_blocked",
                        "continuous_polling_not_started",
                    ),
                )

            return (
                ELIGIBLE_STATUS,
                True,
                (
                    "safety_precedence_existing_suspension",
                    "fresh_readiness_verified",
                    "suspension_cooldown_elapsed",
                    "restart_evidence_verified",
                    "shadow_cycle_eligible",
                    "continuous_polling_not_started",
                ),
            )

        # PRIORITY 2:
        # Failure threshold creates a suspension requirement even if
        # readiness has become stale.
        if failure_suspend_threshold_reached:
            return (
                SUSPENDED_STATUS,
                False,
                (
                    "safety_precedence_failure_threshold",
                    "failure_suspend_threshold_reached",
                    "polling_suspension_required",
                    "shadow_cycle_blocked",
                    "continuous_polling_not_started",
                ),
            )

        # PRIORITY 3:
        # Stale readiness blocks all non-suspended acquisition.
        if not readiness_fresh:
            return (
                BLOCKED_STATUS,
                False,
                (
                    "safety_precedence_readiness_freshness",
                    "readiness_stale",
                    "fresh_readiness_required",
                    "shadow_cycle_blocked",
                    "continuous_polling_not_started",
                ),
            )

        # PRIORITY 4:
        # Cadence and failure backoff must elapse.
        if evaluated_at < next_cycle_eligible_at:
            if polling_state.consecutive_failures > 0:
                return (
                    WAITING_STATUS,
                    False,
                    (
                        "fresh_readiness_verified",
                        "failure_backoff_active",
                        "shadow_cycle_waiting",
                        "continuous_polling_not_started",
                    ),
                )

            return (
                WAITING_STATUS,
                False,
                (
                    "fresh_readiness_verified",
                    "cadence_interval_active",
                    "shadow_cycle_waiting",
                    "continuous_polling_not_started",
                ),
            )

        # PRIORITY 5:
        # Fresh, unsuspended, timing-eligible source may enter one cycle.
        if polling_state.consecutive_failures > 0:
            return (
                ELIGIBLE_STATUS,
                True,
                (
                    "fresh_readiness_verified",
                    "failure_backoff_elapsed",
                    "failure_threshold_not_reached",
                    "shadow_cycle_eligible",
                    "continuous_polling_not_started",
                ),
            )

        return (
            ELIGIBLE_STATUS,
            True,
            (
                "fresh_readiness_verified",
                "base_cadence_elapsed",
                "deterministic_jitter_applied",
                "shadow_cycle_eligible",
                "continuous_polling_not_started",
            ),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ELIGIBLE_STATUS",
    "WAITING_STATUS",
    "SUSPENDED_STATUS",
    "BLOCKED_STATUS",
    "SUPPORTED_DECISION_STATUSES",
    "ShadowPollingPolicyContractError",
    "ShadowPollingPolicyCompatibilityError",
    "ShadowPollingPolicyInvariantError",
    "ShadowPollingPolicy",
    "ShadowPollingState",
    "ShadowPollingDecision",
    "OracleShadowPollingPolicyCadenceEngine",
    "canonical_json",
    "stable_hash",
]
