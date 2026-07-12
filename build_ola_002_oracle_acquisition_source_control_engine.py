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
    / "oracle_acquisition_source_control_engine.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_002_oracle_acquisition_source_control_engine.py"
)


MODULE_CONTENT = r'''
"""
OLA-002
Oracle Acquisition Source Control Engine

Deterministic read-only source health and rate-control evidence boundary
for the Oracle live acquisition subsystem.

Architecture:

SOURCE
    |
SOURCE HEALTH / RATE CONTROL   <- OLA-002
    |
ACQUISITION                    <- OLA-001
    |
NORMALIZATION
    |
DEDUPLICATION
    |
CANONICAL OBSERVATION
    |
ORACLE ROUTING
    |
PERSISTENCE

This engine may:
- evaluate source health observations,
- evaluate deterministic rate-control state,
- enforce approved source-control policies,
- emit immutable OLA-001-compatible health evidence,
- emit immutable OLA-001-compatible rate-control evidence,
- emit immutable combined source-control records,
- preserve replay and audit metadata.

This engine may not:
- acquire source payloads,
- authorize trades,
- place orders,
- invoke execution adapters,
- move funds,
- mutate portfolios.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    AcquisitionContractError,
    AcquisitionInvariantError,
    JSONValue,
    RateControlEvidence,
    SourceHealthEvidence,
)


SCHEMA_VERSION = "OLA-002"
ENGINE_ID = "OLA-002"


class SourceControlContractError(ValueError):
    """Raised when source-control contract input is malformed."""


class SourceControlPolicyError(SourceControlContractError):
    """Raised when a source-control policy is invalid or unavailable."""


class SourceControlInvariantError(RuntimeError):
    """Raised when permanent source-control invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise SourceControlContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise SourceControlContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SourceControlContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise SourceControlContractError(
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
        raise SourceControlContractError(
            f"{field_name} must be greater than zero"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise SourceControlContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise SourceControlContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise SourceControlContractError(
                "non-finite float values are not canonical"
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
                raise SourceControlContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(value[key])

        return result

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    raise SourceControlContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise SourceControlContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise SourceControlContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    return tuple(
        (key, canonical[key])
        for key in sorted(canonical)
    )


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class SourceHealthPolicy:
    policy_id: str
    healthy_status: str
    unhealthy_status: str
    max_consecutive_failures: int
    max_latency_ms: int | None

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        healthy_status: str = "healthy",
        unhealthy_status: str = "unhealthy",
        max_consecutive_failures: int = 0,
        max_latency_ms: int | None = None,
    ) -> "SourceHealthPolicy":
        normalized_policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )
        normalized_healthy_status = _require_non_empty_string(
            healthy_status,
            "healthy_status",
        )
        normalized_unhealthy_status = _require_non_empty_string(
            unhealthy_status,
            "unhealthy_status",
        )

        if (
            normalized_healthy_status
            == normalized_unhealthy_status
        ):
            raise SourceControlPolicyError(
                "healthy_status and unhealthy_status must differ"
            )

        normalized_max_failures = _require_non_negative_int(
            max_consecutive_failures,
            "max_consecutive_failures",
        )

        normalized_max_latency: int | None = None

        if max_latency_ms is not None:
            normalized_max_latency = _require_positive_int(
                max_latency_ms,
                "max_latency_ms",
            )

        return cls(
            policy_id=normalized_policy_id,
            healthy_status=normalized_healthy_status,
            unhealthy_status=normalized_unhealthy_status,
            max_consecutive_failures=normalized_max_failures,
            max_latency_ms=normalized_max_latency,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "healthy_status": self.healthy_status,
            "unhealthy_status": self.unhealthy_status,
            "max_consecutive_failures": (
                self.max_consecutive_failures
            ),
            "max_latency_ms": self.max_latency_ms,
        }


@dataclass(frozen=True, slots=True)
class RateControlPolicy:
    policy_id: str
    max_requests_per_window: int
    window_seconds: int
    minimum_remaining_reserve: int

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        max_requests_per_window: int,
        window_seconds: int,
        minimum_remaining_reserve: int = 0,
    ) -> "RateControlPolicy":
        normalized_policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )
        normalized_max_requests = _require_positive_int(
            max_requests_per_window,
            "max_requests_per_window",
        )
        normalized_window_seconds = _require_positive_int(
            window_seconds,
            "window_seconds",
        )
        normalized_reserve = _require_non_negative_int(
            minimum_remaining_reserve,
            "minimum_remaining_reserve",
        )

        if normalized_reserve >= normalized_max_requests:
            raise SourceControlPolicyError(
                "minimum_remaining_reserve must be less than "
                "max_requests_per_window"
            )

        return cls(
            policy_id=normalized_policy_id,
            max_requests_per_window=normalized_max_requests,
            window_seconds=normalized_window_seconds,
            minimum_remaining_reserve=normalized_reserve,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "max_requests_per_window": (
                self.max_requests_per_window
            ),
            "window_seconds": self.window_seconds,
            "minimum_remaining_reserve": (
                self.minimum_remaining_reserve
            ),
        }


@dataclass(frozen=True, slots=True)
class SourceHealthObservation:
    source_id: str
    checked_at: datetime
    reachable: bool
    consecutive_failures: int
    latency_ms: int | None
    metadata: tuple[tuple[str, JSONValue], ...]
    observation_hash: str

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        checked_at: datetime,
        reachable: bool,
        consecutive_failures: int,
        latency_ms: int | None,
        metadata: Mapping[str, Any],
    ) -> "SourceHealthObservation":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )
        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        if not isinstance(reachable, bool):
            raise SourceControlContractError(
                "reachable must be a bool"
            )

        normalized_failures = _require_non_negative_int(
            consecutive_failures,
            "consecutive_failures",
        )

        normalized_latency: int | None = None

        if latency_ms is not None:
            normalized_latency = _require_non_negative_int(
                latency_ms,
                "latency_ms",
            )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "source_health_observation",
            "source_id": normalized_source_id,
            "checked_at": normalized_checked_at,
            "reachable": reachable,
            "consecutive_failures": normalized_failures,
            "latency_ms": normalized_latency,
            "metadata": _mapping_from_immutable(
                immutable_metadata
            ),
        }

        return cls(
            source_id=normalized_source_id,
            checked_at=normalized_checked_at,
            reachable=reachable,
            consecutive_failures=normalized_failures,
            latency_ms=normalized_latency,
            metadata=immutable_metadata,
            observation_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "checked_at": self.checked_at.isoformat(),
            "reachable": self.reachable,
            "consecutive_failures": (
                self.consecutive_failures
            ),
            "latency_ms": self.latency_ms,
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
            "observation_hash": self.observation_hash,
        }


@dataclass(frozen=True, slots=True)
class RateWindowObservation:
    source_id: str
    checked_at: datetime
    window_started_at: datetime
    requests_used: int
    metadata: tuple[tuple[str, JSONValue], ...]
    observation_hash: str

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        checked_at: datetime,
        window_started_at: datetime,
        requests_used: int,
        metadata: Mapping[str, Any],
    ) -> "RateWindowObservation":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )
        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )
        normalized_window_started_at = (
            _require_aware_datetime(
                window_started_at,
                "window_started_at",
            )
        )

        if normalized_window_started_at > normalized_checked_at:
            raise SourceControlContractError(
                "window_started_at cannot be after checked_at"
            )

        normalized_requests_used = _require_non_negative_int(
            requests_used,
            "requests_used",
        )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "rate_window_observation",
            "source_id": normalized_source_id,
            "checked_at": normalized_checked_at,
            "window_started_at": normalized_window_started_at,
            "requests_used": normalized_requests_used,
            "metadata": _mapping_from_immutable(
                immutable_metadata
            ),
        }

        return cls(
            source_id=normalized_source_id,
            checked_at=normalized_checked_at,
            window_started_at=normalized_window_started_at,
            requests_used=normalized_requests_used,
            metadata=immutable_metadata,
            observation_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "checked_at": self.checked_at.isoformat(),
            "window_started_at": (
                self.window_started_at.isoformat()
            ),
            "requests_used": self.requests_used,
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
            "observation_hash": self.observation_hash,
        }


@dataclass(frozen=True, slots=True)
class SourceControlDecisionRecord:
    schema_version: str
    engine_id: str
    source_id: str
    evaluated_at: datetime
    health_policy_id: str
    rate_policy_id: str
    health_observation_hash: str
    rate_observation_hash: str
    health_evidence: SourceHealthEvidence
    rate_control_evidence: RateControlEvidence
    acquisition_allowed: bool
    reason_codes: tuple[str, ...]
    replay_metadata: tuple[tuple[str, JSONValue], ...]
    audit_metadata: tuple[tuple[str, JSONValue], ...]
    decision_hash: str
    read_only: bool
    execution_allowed: bool
    acquisition_performed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
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
            "source_id": self.source_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "health_policy_id": self.health_policy_id,
            "rate_policy_id": self.rate_policy_id,
            "health_observation_hash": (
                self.health_observation_hash
            ),
            "rate_observation_hash": (
                self.rate_observation_hash
            ),
            "health_evidence": (
                self.health_evidence.to_canonical_dict()
            ),
            "rate_control_evidence": (
                self.rate_control_evidence.to_canonical_dict()
            ),
            "acquisition_allowed": self.acquisition_allowed,
            "reason_codes": list(self.reason_codes),
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "acquisition_performed": self.acquisition_performed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_decision_hash:
            result["decision_hash"] = self.decision_hash

        return result


class OracleAcquisitionSourceControlEngine:
    """
    Deterministic source health and rate-control evaluator.

    Fail-closed rules:
    - only registered source policy pairs may be evaluated,
    - health and rate observations must identify the same source,
    - caller-supplied evaluated_at controls deterministic evidence time,
    - future observations relative to evaluated_at are rejected,
    - stale rate windows are rejected,
    - request counts beyond policy maximum are denied,
    - health failures deny acquisition,
    - latency policy breaches deny acquisition,
    - reserve-boundary breaches deny acquisition.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True
    execution_allowed = False
    acquisition_performed = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        source_policies: Mapping[
            str,
            tuple[
                SourceHealthPolicy,
                RateControlPolicy,
            ],
        ],
    ) -> None:
        if not isinstance(source_policies, Mapping):
            raise SourceControlContractError(
                "source_policies must be a mapping"
            )

        normalized_policies: dict[
            str,
            tuple[
                SourceHealthPolicy,
                RateControlPolicy,
            ],
        ] = {}

        for source_id, policy_pair in source_policies.items():
            normalized_source_id = _require_non_empty_string(
                source_id,
                "source policy source_id",
            )

            if (
                not isinstance(policy_pair, tuple)
                or len(policy_pair) != 2
            ):
                raise SourceControlPolicyError(
                    "source policy value must be "
                    "(SourceHealthPolicy, RateControlPolicy)"
                )

            health_policy, rate_policy = policy_pair

            if not isinstance(
                health_policy,
                SourceHealthPolicy,
            ):
                raise SourceControlPolicyError(
                    "invalid SourceHealthPolicy"
                )

            if not isinstance(
                rate_policy,
                RateControlPolicy,
            ):
                raise SourceControlPolicyError(
                    "invalid RateControlPolicy"
                )

            normalized_policies[normalized_source_id] = (
                health_policy,
                rate_policy,
            )

        if not normalized_policies:
            raise SourceControlPolicyError(
                "at least one source policy pair is required"
            )

        self._source_policies = normalized_policies

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        invariants = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "acquisition_performed": self.acquisition_performed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "acquisition_performed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if invariants != expected:
            raise SourceControlInvariantError(
                "Oracle source-control invariants violated"
            )

    @property
    def approved_source_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._source_policies))

    def evaluate(
        self,
        *,
        health_observation: SourceHealthObservation,
        rate_observation: RateWindowObservation,
        evaluated_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> SourceControlDecisionRecord:
        self._assert_invariants()

        if not isinstance(
            health_observation,
            SourceHealthObservation,
        ):
            raise SourceControlContractError(
                "health_observation must be "
                "SourceHealthObservation"
            )

        if not isinstance(
            rate_observation,
            RateWindowObservation,
        ):
            raise SourceControlContractError(
                "rate_observation must be RateWindowObservation"
            )

        normalized_evaluated_at = _require_aware_datetime(
            evaluated_at,
            "evaluated_at",
        )

        if (
            health_observation.source_id
            != rate_observation.source_id
        ):
            raise SourceControlContractError(
                "health and rate observations must identify "
                "the same source"
            )

        source_id = health_observation.source_id

        policy_pair = self._source_policies.get(source_id)

        if policy_pair is None:
            raise SourceControlPolicyError(
                f"source is not approved for control evaluation: "
                f"{source_id}"
            )

        health_policy, rate_policy = policy_pair

        if health_observation.checked_at > normalized_evaluated_at:
            raise SourceControlContractError(
                "health observation cannot be from the future "
                "relative to evaluated_at"
            )

        if rate_observation.checked_at > normalized_evaluated_at:
            raise SourceControlContractError(
                "rate observation cannot be from the future "
                "relative to evaluated_at"
            )

        window_age_seconds = int(
            (
                rate_observation.checked_at
                - rate_observation.window_started_at
            ).total_seconds()
        )

        if window_age_seconds >= rate_policy.window_seconds:
            raise SourceControlContractError(
                "rate observation describes an expired rate window"
            )

        health_allowed, health_reasons = (
            self._evaluate_health(
                health_observation=health_observation,
                health_policy=health_policy,
            )
        )

        rate_allowed, rate_reasons, remaining = (
            self._evaluate_rate(
                rate_observation=rate_observation,
                rate_policy=rate_policy,
            )
        )

        acquisition_allowed = health_allowed and rate_allowed

        reason_codes = tuple(
            sorted(
                set(
                    health_reasons
                    + rate_reasons
                    + (
                        ["acquisition_allowed"]
                        if acquisition_allowed
                        else ["acquisition_blocked"]
                    )
                )
            )
        )

        health_evidence = SourceHealthEvidence.create(
            source_id=source_id,
            status=(
                health_policy.healthy_status
                if health_allowed
                else health_policy.unhealthy_status
            ),
            checked_at=normalized_evaluated_at,
            details={
                "health_policy_id": health_policy.policy_id,
                "health_observation_hash": (
                    health_observation.observation_hash
                ),
                "reachable": health_observation.reachable,
                "consecutive_failures": (
                    health_observation.consecutive_failures
                ),
                "latency_ms": health_observation.latency_ms,
                "reason_codes": sorted(health_reasons),
            },
        )

        rate_control_evidence = RateControlEvidence.create(
            source_id=source_id,
            allowed=rate_allowed,
            checked_at=normalized_evaluated_at,
            policy_id=rate_policy.policy_id,
            details={
                "rate_observation_hash": (
                    rate_observation.observation_hash
                ),
                "window_started_at": (
                    rate_observation.window_started_at
                ),
                "requests_used": rate_observation.requests_used,
                "max_requests_per_window": (
                    rate_policy.max_requests_per_window
                ),
                "minimum_remaining_reserve": (
                    rate_policy.minimum_remaining_reserve
                ),
                "remaining": remaining,
                "reason_codes": sorted(rate_reasons),
            },
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )
        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        provisional = SourceControlDecisionRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            source_id=source_id,
            evaluated_at=normalized_evaluated_at,
            health_policy_id=health_policy.policy_id,
            rate_policy_id=rate_policy.policy_id,
            health_observation_hash=(
                health_observation.observation_hash
            ),
            rate_observation_hash=(
                rate_observation.observation_hash
            ),
            health_evidence=health_evidence,
            rate_control_evidence=rate_control_evidence,
            acquisition_allowed=acquisition_allowed,
            reason_codes=reason_codes,
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            decision_hash="",
            read_only=True,
            execution_allowed=False,
            acquisition_performed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        decision_hash = stable_hash(
            provisional.to_canonical_dict(
                include_decision_hash=False
            )
        )

        return SourceControlDecisionRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            source_id=provisional.source_id,
            evaluated_at=provisional.evaluated_at,
            health_policy_id=provisional.health_policy_id,
            rate_policy_id=provisional.rate_policy_id,
            health_observation_hash=(
                provisional.health_observation_hash
            ),
            rate_observation_hash=(
                provisional.rate_observation_hash
            ),
            health_evidence=provisional.health_evidence,
            rate_control_evidence=(
                provisional.rate_control_evidence
            ),
            acquisition_allowed=provisional.acquisition_allowed,
            reason_codes=provisional.reason_codes,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            decision_hash=decision_hash,
            read_only=True,
            execution_allowed=False,
            acquisition_performed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    @staticmethod
    def _evaluate_health(
        *,
        health_observation: SourceHealthObservation,
        health_policy: SourceHealthPolicy,
    ) -> tuple[bool, list[str]]:
        reasons: list[str] = []

        if health_observation.reachable:
            reasons.append("source_reachable")
        else:
            reasons.append("source_unreachable")

        failures_allowed = (
            health_observation.consecutive_failures
            <= health_policy.max_consecutive_failures
        )

        if failures_allowed:
            reasons.append(
                "consecutive_failures_within_policy"
            )
        else:
            reasons.append(
                "consecutive_failures_exceeded"
            )

        latency_allowed = True

        if health_policy.max_latency_ms is not None:
            if health_observation.latency_ms is None:
                latency_allowed = False
                reasons.append(
                    "latency_required_but_missing"
                )
            elif (
                health_observation.latency_ms
                > health_policy.max_latency_ms
            ):
                latency_allowed = False
                reasons.append("latency_policy_exceeded")
            else:
                reasons.append("latency_within_policy")
        else:
            reasons.append("latency_policy_not_required")

        allowed = (
            health_observation.reachable
            and failures_allowed
            and latency_allowed
        )

        return allowed, reasons

    @staticmethod
    def _evaluate_rate(
        *,
        rate_observation: RateWindowObservation,
        rate_policy: RateControlPolicy,
    ) -> tuple[bool, list[str], int]:
        reasons: list[str] = []

        remaining = (
            rate_policy.max_requests_per_window
            - rate_observation.requests_used
        )

        if rate_observation.requests_used > (
            rate_policy.max_requests_per_window
        ):
            reasons.append("rate_limit_exceeded")
            return False, reasons, remaining

        reasons.append("rate_usage_within_limit")

        acquisition_remaining = remaining - 1

        if acquisition_remaining < (
            rate_policy.minimum_remaining_reserve
        ):
            reasons.append("rate_reserve_boundary_blocked")
            return False, reasons, remaining

        reasons.append("rate_reserve_preserved")

        return True, reasons, remaining


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SourceControlContractError",
    "SourceControlPolicyError",
    "SourceControlInvariantError",
    "SourceHealthPolicy",
    "RateControlPolicy",
    "SourceHealthObservation",
    "RateWindowObservation",
    "SourceControlDecisionRecord",
    "OracleAcquisitionSourceControlEngine",
    "canonical_json",
    "stable_hash",
]
'''


PACKAGE_INIT_CONTENT = r'''
"""
Oracle live read-only acquisition subsystem.
"""

from .oracle_live_read_only_acquisition_runtime import (
    AcquisitionBatchRecord,
    AcquisitionContractError,
    AcquisitionInvariantError,
    AcquisitionObservationRecord,
    ApprovedReadOnlySourceAdapter,
    ApprovedSourceAdapterRegistration,
    CanonicalObservation,
    CanonicalObservationRouterFailure,
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlEvidence,
    RawSourceObservation,
    SourceAdapterFailure,
    SourceHealthEvidence,
    UnapprovedSourceAdapterError,
)

from .oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceControlContractError,
    SourceControlDecisionRecord,
    SourceControlInvariantError,
    SourceControlPolicyError,
    SourceHealthObservation,
    SourceHealthPolicy,
)

__all__ = [
    "AcquisitionBatchRecord",
    "AcquisitionContractError",
    "AcquisitionInvariantError",
    "AcquisitionObservationRecord",
    "ApprovedReadOnlySourceAdapter",
    "ApprovedSourceAdapterRegistration",
    "CanonicalObservation",
    "CanonicalObservationRouterFailure",
    "DeduplicationEvidence",
    "ObservationRoutingEvidence",
    "OracleLiveReadOnlyAcquisitionRuntime",
    "RateControlEvidence",
    "RawSourceObservation",
    "SourceAdapterFailure",
    "SourceHealthEvidence",
    "UnapprovedSourceAdapterError",
    "OracleAcquisitionSourceControlEngine",
    "RateControlPolicy",
    "RateWindowObservation",
    "SourceControlContractError",
    "SourceControlDecisionRecord",
    "SourceControlInvariantError",
    "SourceControlPolicyError",
    "SourceHealthObservation",
    "SourceHealthPolicy",
]
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceControlContractError,
    SourceControlPolicyError,
    SourceHealthObservation,
    SourceHealthPolicy,
)


EVALUATED_AT = datetime(
    2026,
    7,
    11,
    21,
    0,
    0,
    tzinfo=timezone.utc,
)

CHECKED_AT = datetime(
    2026,
    7,
    11,
    20,
    59,
    55,
    tzinfo=timezone.utc,
)

WINDOW_STARTED_AT = datetime(
    2026,
    7,
    11,
    20,
    59,
    0,
    tzinfo=timezone.utc,
)


def build_engine():
    health_policy = SourceHealthPolicy.create(
        policy_id="health.test.market.v1",
        healthy_status="healthy",
        unhealthy_status="unhealthy",
        max_consecutive_failures=0,
        max_latency_ms=250,
    )

    rate_policy = RateControlPolicy.create(
        policy_id="rate.test.market.v1",
        max_requests_per_window=100,
        window_seconds=60,
        minimum_remaining_reserve=5,
    )

    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.test.market": (
                health_policy,
                rate_policy,
            ),
        }
    )


def build_healthy_observation():
    return SourceHealthObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        reachable=True,
        consecutive_failures=0,
        latency_ms=42,
        metadata={
            "probe_id": "probe-test-1",
            "transport": "https",
        },
    )


def build_rate_observation(
    *,
    requests_used=20,
):
    return RateWindowObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        window_started_at=WINDOW_STARTED_AT,
        requests_used=requests_used,
        metadata={
            "counter_id": "counter-test-1",
        },
    )


def run_primary_contract_test():
    engine = build_engine()

    first = engine.evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={
            "replay_source": "source_control",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-002",
            "operator": "automated_runtime",
        },
    )

    second = build_engine().evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={
            "replay_source": "source_control",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-002",
            "operator": "automated_runtime",
        },
    )

    assert first == second
    assert first.decision_hash == second.decision_hash

    assert first.schema_version == "OLA-002"
    assert first.engine_id == "OLA-002"
    assert first.source_id == "source.test.market"

    assert first.acquisition_allowed is True

    assert (
        first.health_evidence.status
        == "healthy"
    )

    assert (
        first.rate_control_evidence.allowed
        is True
    )

    assert (
        first.health_evidence.source_id
        == "source.test.market"
    )

    assert (
        first.rate_control_evidence.source_id
        == "source.test.market"
    )

    assert first.read_only is True
    assert first.execution_allowed is False
    assert first.acquisition_performed is False
    assert (
        first.trade_authorization_allowed
        is False
    )
    assert first.order_placement_allowed is False
    assert (
        first.execution_adapter_invocation_allowed
        is False
    )
    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    assert "acquisition_allowed" in first.reason_codes
    assert "source_reachable" in first.reason_codes
    assert "latency_within_policy" in first.reason_codes
    assert "rate_reserve_preserved" in first.reason_codes

    try:
        first.acquisition_allowed = False
        raise AssertionError(
            "SourceControlDecisionRecord must be immutable"
        )
    except FrozenInstanceError:
        pass

    return first


def run_health_block_test():
    engine = build_engine()

    unhealthy = SourceHealthObservation.create(
        source_id="source.test.market",
        checked_at=CHECKED_AT,
        reachable=False,
        consecutive_failures=1,
        latency_ms=None,
        metadata={},
    )

    result = engine.evaluate(
        health_observation=unhealthy,
        rate_observation=build_rate_observation(),
        evaluated_at=EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.acquisition_allowed is False
    assert result.health_evidence.status == "unhealthy"
    assert "source_unreachable" in result.reason_codes
    assert "acquisition_blocked" in result.reason_codes


def run_rate_block_test():
    engine = build_engine()

    result = engine.evaluate(
        health_observation=build_healthy_observation(),
        rate_observation=build_rate_observation(
            requests_used=95
        ),
        evaluated_at=EVALUATED_AT,
        replay_metadata={},
        audit_metadata={},
    )

    assert result.acquisition_allowed is False
    assert result.rate_control_evidence.allowed is False
    assert (
        "rate_reserve_boundary_blocked"
        in result.reason_codes
    )
    assert "acquisition_blocked" in result.reason_codes


def run_fail_closed_tests():
    engine = build_engine()

    mismatched_rate = RateWindowObservation.create(
        source_id="source.other.market",
        checked_at=CHECKED_AT,
        window_started_at=WINDOW_STARTED_AT,
        requests_used=1,
        metadata={},
    )

    try:
        engine.evaluate(
            health_observation=build_healthy_observation(),
            rate_observation=mismatched_rate,
            evaluated_at=EVALUATED_AT,
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "source identity mismatch must fail closed"
        )
    except SourceControlContractError:
        pass

    expired_window = RateWindowObservation.create(
        source_id="source.test.market",
        checked_at=EVALUATED_AT,
        window_started_at=datetime(
            2026,
            7,
            11,
            20,
            58,
            59,
            tzinfo=timezone.utc,
        ),
        requests_used=1,
        metadata={},
    )

    try:
        engine.evaluate(
            health_observation=build_healthy_observation(),
            rate_observation=expired_window,
            evaluated_at=EVALUATED_AT,
            replay_metadata={},
            audit_metadata={},
        )
        raise AssertionError(
            "expired rate windows must fail closed"
        )
    except SourceControlContractError:
        pass

    try:
        SourceHealthPolicy.create(
            policy_id="bad.health.policy",
            healthy_status="same",
            unhealthy_status="same",
        )
        raise AssertionError(
            "identical health statuses must fail closed"
        )
    except SourceControlPolicyError:
        pass

    try:
        RateControlPolicy.create(
            policy_id="bad.rate.policy",
            max_requests_per_window=10,
            window_seconds=60,
            minimum_remaining_reserve=10,
        )
        raise AssertionError(
            "invalid reserve policy must fail closed"
        )
    except SourceControlPolicyError:
        pass

    try:
        SourceHealthObservation.create(
            source_id="source.test.market",
            checked_at=datetime(
                2026,
                7,
                11,
                20,
                0,
                0,
            ),
            reachable=True,
            consecutive_failures=0,
            latency_ms=1,
            metadata={},
        )
        raise AssertionError(
            "naive timestamps must fail closed"
        )
    except SourceControlContractError:
        pass


def main():
    result = run_primary_contract_test()
    run_health_block_test()
    run_rate_block_test()
    run_fail_closed_tests()

    output = {
        "schema_version": result.schema_version,
        "engine_id": result.engine_id,
        "source_id": result.source_id,
        "acquisition_allowed": result.acquisition_allowed,
        "health_status": result.health_evidence.status,
        "rate_allowed": (
            result.rate_control_evidence.allowed
        ),
        "reason_codes": list(result.reason_codes),
        "read_only": result.read_only,
        "execution_allowed": result.execution_allowed,
        "acquisition_performed": (
            result.acquisition_performed
        ),
        "trade_authorization_allowed": (
            result.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            result.order_placement_allowed
        ),
        "execution_adapter_invocation_allowed": (
            result.execution_adapter_invocation_allowed
        ),
        "funds_moved": result.funds_moved,
        "portfolio_mutated": result.portfolio_mutated,
    }

    print(
        "[PASS] OLA-002 "
        "Oracle Acquisition Source Control Engine"
    )
    print(output)


if __name__ == "__main__":
    main()
'''


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


def main() -> None:
    print("========================================")
    print(" OLA-002 INSTALLER")
    print(" Oracle Acquisition Source Control Engine")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        PACKAGE_INIT_PATH,
        PACKAGE_INIT_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print("[DONE] OLA-002 installed")
    print()
    print("Run:")
    print(
        "py test_ola_002_"
        "oracle_acquisition_source_control_engine.py"
    )


if __name__ == "__main__":
    main()