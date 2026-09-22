"""
OLA-031
Oracle Canonical Market State Fingerprint Contract

Exact live market-state identity boundary for repeated Oracle observations.

Purpose:
- Distinguish "Oracle took another frame" from "the market actually changed."
- Project only canonical current mutable market-state fields.
- Exclude acquisition envelope, timestamps, provenance, batch identity, and
  CanonicalObservation content/replay identity from market-state hashing.
- Preserve exact fixed-point source strings without float conversion.
- Bind fingerprint identity to source + market while allowing equal state hashes
  for equal state projections on different markets.
- Provide the canonical foundation for future dwell/change lineage.

This is not OI-046 Market DNA Fingerprinting.
OI-046 owns broad behavioral similarity and analog fingerprints.
OLA-031 owns exact live market-state equality.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Any, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    JSONValue,
)


SCHEMA_VERSION = "OLA-031"
ENGINE_ID = "OLA-031"

MARKET_STATE_FINGERPRINT_RECORD_TYPE = (
    "canonical_market_state_fingerprint"
)

MARKET_STATE_PROJECTION_VERSION = (
    "oracle.market_state_projection.v1"
)

MARKET_STATE_FIELDS = (
    "yes_bid_dollars",
    "yes_bid_size_fp",
    "yes_ask_dollars",
    "yes_ask_size_fp",
    "no_bid_dollars",
    "no_ask_dollars",
    "last_price_dollars",
    "volume_fp",
    "volume_24h_fp",
    "open_interest_fp",
    "liquidity_dollars",
)

EXCLUDED_ACQUISITION_ENVELOPE_FIELDS = (
    "observation_id",
    "source_observation_id",
    "observed_at",
    "acquired_at",
    "acquisition_batch_id",
    "content_hash",
    "replay_hash",
    "provenance",
)

EXCLUDED_SOURCE_HISTORY_FIELDS = (
    "previous_yes_bid_dollars",
    "previous_yes_ask_dollars",
    "previous_price_dollars",
)

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class MarketStateFingerprintContractError(ValueError):
    """Raised when canonical market-state fingerprint input is malformed."""


class MarketStateFingerprintInvariantError(RuntimeError):
    """Raised when permanent OLA-031 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise MarketStateFingerprintContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise MarketStateFingerprintContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _canonicalize(value: Any) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise MarketStateFingerprintContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise MarketStateFingerprintContractError(
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

    raise MarketStateFingerprintContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def _stable_hash(value: Any) -> str:
    canonical = _canonicalize(value)

    encoded = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: _canonicalize(item)
        for key, item in value
    }


def _immutable_mapping(
    value: Mapping[str, Any],
) -> tuple[tuple[str, JSONValue], ...]:
    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise MarketStateFingerprintContractError(
            "market state projection must canonicalize to a mapping"
        )

    return tuple(
        (key, canonical[key])
        for key in sorted(canonical.keys())
    )


@dataclass(frozen=True, slots=True)
class CanonicalMarketStateFingerprint:
    schema_version: str
    engine_id: str
    record_type: str
    projection_version: str
    source_id: str
    source_market_id: str
    observation_id: str
    observation_type: str
    market_state: tuple[tuple[str, JSONValue], ...]
    market_state_hash: str
    fingerprint_id: str
    state_field_count: int
    acquisition_envelope_excluded: bool
    source_history_excluded: bool
    exact_fixed_point_strings_preserved: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    fingerprint_hash: str

    @classmethod
    def create(
        cls,
        *,
        observation: CanonicalObservation,
    ) -> "CanonicalMarketStateFingerprint":
        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise MarketStateFingerprintContractError(
                "observation must be a CanonicalObservation"
            )

        if observation.observation_type != "market_snapshot":
            raise MarketStateFingerprintContractError(
                "observation_type must be market_snapshot"
            )

        if observation.read_only is not True:
            raise MarketStateFingerprintInvariantError(
                "canonical observation must remain read-only"
            )

        if observation.execution_allowed is not False:
            raise MarketStateFingerprintInvariantError(
                "canonical observation execution must remain disabled"
            )

        payload = _mapping_from_immutable(
            observation.payload
        )

        source_market_id = _require_non_empty_string(
            payload.get("source_market_id"),
            "payload.source_market_id",
        )

        missing_fields = tuple(
            field_name
            for field_name in MARKET_STATE_FIELDS
            if field_name not in payload
        )

        if missing_fields:
            raise MarketStateFingerprintContractError(
                "market state payload missing required fields: "
                + ",".join(missing_fields)
            )

        projected_state = {
            field_name: payload[field_name]
            for field_name in MARKET_STATE_FIELDS
        }

        immutable_state = _immutable_mapping(
            projected_state
        )

        state_dict = _mapping_from_immutable(
            immutable_state
        )

        market_state_hash = _stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "projection_version": (
                    MARKET_STATE_PROJECTION_VERSION
                ),
                "record_type": "market_state_projection",
                "market_state": state_dict,
            }
        )

        fingerprint_id = (
            "market_state_fingerprint."
            + _stable_hash(
                {
                    "schema_version": SCHEMA_VERSION,
                    "projection_version": (
                        MARKET_STATE_PROJECTION_VERSION
                    ),
                    "source_id": observation.source_id,
                    "source_market_id": source_market_id,
                    "market_state_hash": market_state_hash,
                }
            )
        )

        fingerprint_payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "record_type": (
                MARKET_STATE_FINGERPRINT_RECORD_TYPE
            ),
            "projection_version": (
                MARKET_STATE_PROJECTION_VERSION
            ),
            "source_id": observation.source_id,
            "source_market_id": source_market_id,
            "observation_id": observation.observation_id,
            "observation_type": observation.observation_type,
            "market_state": state_dict,
            "market_state_hash": market_state_hash,
            "fingerprint_id": fingerprint_id,
            "state_field_count": len(MARKET_STATE_FIELDS),
            "acquisition_envelope_excluded": True,
            "source_history_excluded": True,
            "exact_fixed_point_strings_preserved": True,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": (
                EXECUTION_ADAPTER_RESOLVED
            ),
            "execution_adapter_invoked": (
                EXECUTION_ADAPTER_INVOKED
            ),
            "trade_authorization_allowed": (
                TRADE_AUTHORIZATION_ALLOWED
            ),
            "order_placement_allowed": (
                ORDER_PLACEMENT_ALLOWED
            ),
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        record = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            record_type=(
                MARKET_STATE_FINGERPRINT_RECORD_TYPE
            ),
            projection_version=(
                MARKET_STATE_PROJECTION_VERSION
            ),
            source_id=observation.source_id,
            source_market_id=source_market_id,
            observation_id=observation.observation_id,
            observation_type=observation.observation_type,
            market_state=immutable_state,
            market_state_hash=market_state_hash,
            fingerprint_id=fingerprint_id,
            state_field_count=len(MARKET_STATE_FIELDS),
            acquisition_envelope_excluded=True,
            source_history_excluded=True,
            exact_fixed_point_strings_preserved=True,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=(
                EXECUTION_ADAPTER_RESOLVED
            ),
            execution_adapter_invoked=(
                EXECUTION_ADAPTER_INVOKED
            ),
            trade_authorization_allowed=(
                TRADE_AUTHORIZATION_ALLOWED
            ),
            order_placement_allowed=(
                ORDER_PLACEMENT_ALLOWED
            ),
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            fingerprint_hash=_stable_hash(
                fingerprint_payload
            ),
        )

        record.assert_invariants()

        return record

    def market_state_dict(self) -> dict[str, JSONValue]:
        return _mapping_from_immutable(
            self.market_state
        )

    def same_market_state_as(
        self,
        other: "CanonicalMarketStateFingerprint",
    ) -> bool:
        if not isinstance(
            other,
            CanonicalMarketStateFingerprint,
        ):
            raise MarketStateFingerprintContractError(
                "other must be a CanonicalMarketStateFingerprint"
            )

        return (
            self.source_id == other.source_id
            and self.source_market_id == other.source_market_id
            and self.market_state_hash == other.market_state_hash
        )

    def assert_invariants(self) -> None:
        if self.state_field_count != len(MARKET_STATE_FIELDS):
            raise MarketStateFingerprintInvariantError(
                "market state field count invariant violated"
            )

        if tuple(
            key
            for key, _ in self.market_state
        ) != tuple(sorted(MARKET_STATE_FIELDS)):
            raise MarketStateFingerprintInvariantError(
                "market state projection field invariant violated"
            )

        if (
            self.acquisition_envelope_excluded is not True
            or self.source_history_excluded is not True
            or self.exact_fixed_point_strings_preserved is not True
        ):
            raise MarketStateFingerprintInvariantError(
                "market state projection invariant violated"
            )

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
            raise MarketStateFingerprintInvariantError(
                "OLA-031 read-only invariants violated"
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "record_type": self.record_type,
            "projection_version": self.projection_version,
            "source_id": self.source_id,
            "source_market_id": self.source_market_id,
            "observation_id": self.observation_id,
            "observation_type": self.observation_type,
            "market_state": self.market_state_dict(),
            "market_state_hash": self.market_state_hash,
            "fingerprint_id": self.fingerprint_id,
            "state_field_count": self.state_field_count,
            "acquisition_envelope_excluded": (
                self.acquisition_envelope_excluded
            ),
            "source_history_excluded": (
                self.source_history_excluded
            ),
            "exact_fixed_point_strings_preserved": (
                self.exact_fixed_point_strings_preserved
            ),
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
            "fingerprint_hash": self.fingerprint_hash,
        }


class OracleCanonicalMarketStateFingerprintContract:
    read_only = True
    execution_allowed = False

    def fingerprint(
        self,
        *,
        observation: CanonicalObservation,
    ) -> CanonicalMarketStateFingerprint:
        return CanonicalMarketStateFingerprint.create(
            observation=observation
        )
