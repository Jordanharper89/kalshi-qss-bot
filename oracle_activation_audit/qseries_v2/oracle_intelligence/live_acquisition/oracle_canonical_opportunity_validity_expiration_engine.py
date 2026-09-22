"""
OLA-005
Oracle Canonical Opportunity Validity and Expiration Engine

Canonical freshness, validity-window, and expiration evidence boundary
for Oracle read-only opportunity intelligence.

Architecture:

CANONICAL MARKET IDENTITY
    |
VERIFIED VENUE RESOLUTION
    |
CANONICAL OPPORTUNITY OBSERVATION
    |
VALIDITY / EXPIRATION EVIDENCE     <- OLA-005
    |
CROSS-VENUE COMPARISON
    |
ORACLE ALERT / OPPORTUNITY OUTPUT
    |
Q SERIES INTAKE

Permanent rules:

- Caller supplies all contract timestamps.
- Opportunity validity is explicit.
- valid_from is explicit.
- expires_at is explicit.
- observed_at is preserved.
- evaluated_at is caller supplied.
- Expired opportunities remain expired evidence.
- Future-dated validity fails closed.
- Invalid validity windows fail closed.
- No default expiration duration is silently invented.
- Oracle may classify freshness.
- Oracle may not authorize execution.
- Oracle may not select execution adapters.
- Q Series must later reject expired opportunities.
- Canonical stable hashing is used.
- repr() is never used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping


SCHEMA_VERSION = "OLA-005"
ENGINE_ID = "OLA-005"

OPPORTUNITY_VALIDITY_RECORD_TYPE = (
    "canonical_opportunity_validity_evidence"
)


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class OpportunityValidityContractError(ValueError):
    """Raised when opportunity validity contract data is malformed."""


class OpportunityValidityInvariantError(RuntimeError):
    """Raised when permanent no-execution invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise OpportunityValidityContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise OpportunityValidityContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise OpportunityValidityContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OpportunityValidityContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


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
            raise OpportunityValidityContractError(
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
                raise OpportunityValidityContractError(
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

    raise OpportunityValidityContractError(
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
        raise OpportunityValidityContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise OpportunityValidityContractError(
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
class OpportunityValidityRequest:
    opportunity_id: str
    canonical_market_id: str
    venue_id: str
    opportunity_type: str
    observed_at: datetime
    valid_from: datetime
    expires_at: datetime
    validity_policy_id: str
    source_record_hash: str
    metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    request_hash: str

    @classmethod
    def create(
        cls,
        *,
        opportunity_id: str,
        canonical_market_id: str,
        venue_id: str,
        opportunity_type: str,
        observed_at: datetime,
        valid_from: datetime,
        expires_at: datetime,
        validity_policy_id: str,
        source_record_hash: str,
        metadata: Mapping[str, Any],
    ) -> "OpportunityValidityRequest":
        normalized_opportunity_id = _require_non_empty_string(
            opportunity_id,
            "opportunity_id",
        )

        normalized_market_id = _require_non_empty_string(
            canonical_market_id,
            "canonical_market_id",
        )

        normalized_venue_id = _require_non_empty_string(
            venue_id,
            "venue_id",
        )

        normalized_opportunity_type = _require_non_empty_string(
            opportunity_type,
            "opportunity_type",
        )

        normalized_observed_at = _require_aware_datetime(
            observed_at,
            "observed_at",
        )

        normalized_valid_from = _require_aware_datetime(
            valid_from,
            "valid_from",
        )

        normalized_expires_at = _require_aware_datetime(
            expires_at,
            "expires_at",
        )

        normalized_policy_id = _require_non_empty_string(
            validity_policy_id,
            "validity_policy_id",
        )

        normalized_source_record_hash = _require_non_empty_string(
            source_record_hash,
            "source_record_hash",
        )

        if normalized_valid_from < normalized_observed_at:
            raise OpportunityValidityContractError(
                "valid_from cannot be before observed_at"
            )

        if normalized_expires_at <= normalized_valid_from:
            raise OpportunityValidityContractError(
                "expires_at must be after valid_from"
            )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "opportunity_validity_request",
            "opportunity_id": normalized_opportunity_id,
            "canonical_market_id": normalized_market_id,
            "venue_id": normalized_venue_id,
            "opportunity_type": normalized_opportunity_type,
            "observed_at": normalized_observed_at,
            "valid_from": normalized_valid_from,
            "expires_at": normalized_expires_at,
            "validity_policy_id": normalized_policy_id,
            "source_record_hash": (
                normalized_source_record_hash
            ),
            "metadata": _mapping_from_immutable(
                immutable_metadata
            ),
        }

        return cls(
            opportunity_id=normalized_opportunity_id,
            canonical_market_id=normalized_market_id,
            venue_id=normalized_venue_id,
            opportunity_type=normalized_opportunity_type,
            observed_at=normalized_observed_at,
            valid_from=normalized_valid_from,
            expires_at=normalized_expires_at,
            validity_policy_id=normalized_policy_id,
            source_record_hash=normalized_source_record_hash,
            metadata=immutable_metadata,
            request_hash=stable_hash(payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "opportunity_type": self.opportunity_type,
            "observed_at": self.observed_at.isoformat(),
            "valid_from": self.valid_from.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "validity_policy_id": self.validity_policy_id,
            "source_record_hash": self.source_record_hash,
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
            "request_hash": self.request_hash,
        }


@dataclass(frozen=True, slots=True)
class CanonicalOpportunityValidityEvidence:
    schema_version: str
    engine_id: str
    opportunity_id: str
    canonical_market_id: str
    venue_id: str
    opportunity_type: str
    observed_at: datetime
    valid_from: datetime
    expires_at: datetime
    evaluated_at: datetime
    observation_date_utc: str
    observation_time_utc: str
    expiration_date_utc: str
    expiration_time_utc: str
    validity_policy_id: str
    source_record_hash: str
    request_hash: str
    validity_status: str
    freshness_status: str
    reason_codes: tuple[str, ...]
    seconds_until_expiration: int
    active: bool
    expired: bool
    future_validity: bool
    validity_evidence_hash: str
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    immutable: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_validity_evidence_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "opportunity_id": self.opportunity_id,
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "opportunity_type": self.opportunity_type,
            "observed_at": self.observed_at.isoformat(),
            "valid_from": self.valid_from.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat(),
            "observation_date_utc": self.observation_date_utc,
            "observation_time_utc": self.observation_time_utc,
            "expiration_date_utc": self.expiration_date_utc,
            "expiration_time_utc": self.expiration_time_utc,
            "validity_policy_id": self.validity_policy_id,
            "source_record_hash": self.source_record_hash,
            "request_hash": self.request_hash,
            "validity_status": self.validity_status,
            "freshness_status": self.freshness_status,
            "reason_codes": list(self.reason_codes),
            "seconds_until_expiration": (
                self.seconds_until_expiration
            ),
            "active": self.active,
            "expired": self.expired,
            "future_validity": self.future_validity,
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "immutable": self.immutable,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
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

        if include_validity_evidence_hash:
            result["validity_evidence_hash"] = (
                self.validity_evidence_hash
            )

        return result


class OracleCanonicalOpportunityValidityExpirationEngine:
    """
    Evaluates explicit Oracle opportunity validity windows.

    This engine does not invent expiry durations.

    The caller must provide:
    - observed_at
    - valid_from
    - expires_at
    - evaluated_at

    Status model:

    PENDING
        evaluated_at < valid_from

    ACTIVE
        valid_from <= evaluated_at < expires_at

    EXPIRED
        evaluated_at >= expires_at

    Expiration boundary is closed at expires_at:
    evaluated_at == expires_at is EXPIRED.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    read_only = True
    execution_allowed = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(self) -> None:
        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
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
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise OpportunityValidityInvariantError(
                "Oracle validity invariants violated"
            )

    def evaluate(
        self,
        *,
        request: OpportunityValidityRequest,
        evaluated_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> CanonicalOpportunityValidityEvidence:
        self._assert_invariants()

        if not isinstance(
            request,
            OpportunityValidityRequest,
        ):
            raise OpportunityValidityContractError(
                "request must be OpportunityValidityRequest"
            )

        normalized_evaluated_at = _require_aware_datetime(
            evaluated_at,
            "evaluated_at",
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        if normalized_evaluated_at < request.valid_from:
            validity_status = "pending"
            freshness_status = "not_yet_valid"

            reason_codes = (
                "opportunity_not_yet_valid",
                "validity_window_pending",
            )

            active = False
            expired = False
            future_validity = True

        elif normalized_evaluated_at >= request.expires_at:
            validity_status = "expired"
            freshness_status = "expired"

            reason_codes = (
                "expiration_boundary_reached",
                "opportunity_expired",
            )

            active = False
            expired = True
            future_validity = False

        else:
            validity_status = "active"
            freshness_status = "fresh"

            reason_codes = (
                "opportunity_active",
                "within_validity_window",
            )

            active = True
            expired = False
            future_validity = False

        seconds_until_expiration = int(
            (
                request.expires_at
                - normalized_evaluated_at
            ).total_seconds()
        )

        provisional = CanonicalOpportunityValidityEvidence(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            opportunity_id=request.opportunity_id,
            canonical_market_id=(
                request.canonical_market_id
            ),
            venue_id=request.venue_id,
            opportunity_type=request.opportunity_type,
            observed_at=request.observed_at,
            valid_from=request.valid_from,
            expires_at=request.expires_at,
            evaluated_at=normalized_evaluated_at,
            observation_date_utc=(
                request.observed_at.date().isoformat()
            ),
            observation_time_utc=(
                request.observed_at.time().isoformat()
            ),
            expiration_date_utc=(
                request.expires_at.date().isoformat()
            ),
            expiration_time_utc=(
                request.expires_at.time().isoformat()
            ),
            validity_policy_id=(
                request.validity_policy_id
            ),
            source_record_hash=request.source_record_hash,
            request_hash=request.request_hash,
            validity_status=validity_status,
            freshness_status=freshness_status,
            reason_codes=reason_codes,
            seconds_until_expiration=(
                seconds_until_expiration
            ),
            active=active,
            expired=expired,
            future_validity=future_validity,
            validity_evidence_hash="",
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        evidence_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": OPPORTUNITY_VALIDITY_RECORD_TYPE,
                "evidence": (
                    provisional.to_canonical_dict(
                        include_validity_evidence_hash=False
                    )
                ),
            }
        )

        return CanonicalOpportunityValidityEvidence(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            opportunity_id=provisional.opportunity_id,
            canonical_market_id=(
                provisional.canonical_market_id
            ),
            venue_id=provisional.venue_id,
            opportunity_type=(
                provisional.opportunity_type
            ),
            observed_at=provisional.observed_at,
            valid_from=provisional.valid_from,
            expires_at=provisional.expires_at,
            evaluated_at=provisional.evaluated_at,
            observation_date_utc=(
                provisional.observation_date_utc
            ),
            observation_time_utc=(
                provisional.observation_time_utc
            ),
            expiration_date_utc=(
                provisional.expiration_date_utc
            ),
            expiration_time_utc=(
                provisional.expiration_time_utc
            ),
            validity_policy_id=(
                provisional.validity_policy_id
            ),
            source_record_hash=(
                provisional.source_record_hash
            ),
            request_hash=provisional.request_hash,
            validity_status=provisional.validity_status,
            freshness_status=provisional.freshness_status,
            reason_codes=provisional.reason_codes,
            seconds_until_expiration=(
                provisional.seconds_until_expiration
            ),
            active=provisional.active,
            expired=provisional.expired,
            future_validity=provisional.future_validity,
            validity_evidence_hash=evidence_hash,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            immutable=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OpportunityValidityContractError",
    "OpportunityValidityInvariantError",
    "OpportunityValidityRequest",
    "CanonicalOpportunityValidityEvidence",
    "OracleCanonicalOpportunityValidityExpirationEngine",
    "canonical_json",
    "stable_hash",
]
