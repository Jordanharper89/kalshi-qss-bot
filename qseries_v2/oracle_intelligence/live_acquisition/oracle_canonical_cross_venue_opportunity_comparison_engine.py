"""
OLA-006
Oracle Canonical Cross-Venue Opportunity Comparison Engine

Canonical read-only comparison and ranking boundary for verified Oracle
opportunities across approved venues.

Architecture:

CANONICAL OBSERVATIONS
    |
CANONICAL MARKET IDENTITY
    |
VERIFIED VENUE RESOLUTION
    |
VALIDITY / EXPIRATION EVIDENCE
    |
CANONICAL COMPARABILITY CONTRACT
    |
CROSS-VENUE OPPORTUNITY COMPARISON   <- OLA-006
    |
RANKED ORACLE INTELLIGENCE
    |
ORACLE ALERT / OPPORTUNITY OUTPUT
    |
Q SERIES INTAKE

Permanent rules:

- Oracle may compare verified active opportunities.
- Oracle may rank venues as intelligence.
- Oracle may identify the strongest opportunity expression.
- Oracle may not resolve execution adapters.
- Oracle may not authorize trades.
- Oracle may not place orders.
- Raw prices from unlike instruments are never compared directly.
- Prediction share price is not directly comparable to spot asset price.
- A canonical thesis_id is required.
- A canonical comparability_group_id is required.
- Caller-supplied normalized scoring evidence is required.
- Scoring component weights are explicit.
- Scoring component values are explicit.
- Missing scoring components fail closed.
- Extra scoring components fail closed.
- Score ties remain explicit.
- Expired opportunities are ineligible.
- Pending opportunities are ineligible.
- Unverified venues are ineligible.
- No default venue exists.
- No fallback execution adapter exists.
- Caller supplies comparison timestamps.
- Canonical stable hashing is used.
- repr() is never used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "OLA-006"
ENGINE_ID = "OLA-006"

COMPARISON_CANDIDATE_RECORD_TYPE = (
    "canonical_cross_venue_comparison_candidate"
)

COMPARISON_RESULT_RECORD_TYPE = (
    "canonical_cross_venue_comparison_result"
)


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class OpportunityComparisonContractError(ValueError):
    """Raised when comparison contract data is malformed."""


class OpportunityComparabilityError(
    OpportunityComparisonContractError
):
    """Raised when candidates cannot safely be compared."""


class OpportunityComparisonInvariantError(RuntimeError):
    """Raised when permanent no-execution invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise OpportunityComparisonContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise OpportunityComparisonContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise OpportunityComparisonContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OpportunityComparisonContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_bool(
    value: Any,
    field_name: str,
) -> bool:
    if not isinstance(value, bool):
        raise OpportunityComparisonContractError(
            f"{field_name} must be a bool"
        )

    return value


def _require_decimal(
    value: Any,
    field_name: str,
) -> Decimal:
    if isinstance(value, bool):
        raise OpportunityComparisonContractError(
            f"{field_name} must be decimal-compatible"
        )

    try:
        normalized = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise OpportunityComparisonContractError(
            f"{field_name} must be decimal-compatible"
        ) from exc

    if not normalized.is_finite():
        raise OpportunityComparisonContractError(
            f"{field_name} must be finite"
        )

    return normalized


def _canonical_decimal(
    value: Decimal,
) -> str:
    if not value.is_finite():
        raise OpportunityComparisonContractError(
            "non-finite Decimal values are not canonical"
        )

    return format(value, "f")


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
            raise OpportunityComparisonContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, Decimal):
        return _canonical_decimal(value)

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
                raise OpportunityComparisonContractError(
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

    raise OpportunityComparisonContractError(
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
        raise OpportunityComparisonContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise OpportunityComparisonContractError(
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


def _immutable_decimal_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        raise OpportunityComparisonContractError(
            f"{field_name} must be a mapping"
        )

    normalized: dict[str, str] = {}

    for key, item in value.items():
        normalized_key = _require_non_empty_string(
            key,
            f"{field_name} key",
        )

        decimal_value = _require_decimal(
            item,
            f"{field_name}.{normalized_key}",
        )

        normalized[normalized_key] = _canonical_decimal(
            decimal_value
        )

    return tuple(
        (key, normalized[key])
        for key in sorted(normalized)
    )


def _decimal_mapping_from_immutable(
    value: tuple[tuple[str, str], ...],
) -> dict[str, Decimal]:
    return {
        key: Decimal(item)
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class ComparisonScoringPolicy:
    policy_id: str
    component_weights: tuple[tuple[str, str], ...]
    total_weight: str
    higher_score_preferred: bool
    policy_hash: str

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        component_weights: Mapping[str, Any],
        higher_score_preferred: bool = True,
    ) -> "ComparisonScoringPolicy":
        normalized_policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )

        immutable_weights = _immutable_decimal_mapping(
            component_weights,
            "component_weights",
        )

        if not immutable_weights:
            raise OpportunityComparisonContractError(
                "component_weights must not be empty"
            )

        weights = _decimal_mapping_from_immutable(
            immutable_weights
        )

        for component_id, weight in weights.items():
            if weight <= Decimal("0"):
                raise OpportunityComparisonContractError(
                    "component weight must be greater than zero: "
                    f"{component_id}"
                )

        total_weight = sum(
            weights.values(),
            Decimal("0"),
        )

        normalized_higher_score_preferred = _require_bool(
            higher_score_preferred,
            "higher_score_preferred",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "comparison_scoring_policy",
            "policy_id": normalized_policy_id,
            "component_weights": {
                key: value
                for key, value in immutable_weights
            },
            "total_weight": _canonical_decimal(
                total_weight
            ),
            "higher_score_preferred": (
                normalized_higher_score_preferred
            ),
        }

        return cls(
            policy_id=normalized_policy_id,
            component_weights=immutable_weights,
            total_weight=_canonical_decimal(
                total_weight
            ),
            higher_score_preferred=(
                normalized_higher_score_preferred
            ),
            policy_hash=stable_hash(payload),
        )

    @property
    def component_ids(self) -> tuple[str, ...]:
        return tuple(
            key
            for key, _ in self.component_weights
        )

    def weights_dict(self) -> dict[str, Decimal]:
        return _decimal_mapping_from_immutable(
            self.component_weights
        )


@dataclass(frozen=True, slots=True)
class CrossVenueOpportunityCandidate:
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
    observed_at: datetime
    valid_from: datetime
    expires_at: datetime
    validity_status: str
    venue_verified: bool
    source_record_hash: str
    validity_evidence_hash: str
    normalized_components: tuple[
        tuple[str, str],
        ...
    ]
    metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    candidate_hash: str

    @classmethod
    def create(
        cls,
        *,
        opportunity_id: str,
        thesis_id: str,
        comparability_group_id: str,
        canonical_market_id: str,
        venue_id: str,
        venue_name: str,
        venue_type: str,
        instrument_type: str,
        opportunity_type: str,
        expression_type: str,
        direction: str,
        reference_price: Any,
        price_unit: str,
        observed_at: datetime,
        valid_from: datetime,
        expires_at: datetime,
        validity_status: str,
        venue_verified: bool,
        source_record_hash: str,
        validity_evidence_hash: str,
        normalized_components: Mapping[str, Any],
        metadata: Mapping[str, Any],
    ) -> "CrossVenueOpportunityCandidate":
        normalized_opportunity_id = _require_non_empty_string(
            opportunity_id,
            "opportunity_id",
        )

        normalized_thesis_id = _require_non_empty_string(
            thesis_id,
            "thesis_id",
        )

        normalized_comparability_group_id = (
            _require_non_empty_string(
                comparability_group_id,
                "comparability_group_id",
            )
        )

        normalized_market_id = _require_non_empty_string(
            canonical_market_id,
            "canonical_market_id",
        )

        normalized_venue_id = _require_non_empty_string(
            venue_id,
            "venue_id",
        )

        normalized_venue_name = _require_non_empty_string(
            venue_name,
            "venue_name",
        )

        normalized_venue_type = _require_non_empty_string(
            venue_type,
            "venue_type",
        )

        normalized_instrument_type = _require_non_empty_string(
            instrument_type,
            "instrument_type",
        )

        normalized_opportunity_type = _require_non_empty_string(
            opportunity_type,
            "opportunity_type",
        )

        normalized_expression_type = _require_non_empty_string(
            expression_type,
            "expression_type",
        )

        normalized_direction = _require_non_empty_string(
            direction,
            "direction",
        )

        normalized_reference_price = _canonical_decimal(
            _require_decimal(
                reference_price,
                "reference_price",
            )
        )

        normalized_price_unit = _require_non_empty_string(
            price_unit,
            "price_unit",
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

        normalized_validity_status = _require_non_empty_string(
            validity_status,
            "validity_status",
        )

        normalized_venue_verified = _require_bool(
            venue_verified,
            "venue_verified",
        )

        normalized_source_record_hash = _require_non_empty_string(
            source_record_hash,
            "source_record_hash",
        )

        normalized_validity_evidence_hash = (
            _require_non_empty_string(
                validity_evidence_hash,
                "validity_evidence_hash",
            )
        )

        if normalized_valid_from < normalized_observed_at:
            raise OpportunityComparisonContractError(
                "valid_from cannot be before observed_at"
            )

        if normalized_expires_at <= normalized_valid_from:
            raise OpportunityComparisonContractError(
                "expires_at must be after valid_from"
            )

        immutable_components = _immutable_decimal_mapping(
            normalized_components,
            "normalized_components",
        )

        if not immutable_components:
            raise OpportunityComparisonContractError(
                "normalized_components must not be empty"
            )

        for component_id, component_value in (
            _decimal_mapping_from_immutable(
                immutable_components
            ).items()
        ):
            if (
                component_value < Decimal("0")
                or component_value > Decimal("1")
            ):
                raise OpportunityComparisonContractError(
                    "normalized scoring component must be between "
                    "0 and 1 inclusive: "
                    f"{component_id}"
                )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": COMPARISON_CANDIDATE_RECORD_TYPE,
            "opportunity_id": normalized_opportunity_id,
            "thesis_id": normalized_thesis_id,
            "comparability_group_id": (
                normalized_comparability_group_id
            ),
            "canonical_market_id": normalized_market_id,
            "venue_id": normalized_venue_id,
            "venue_name": normalized_venue_name,
            "venue_type": normalized_venue_type,
            "instrument_type": normalized_instrument_type,
            "opportunity_type": normalized_opportunity_type,
            "expression_type": normalized_expression_type,
            "direction": normalized_direction,
            "reference_price": normalized_reference_price,
            "price_unit": normalized_price_unit,
            "observed_at": normalized_observed_at,
            "valid_from": normalized_valid_from,
            "expires_at": normalized_expires_at,
            "validity_status": normalized_validity_status,
            "venue_verified": normalized_venue_verified,
            "source_record_hash": normalized_source_record_hash,
            "validity_evidence_hash": (
                normalized_validity_evidence_hash
            ),
            "normalized_components": {
                key: value
                for key, value in immutable_components
            },
            "metadata": _mapping_from_immutable(
                immutable_metadata
            ),
        }

        return cls(
            opportunity_id=normalized_opportunity_id,
            thesis_id=normalized_thesis_id,
            comparability_group_id=(
                normalized_comparability_group_id
            ),
            canonical_market_id=normalized_market_id,
            venue_id=normalized_venue_id,
            venue_name=normalized_venue_name,
            venue_type=normalized_venue_type,
            instrument_type=normalized_instrument_type,
            opportunity_type=normalized_opportunity_type,
            expression_type=normalized_expression_type,
            direction=normalized_direction,
            reference_price=normalized_reference_price,
            price_unit=normalized_price_unit,
            observed_at=normalized_observed_at,
            valid_from=normalized_valid_from,
            expires_at=normalized_expires_at,
            validity_status=normalized_validity_status,
            venue_verified=normalized_venue_verified,
            source_record_hash=normalized_source_record_hash,
            validity_evidence_hash=(
                normalized_validity_evidence_hash
            ),
            normalized_components=immutable_components,
            metadata=immutable_metadata,
            candidate_hash=stable_hash(payload),
        )

    def components_dict(self) -> dict[str, Decimal]:
        return _decimal_mapping_from_immutable(
            self.normalized_components
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "thesis_id": self.thesis_id,
            "comparability_group_id": (
                self.comparability_group_id
            ),
            "canonical_market_id": self.canonical_market_id,
            "venue_id": self.venue_id,
            "venue_name": self.venue_name,
            "venue_type": self.venue_type,
            "instrument_type": self.instrument_type,
            "opportunity_type": self.opportunity_type,
            "expression_type": self.expression_type,
            "direction": self.direction,
            "reference_price": self.reference_price,
            "price_unit": self.price_unit,
            "observed_at": self.observed_at.isoformat(),
            "valid_from": self.valid_from.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "validity_status": self.validity_status,
            "venue_verified": self.venue_verified,
            "source_record_hash": self.source_record_hash,
            "validity_evidence_hash": (
                self.validity_evidence_hash
            ),
            "normalized_components": {
                key: value
                for key, value in self.normalized_components
            },
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
            "candidate_hash": self.candidate_hash,
        }


@dataclass(frozen=True, slots=True)
class RankedCrossVenueOpportunity:
    rank: int
    opportunity_id: str
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
    candidate_hash: str
    expires_at: datetime
    rank_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "opportunity_id": self.opportunity_id,
            "canonical_market_id": self.canonical_market_id,
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
            "candidate_hash": self.candidate_hash,
            "expires_at": self.expires_at.isoformat(),
            "rank_hash": self.rank_hash,
        }


@dataclass(frozen=True, slots=True)
class CrossVenueOpportunityComparisonResult:
    schema_version: str
    engine_id: str
    thesis_id: str
    comparability_group_id: str
    scoring_policy_id: str
    scoring_policy_hash: str
    compared_at: datetime
    candidate_count: int
    eligible_count: int
    ineligible_count: int
    ranked_opportunities: tuple[
        RankedCrossVenueOpportunity,
        ...
    ]
    best_opportunity_id: str | None
    best_venue_id: str | None
    best_venue_name: str | None
    best_expression_type: str | None
    best_direction: str | None
    best_reference_price: str | None
    best_price_unit: str | None
    best_normalized_score: str | None
    tie_for_best: bool
    comparison_status: str
    reason_codes: tuple[str, ...]
    comparison_hash: str
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    read_only: bool
    execution_allowed: bool
    venue_ranked_as_intelligence: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_comparison_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "thesis_id": self.thesis_id,
            "comparability_group_id": (
                self.comparability_group_id
            ),
            "scoring_policy_id": self.scoring_policy_id,
            "scoring_policy_hash": self.scoring_policy_hash,
            "compared_at": self.compared_at.isoformat(),
            "candidate_count": self.candidate_count,
            "eligible_count": self.eligible_count,
            "ineligible_count": self.ineligible_count,
            "ranked_opportunities": [
                item.to_canonical_dict()
                for item in self.ranked_opportunities
            ],
            "best_opportunity_id": self.best_opportunity_id,
            "best_venue_id": self.best_venue_id,
            "best_venue_name": self.best_venue_name,
            "best_expression_type": (
                self.best_expression_type
            ),
            "best_direction": self.best_direction,
            "best_reference_price": (
                self.best_reference_price
            ),
            "best_price_unit": self.best_price_unit,
            "best_normalized_score": (
                self.best_normalized_score
            ),
            "tie_for_best": self.tie_for_best,
            "comparison_status": self.comparison_status,
            "reason_codes": list(self.reason_codes),
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "venue_ranked_as_intelligence": (
                self.venue_ranked_as_intelligence
            ),
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

        if include_comparison_hash:
            result["comparison_hash"] = self.comparison_hash

        return result


class OracleCanonicalCrossVenueOpportunityComparisonEngine:
    """
    Canonical cross-venue opportunity comparison engine.

    Comparison is based only on explicitly normalized scoring components.

    Raw instrument prices are preserved as identity/display evidence but are
    never used as a universal cross-instrument comparison unit.

    Example:

    Kalshi YES share:
        reference_price = 0.31
        price_unit = USD_PER_SHARE

    Coinbase BTC spot:
        reference_price = 117420
        price_unit = USD_PER_BTC

    These raw prices are not mathematically compared.

    Instead, both candidates may provide normalized scoring components such
    as:

        thesis_alignment
        expected_edge
        liquidity_quality
        execution_quality
        time_fit

    Each component must be in [0, 1].

    The scoring policy explicitly weights those normalized components.
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
        scoring_policy: ComparisonScoringPolicy,
    ) -> None:
        if not isinstance(
            scoring_policy,
            ComparisonScoringPolicy,
        ):
            raise OpportunityComparisonContractError(
                "scoring_policy must be ComparisonScoringPolicy"
            )

        self._scoring_policy = scoring_policy

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
            raise OpportunityComparisonInvariantError(
                "Oracle cross-venue comparison invariants violated"
            )

    def compare(
        self,
        *,
        candidates: Sequence[
            CrossVenueOpportunityCandidate
        ],
        compared_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> CrossVenueOpportunityComparisonResult:
        self._assert_invariants()

        if isinstance(candidates, (str, bytes)):
            raise OpportunityComparisonContractError(
                "candidates must be a sequence of candidate records"
            )

        if not isinstance(candidates, Sequence):
            raise OpportunityComparisonContractError(
                "candidates must be a sequence"
            )

        if not candidates:
            raise OpportunityComparisonContractError(
                "candidates must not be empty"
            )

        normalized_compared_at = _require_aware_datetime(
            compared_at,
            "compared_at",
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        validated_candidates: list[
            CrossVenueOpportunityCandidate
        ] = []

        opportunity_ids: set[str] = set()

        for candidate in candidates:
            if not isinstance(
                candidate,
                CrossVenueOpportunityCandidate,
            ):
                raise OpportunityComparisonContractError(
                    "candidates contains incompatible record"
                )

            if candidate.opportunity_id in opportunity_ids:
                raise OpportunityComparisonContractError(
                    "duplicate opportunity_id in comparison"
                )

            opportunity_ids.add(candidate.opportunity_id)

            self._validate_component_contract(
                candidate
            )

            validated_candidates.append(candidate)

        thesis_ids = {
            candidate.thesis_id
            for candidate in validated_candidates
        }

        if len(thesis_ids) != 1:
            raise OpportunityComparabilityError(
                "all candidates must share one thesis_id"
            )

        comparability_group_ids = {
            candidate.comparability_group_id
            for candidate in validated_candidates
        }

        if len(comparability_group_ids) != 1:
            raise OpportunityComparabilityError(
                "all candidates must share one "
                "comparability_group_id"
            )

        thesis_id = next(iter(thesis_ids))

        comparability_group_id = next(
            iter(comparability_group_ids)
        )

        eligible_candidates = [
            candidate
            for candidate in validated_candidates
            if self._is_eligible(
                candidate=candidate,
                compared_at=normalized_compared_at,
            )
        ]

        scored_candidates = [
            (
                candidate,
                self._calculate_score(candidate),
            )
            for candidate in eligible_candidates
        ]

        reverse = (
            self._scoring_policy.higher_score_preferred
        )

        scored_candidates.sort(
            key=lambda item: (
                item[1],
                item[0].opportunity_id,
            ),
            reverse=reverse,
        )

        ranked_opportunities: list[
            RankedCrossVenueOpportunity
        ] = []

        prior_score: Decimal | None = None
        current_rank = 0

        for index, (
            candidate,
            score,
        ) in enumerate(
            scored_candidates,
            start=1,
        ):
            if prior_score is None or score != prior_score:
                current_rank = index

            rank_payload = {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    "ranked_cross_venue_opportunity"
                ),
                "rank": current_rank,
                "opportunity_id": candidate.opportunity_id,
                "canonical_market_id": (
                    candidate.canonical_market_id
                ),
                "venue_id": candidate.venue_id,
                "venue_name": candidate.venue_name,
                "venue_type": candidate.venue_type,
                "instrument_type": candidate.instrument_type,
                "opportunity_type": (
                    candidate.opportunity_type
                ),
                "expression_type": candidate.expression_type,
                "direction": candidate.direction,
                "reference_price": candidate.reference_price,
                "price_unit": candidate.price_unit,
                "normalized_score": _canonical_decimal(
                    score
                ),
                "candidate_hash": candidate.candidate_hash,
                "expires_at": candidate.expires_at,
            }

            ranked_opportunities.append(
                RankedCrossVenueOpportunity(
                    rank=current_rank,
                    opportunity_id=candidate.opportunity_id,
                    canonical_market_id=(
                        candidate.canonical_market_id
                    ),
                    venue_id=candidate.venue_id,
                    venue_name=candidate.venue_name,
                    venue_type=candidate.venue_type,
                    instrument_type=(
                        candidate.instrument_type
                    ),
                    opportunity_type=(
                        candidate.opportunity_type
                    ),
                    expression_type=(
                        candidate.expression_type
                    ),
                    direction=candidate.direction,
                    reference_price=(
                        candidate.reference_price
                    ),
                    price_unit=candidate.price_unit,
                    normalized_score=_canonical_decimal(
                        score
                    ),
                    candidate_hash=candidate.candidate_hash,
                    expires_at=candidate.expires_at,
                    rank_hash=stable_hash(rank_payload),
                )
            )

            prior_score = score

        immutable_ranked = tuple(
            ranked_opportunities
        )

        if not immutable_ranked:
            best = None
            tie_for_best = False
            comparison_status = "no_eligible_opportunities"
            reason_codes = (
                "all_candidates_ineligible",
                "no_active_verified_opportunity",
            )
        else:
            best = immutable_ranked[0]

            best_score = best.normalized_score

            top_rank_count = sum(
                1
                for item in immutable_ranked
                if item.rank == 1
                and item.normalized_score == best_score
            )

            tie_for_best = top_rank_count > 1

            if tie_for_best:
                comparison_status = "best_opportunity_tied"
                reason_codes = (
                    "cross_venue_comparison_completed",
                    "normalized_scoring_used",
                    "raw_prices_not_compared_directly",
                    "best_opportunity_tied",
                )
            else:
                comparison_status = "best_opportunity_resolved"
                reason_codes = (
                    "cross_venue_comparison_completed",
                    "normalized_scoring_used",
                    "raw_prices_not_compared_directly",
                    "best_opportunity_resolved",
                    "venue_ranked_as_intelligence",
                )

        provisional = CrossVenueOpportunityComparisonResult(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            thesis_id=thesis_id,
            comparability_group_id=(
                comparability_group_id
            ),
            scoring_policy_id=(
                self._scoring_policy.policy_id
            ),
            scoring_policy_hash=(
                self._scoring_policy.policy_hash
            ),
            compared_at=normalized_compared_at,
            candidate_count=len(validated_candidates),
            eligible_count=len(eligible_candidates),
            ineligible_count=(
                len(validated_candidates)
                - len(eligible_candidates)
            ),
            ranked_opportunities=immutable_ranked,
            best_opportunity_id=(
                None
                if best is None
                else best.opportunity_id
            ),
            best_venue_id=(
                None
                if best is None
                else best.venue_id
            ),
            best_venue_name=(
                None
                if best is None
                else best.venue_name
            ),
            best_expression_type=(
                None
                if best is None
                else best.expression_type
            ),
            best_direction=(
                None
                if best is None
                else best.direction
            ),
            best_reference_price=(
                None
                if best is None
                else best.reference_price
            ),
            best_price_unit=(
                None
                if best is None
                else best.price_unit
            ),
            best_normalized_score=(
                None
                if best is None
                else best.normalized_score
            ),
            tie_for_best=tie_for_best,
            comparison_status=comparison_status,
            reason_codes=reason_codes,
            comparison_hash="",
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            read_only=True,
            execution_allowed=False,
            venue_ranked_as_intelligence=(
                best is not None
            ),
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        comparison_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    COMPARISON_RESULT_RECORD_TYPE
                ),
                "comparison": (
                    provisional.to_canonical_dict(
                        include_comparison_hash=False
                    )
                ),
            }
        )

        return CrossVenueOpportunityComparisonResult(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            thesis_id=provisional.thesis_id,
            comparability_group_id=(
                provisional.comparability_group_id
            ),
            scoring_policy_id=(
                provisional.scoring_policy_id
            ),
            scoring_policy_hash=(
                provisional.scoring_policy_hash
            ),
            compared_at=provisional.compared_at,
            candidate_count=provisional.candidate_count,
            eligible_count=provisional.eligible_count,
            ineligible_count=provisional.ineligible_count,
            ranked_opportunities=(
                provisional.ranked_opportunities
            ),
            best_opportunity_id=(
                provisional.best_opportunity_id
            ),
            best_venue_id=provisional.best_venue_id,
            best_venue_name=provisional.best_venue_name,
            best_expression_type=(
                provisional.best_expression_type
            ),
            best_direction=provisional.best_direction,
            best_reference_price=(
                provisional.best_reference_price
            ),
            best_price_unit=(
                provisional.best_price_unit
            ),
            best_normalized_score=(
                provisional.best_normalized_score
            ),
            tie_for_best=provisional.tie_for_best,
            comparison_status=(
                provisional.comparison_status
            ),
            reason_codes=provisional.reason_codes,
            comparison_hash=comparison_hash,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            read_only=True,
            execution_allowed=False,
            venue_ranked_as_intelligence=(
                provisional.venue_ranked_as_intelligence
            ),
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def _validate_component_contract(
        self,
        candidate: CrossVenueOpportunityCandidate,
    ) -> None:
        candidate_component_ids = set(
            candidate.components_dict()
        )

        policy_component_ids = set(
            self._scoring_policy.component_ids
        )

        if candidate_component_ids != policy_component_ids:
            missing = tuple(
                sorted(
                    policy_component_ids
                    - candidate_component_ids
                )
            )

            extra = tuple(
                sorted(
                    candidate_component_ids
                    - policy_component_ids
                )
            )

            raise OpportunityComparisonContractError(
                "candidate scoring component contract mismatch; "
                f"missing={missing}, extra={extra}"
            )

    @staticmethod
    def _is_eligible(
        *,
        candidate: CrossVenueOpportunityCandidate,
        compared_at: datetime,
    ) -> bool:
        if candidate.venue_verified is not True:
            return False

        if candidate.validity_status != "active":
            return False

        if compared_at < candidate.valid_from:
            return False

        if compared_at >= candidate.expires_at:
            return False

        return True

    def _calculate_score(
        self,
        candidate: CrossVenueOpportunityCandidate,
    ) -> Decimal:
        components = candidate.components_dict()

        weights = self._scoring_policy.weights_dict()

        weighted_total = sum(
            (
                components[component_id]
                * weights[component_id]
            )
            for component_id in self._scoring_policy.component_ids
        )

        total_weight = Decimal(
            self._scoring_policy.total_weight
        )

        if total_weight <= Decimal("0"):
            raise OpportunityComparisonInvariantError(
                "scoring policy total weight must be positive"
            )

        return weighted_total / total_weight


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "OpportunityComparisonContractError",
    "OpportunityComparabilityError",
    "OpportunityComparisonInvariantError",
    "ComparisonScoringPolicy",
    "CrossVenueOpportunityCandidate",
    "RankedCrossVenueOpportunity",
    "CrossVenueOpportunityComparisonResult",
    "OracleCanonicalCrossVenueOpportunityComparisonEngine",
    "canonical_json",
    "stable_hash",
]
