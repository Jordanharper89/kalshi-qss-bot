"""
OLA-007
Oracle Canonical Opportunity Alert Record Engine

Canonical immutable alert/opportunity output contract for Oracle.

Architecture:

CANONICAL OBSERVATIONS
    |
MARKET IDENTITY / VENUE RESOLUTION
    |
VALIDITY / EXPIRATION
    |
CROSS-VENUE COMPARISON
    |
CANONICAL OPPORTUNITY ALERT RECORD   <- OLA-007
    |
ORACLE ALERT DELIVERY
    |
Q SERIES INTAKE

Permanent rules:

- Alert records must reference a resolved OLA-006 comparison.
- No alert is created when no best opportunity exists.
- Tied best opportunities fail closed.
- Venue identity must be explicit.
- Venue-specific price and price unit must be explicit.
- Opportunity direction must be explicit.
- Opportunity expression type must be explicit.
- Date and time evidence must be explicit.
- valid_from and expires_at must be explicit.
- Alert freshness is evaluated using caller-supplied alert_created_at.
- Expired selections cannot create active alert records.
- Future-valid selections cannot create active alert records.
- Oracle may publish intelligence.
- Oracle may not authorize execution.
- Oracle may not resolve execution adapters.
- Oracle may not invoke execution adapters.
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


from .oracle_canonical_cross_venue_opportunity_comparison_engine import (
    CrossVenueOpportunityComparisonResult,
    RankedCrossVenueOpportunity,
)


SCHEMA_VERSION = "OLA-007"
ENGINE_ID = "OLA-007"

ALERT_RECORD_TYPE = "canonical_oracle_opportunity_alert_record"


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class OpportunityAlertContractError(ValueError):
    """Raised when canonical alert contract data is malformed."""


class OpportunityAlertSelectionError(
    OpportunityAlertContractError
):
    """Raised when a comparison cannot safely produce one alert."""


class OpportunityAlertInvariantError(RuntimeError):
    """Raised when permanent Oracle alert invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise OpportunityAlertContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise OpportunityAlertContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise OpportunityAlertContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OpportunityAlertContractError(
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
            raise OpportunityAlertContractError(
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
                raise OpportunityAlertContractError(
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

    raise OpportunityAlertContractError(
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
        raise OpportunityAlertContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise OpportunityAlertContractError(
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
class CanonicalOpportunityAlertRecord:
    schema_version: str
    engine_id: str
    alert_id: str
    opportunity_id: str
    thesis_id: str
    comparability_group_id: str
    canonical_market_id: str
    venue_id: str
    venue_name: str
    venue_type: str
    instrument_type: str
    opportunity_type: str
    expression_type: str
    direction: str
    reference_price: str
    price_unit: str
    normalized_score: str
    comparison_hash: str
    candidate_hash: str
    source_expires_at: datetime
    alert_created_at: datetime
    alert_date_utc: str
    alert_time_utc: str
    expiration_date_utc: str
    expiration_time_utc: str
    seconds_until_expiration: int
    alert_status: str
    freshness_status: str
    reason_codes: tuple[str, ...]
    display_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    alert_hash: str
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
        include_alert_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "alert_id": self.alert_id,
            "opportunity_id": self.opportunity_id,
            "thesis_id": self.thesis_id,
            "comparability_group_id": (
                self.comparability_group_id
            ),
            "canonical_market_id": (
                self.canonical_market_id
            ),
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "venue_type": self.venue_type,
            "instrument_type": self.instrument_type,
            "opportunity_type": self.opportunity_type,
            "expression_type": self.expression_type,
            "direction": self.direction,
            "reference_price": self.reference_price,
            "price_unit": self.price_unit,
            "normalized_score": self.normalized_score,
            "comparison_hash": self.comparison_hash,
            "candidate_hash": self.candidate_hash,
            "source_expires_at": (
                self.source_expires_at.isoformat()
            ),
            "alert_created_at": (
                self.alert_created_at.isoformat()
            ),
            "alert_date_utc": self.alert_date_utc,
            "alert_time_utc": self.alert_time_utc,
            "expiration_date_utc": (
                self.expiration_date_utc
            ),
            "expiration_time_utc": (
                self.expiration_time_utc
            ),
            "seconds_until_expiration": (
                self.seconds_until_expiration
            ),
            "alert_status": self.alert_status,
            "freshness_status": self.freshness_status,
            "reason_codes": list(self.reason_codes),
            "display_metadata": _mapping_from_immutable(
                self.display_metadata
            ),
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

        if include_alert_hash:
            result["alert_hash"] = self.alert_hash

        return result


class OracleCanonicalOpportunityAlertRecordEngine:
    """
    Produces one canonical Oracle alert record from a resolved comparison.

    This engine is intentionally downstream of OLA-006.

    It does not independently choose a venue.
    It does not independently score candidates.
    It does not resolve execution adapters.

    It freezes the OLA-006 winning intelligence into a canonical output
    record suitable for later delivery or Q Series intake.
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

    def __init__(self) -> None:
        self._assert_invariants()

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
            raise OpportunityAlertInvariantError(
                "Oracle alert invariants violated"
            )

    def create_alert(
        self,
        *,
        comparison: CrossVenueOpportunityComparisonResult,
        alert_created_at: datetime,
        display_metadata: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> CanonicalOpportunityAlertRecord:
        self._assert_invariants()

        if not isinstance(
            comparison,
            CrossVenueOpportunityComparisonResult,
        ):
            raise OpportunityAlertContractError(
                "comparison must be "
                "CrossVenueOpportunityComparisonResult"
            )

        normalized_alert_created_at = (
            _require_aware_datetime(
                alert_created_at,
                "alert_created_at",
            )
        )

        immutable_display_metadata = _immutable_mapping(
            display_metadata,
            "display_metadata",
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        selected = self._resolve_selected_candidate(
            comparison
        )

        if normalized_alert_created_at < comparison.compared_at:
            raise OpportunityAlertContractError(
                "alert_created_at cannot be before compared_at"
            )

        if normalized_alert_created_at >= selected.expires_at:
            raise OpportunityAlertSelectionError(
                "selected opportunity expired before alert creation"
            )

        seconds_until_expiration = int(
            (
                selected.expires_at
                - normalized_alert_created_at
            ).total_seconds()
        )

        if seconds_until_expiration <= 0:
            raise OpportunityAlertSelectionError(
                "selected opportunity has no remaining validity"
            )

        alert_id = "alert." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "oracle_alert_identity",
                "comparison_hash": comparison.comparison_hash,
                "opportunity_id": selected.opportunity_id,
                "candidate_hash": selected.candidate_hash,
                "alert_created_at": normalized_alert_created_at,
            }
        )

        reason_codes = (
            "best_opportunity_selected_from_comparison",
            "explicit_venue_identity_preserved",
            "venue_specific_price_preserved",
            "expiration_evidence_preserved",
            "canonical_alert_created",
        )

        provisional = CanonicalOpportunityAlertRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            alert_id=alert_id,
            opportunity_id=selected.opportunity_id,
            thesis_id=comparison.thesis_id,
            comparability_group_id=(
                comparison.comparability_group_id
            ),
            canonical_market_id=(
                selected.canonical_market_id
            ),
            venue_id=selected.venue_id,
            venue_name=selected.venue_name,
            venue_type=selected.venue_type,
            instrument_type=selected.instrument_type,
            opportunity_type=selected.opportunity_type,
            expression_type=selected.expression_type,
            direction=selected.direction,
            reference_price=selected.reference_price,
            price_unit=selected.price_unit,
            normalized_score=selected.normalized_score,
            comparison_hash=comparison.comparison_hash,
            candidate_hash=selected.candidate_hash,
            source_expires_at=selected.expires_at,
            alert_created_at=normalized_alert_created_at,
            alert_date_utc=(
                normalized_alert_created_at.date().isoformat()
            ),
            alert_time_utc=(
                normalized_alert_created_at.time().isoformat()
            ),
            expiration_date_utc=(
                selected.expires_at.date().isoformat()
            ),
            expiration_time_utc=(
                selected.expires_at.time().isoformat()
            ),
            seconds_until_expiration=(
                seconds_until_expiration
            ),
            alert_status="active",
            freshness_status="fresh",
            reason_codes=reason_codes,
            display_metadata=immutable_display_metadata,
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            alert_hash="",
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

        alert_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": ALERT_RECORD_TYPE,
                "alert": provisional.to_canonical_dict(
                    include_alert_hash=False
                ),
            }
        )

        return CanonicalOpportunityAlertRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            alert_id=provisional.alert_id,
            opportunity_id=provisional.opportunity_id,
            thesis_id=provisional.thesis_id,
            comparability_group_id=(
                provisional.comparability_group_id
            ),
            canonical_market_id=(
                provisional.canonical_market_id
            ),
            venue_id=provisional.venue_id,
            venue_name=provisional.venue_name,
            venue_type=provisional.venue_type,
            instrument_type=provisional.instrument_type,
            opportunity_type=provisional.opportunity_type,
            expression_type=provisional.expression_type,
            direction=provisional.direction,
            reference_price=provisional.reference_price,
            price_unit=provisional.price_unit,
            normalized_score=provisional.normalized_score,
            comparison_hash=provisional.comparison_hash,
            candidate_hash=provisional.candidate_hash,
            source_expires_at=provisional.source_expires_at,
            alert_created_at=provisional.alert_created_at,
            alert_date_utc=provisional.alert_date_utc,
            alert_time_utc=provisional.alert_time_utc,
            expiration_date_utc=(
                provisional.expiration_date_utc
            ),
            expiration_time_utc=(
                provisional.expiration_time_utc
            ),
            seconds_until_expiration=(
                provisional.seconds_until_expiration
            ),
            alert_status=provisional.alert_status,
            freshness_status=provisional.freshness_status,
            reason_codes=provisional.reason_codes,
            display_metadata=provisional.display_metadata,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            alert_hash=alert_hash,
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

    @staticmethod
    def _resolve_selected_candidate(
        comparison: CrossVenueOpportunityComparisonResult,
    ) -> RankedCrossVenueOpportunity:
        if comparison.comparison_status != (
            "best_opportunity_resolved"
        ):
            raise OpportunityAlertSelectionError(
                "comparison has no uniquely resolved best opportunity"
            )

        if comparison.tie_for_best is True:
            raise OpportunityAlertSelectionError(
                "tied best opportunity cannot produce one alert"
            )

        if comparison.best_opportunity_id is None:
            raise OpportunityAlertSelectionError(
                "comparison best_opportunity_id is missing"
            )

        if comparison.best_venue_id is None:
            raise OpportunityAlertSelectionError(
                "comparison best_venue_id is missing"
            )

        rank_one = [
            candidate
            for candidate in comparison.ranked_opportunities
            if candidate.rank == 1
        ]

        if len(rank_one) != 1:
            raise OpportunityAlertSelectionError(
                "comparison must contain exactly one rank-one candidate"
            )

        selected = rank_one[0]

        if (
            selected.opportunity_id
            != comparison.best_opportunity_id
        ):
            raise OpportunityAlertSelectionError(
                "rank-one opportunity does not match comparison best"
            )

        if selected.venue_id != comparison.best_venue_id:
            raise OpportunityAlertSelectionError(
                "rank-one venue does not match comparison best"
            )

        if (
            selected.reference_price
            != comparison.best_reference_price
        ):
            raise OpportunityAlertSelectionError(
                "rank-one price does not match comparison best"
            )

        if selected.price_unit != comparison.best_price_unit:
            raise OpportunityAlertSelectionError(
                "rank-one price unit does not match comparison best"
            )

        return selected


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OpportunityAlertContractError",
    "OpportunityAlertSelectionError",
    "OpportunityAlertInvariantError",
    "CanonicalOpportunityAlertRecord",
    "OracleCanonicalOpportunityAlertRecordEngine",
    "canonical_json",
    "stable_hash",
]
