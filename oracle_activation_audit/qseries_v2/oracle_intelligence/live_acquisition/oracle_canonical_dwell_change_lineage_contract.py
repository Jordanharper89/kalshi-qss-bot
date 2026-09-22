"""
OLA-032
Oracle Canonical Dwell / Change Lineage Contract

Canonical temporal lineage boundary built directly on OLA-031 exact live
market-state identity.

Purpose:
- Measure how long an exact OLA-031 market state remained observed.
- Count consecutive frames preserving the exact same market state.
- Preserve first-observed and last-observed timestamps for the current state.
- Detect the first observed frame carrying a different exact market-state hash.
- Bind previous and current market-state hashes to deterministic transition
  identity.
- Chain every lineage record immutably for deterministic replay and audit.

This boundary performs no intelligence interpretation, signal scoring, alerting,
Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping

from .oracle_canonical_market_state_fingerprint_contract import (
    CanonicalMarketStateFingerprint,
)


SCHEMA_VERSION = "OLA-032"
ENGINE_ID = "OLA-032"

DWELL_CHANGE_LINEAGE_RECORD_TYPE = (
    "canonical_market_state_dwell_change_lineage"
)
LINEAGE_VERSION = "oracle.market_state_lineage.v1"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class DwellChangeLineageContractError(ValueError):
    """Raised when OLA-032 lineage input is malformed."""


class DwellChangeLineageInvariantError(RuntimeError):
    """Raised when permanent OLA-032 invariants are violated."""


def _canonicalize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DwellChangeLineageContractError(
                "non-finite floats are not canonical"
            )
        return json.loads(json.dumps(value, allow_nan=False))
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return _require_utc_datetime(
            value,
            "canonical_datetime",
        ).isoformat()
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise DwellChangeLineageContractError(
                    "canonical mapping keys must be strings"
                )
            result[key] = _canonicalize(value[key])
        return result
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    raise DwellChangeLineageContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise DwellChangeLineageContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()
    if not normalized:
        raise DwellChangeLineageContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise DwellChangeLineageContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None:
        raise DwellChangeLineageContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DwellChangeLineageContractError(
            f"{field_name} must be an integer"
        )
    if value <= 0:
        raise DwellChangeLineageContractError(
            f"{field_name} must be greater than zero"
        )

    return value


@dataclass(frozen=True, slots=True)
class CanonicalMarketStateDwellChangeLineage:
    schema_version: str
    engine_id: str
    record_type: str
    lineage_version: str
    source_id: str
    source_market_id: str
    observation_id: str
    fingerprint_id: str
    previous_fingerprint_id: str | None
    previous_market_state_hash: str | None
    current_market_state_hash: str
    state_first_observed_at: datetime
    state_last_observed_at: datetime
    current_frame_observed_at: datetime
    state_changed_at: datetime | None
    consecutive_frame_count: int
    dwell_seconds: str
    transition_detected: bool
    transition_id: str | None
    previous_lineage_hash: str | None
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    lineage_hash: str

    @classmethod
    def create(
        cls,
        *,
        current_fingerprint: CanonicalMarketStateFingerprint,
        current_frame_observed_at: datetime,
        previous_lineage: (
            "CanonicalMarketStateDwellChangeLineage | None"
        ) = None,
    ) -> "CanonicalMarketStateDwellChangeLineage":
        if not isinstance(
            current_fingerprint,
            CanonicalMarketStateFingerprint,
        ):
            raise DwellChangeLineageContractError(
                "current_fingerprint must be an "
                "OLA-031 CanonicalMarketStateFingerprint"
            )

        current_fingerprint.assert_invariants()

        if current_fingerprint.read_only is not True:
            raise DwellChangeLineageInvariantError(
                "OLA-031 fingerprint must remain read-only"
            )
        if current_fingerprint.execution_allowed is not False:
            raise DwellChangeLineageInvariantError(
                "OLA-031 fingerprint execution must remain disabled"
            )

        current_time = _require_utc_datetime(
            current_frame_observed_at,
            "current_frame_observed_at",
        )
        source_id = _require_non_empty_string(
            current_fingerprint.source_id,
            "current_fingerprint.source_id",
        )
        source_market_id = _require_non_empty_string(
            current_fingerprint.source_market_id,
            "current_fingerprint.source_market_id",
        )
        observation_id = _require_non_empty_string(
            current_fingerprint.observation_id,
            "current_fingerprint.observation_id",
        )
        fingerprint_id = _require_non_empty_string(
            current_fingerprint.fingerprint_id,
            "current_fingerprint.fingerprint_id",
        )
        current_state_hash = _require_non_empty_string(
            current_fingerprint.market_state_hash,
            "current_fingerprint.market_state_hash",
        )

        if previous_lineage is None:
            previous_fingerprint_id = None
            previous_state_hash = None
            state_first_observed_at = current_time
            state_last_observed_at = current_time
            state_changed_at = None
            consecutive_frame_count = 1
            transition_detected = False
            transition_id = None
            previous_lineage_hash = None
        else:
            if not isinstance(
                previous_lineage,
                CanonicalMarketStateDwellChangeLineage,
            ):
                raise DwellChangeLineageContractError(
                    "previous_lineage must be an OLA-032 lineage record"
                )

            previous_lineage.assert_invariants()

            if previous_lineage.source_id != source_id:
                raise DwellChangeLineageContractError(
                    "source_id lineage continuity mismatch"
                )
            if previous_lineage.source_market_id != source_market_id:
                raise DwellChangeLineageContractError(
                    "source_market_id lineage continuity mismatch"
                )
            if current_time < previous_lineage.current_frame_observed_at:
                raise DwellChangeLineageContractError(
                    "current_frame_observed_at regressed"
                )

            previous_fingerprint_id = previous_lineage.fingerprint_id
            previous_state_hash = (
                previous_lineage.current_market_state_hash
            )
            previous_lineage_hash = previous_lineage.lineage_hash
            transition_detected = (
                previous_state_hash != current_state_hash
            )

            if transition_detected:
                state_first_observed_at = current_time
                state_last_observed_at = current_time
                state_changed_at = current_time
                consecutive_frame_count = 1
                transition_id = (
                    "market_state_transition."
                    + _stable_hash(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "lineage_version": LINEAGE_VERSION,
                            "source_id": source_id,
                            "source_market_id": source_market_id,
                            "previous_market_state_hash": (
                                previous_state_hash
                            ),
                            "current_market_state_hash": (
                                current_state_hash
                            ),
                            "transition_observed_at": current_time,
                            "previous_lineage_hash": (
                                previous_lineage_hash
                            ),
                        }
                    )
                )
            else:
                state_first_observed_at = (
                    previous_lineage.state_first_observed_at
                )
                state_last_observed_at = current_time
                state_changed_at = previous_lineage.state_changed_at
                consecutive_frame_count = _require_positive_int(
                    previous_lineage.consecutive_frame_count,
                    "previous_lineage.consecutive_frame_count",
                ) + 1
                transition_id = None

        dwell_seconds_value = (
            state_last_observed_at - state_first_observed_at
        ).total_seconds()
        if dwell_seconds_value < 0:
            raise DwellChangeLineageInvariantError(
                "dwell duration cannot be negative"
            )

        dwell_seconds = format(dwell_seconds_value, ".6f")

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "record_type": DWELL_CHANGE_LINEAGE_RECORD_TYPE,
            "lineage_version": LINEAGE_VERSION,
            "source_id": source_id,
            "source_market_id": source_market_id,
            "observation_id": observation_id,
            "fingerprint_id": fingerprint_id,
            "previous_fingerprint_id": previous_fingerprint_id,
            "previous_market_state_hash": previous_state_hash,
            "current_market_state_hash": current_state_hash,
            "state_first_observed_at": state_first_observed_at,
            "state_last_observed_at": state_last_observed_at,
            "current_frame_observed_at": current_time,
            "state_changed_at": state_changed_at,
            "consecutive_frame_count": consecutive_frame_count,
            "dwell_seconds": dwell_seconds,
            "transition_detected": transition_detected,
            "transition_id": transition_id,
            "previous_lineage_hash": previous_lineage_hash,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        record = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            record_type=DWELL_CHANGE_LINEAGE_RECORD_TYPE,
            lineage_version=LINEAGE_VERSION,
            source_id=source_id,
            source_market_id=source_market_id,
            observation_id=observation_id,
            fingerprint_id=fingerprint_id,
            previous_fingerprint_id=previous_fingerprint_id,
            previous_market_state_hash=previous_state_hash,
            current_market_state_hash=current_state_hash,
            state_first_observed_at=state_first_observed_at,
            state_last_observed_at=state_last_observed_at,
            current_frame_observed_at=current_time,
            state_changed_at=state_changed_at,
            consecutive_frame_count=consecutive_frame_count,
            dwell_seconds=dwell_seconds,
            transition_detected=transition_detected,
            transition_id=transition_id,
            previous_lineage_hash=previous_lineage_hash,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            lineage_hash=_stable_hash(payload),
        )

        record.assert_invariants()
        return record

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise DwellChangeLineageInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise DwellChangeLineageInvariantError(
                "engine identity invariant violated"
            )
        if self.record_type != DWELL_CHANGE_LINEAGE_RECORD_TYPE:
            raise DwellChangeLineageInvariantError(
                "record type invariant violated"
            )
        if self.lineage_version != LINEAGE_VERSION:
            raise DwellChangeLineageInvariantError(
                "lineage version invariant violated"
            )

        _require_positive_int(
            self.consecutive_frame_count,
            "consecutive_frame_count",
        )

        first_time = _require_utc_datetime(
            self.state_first_observed_at,
            "state_first_observed_at",
        )
        last_time = _require_utc_datetime(
            self.state_last_observed_at,
            "state_last_observed_at",
        )
        frame_time = _require_utc_datetime(
            self.current_frame_observed_at,
            "current_frame_observed_at",
        )

        if first_time > last_time:
            raise DwellChangeLineageInvariantError(
                "state first-observed time exceeds last-observed time"
            )
        if last_time != frame_time:
            raise DwellChangeLineageInvariantError(
                "state last-observed time must equal current frame time"
            )

        expected_dwell = format(
            (last_time - first_time).total_seconds(),
            ".6f",
        )
        if self.dwell_seconds != expected_dwell:
            raise DwellChangeLineageInvariantError(
                "dwell duration invariant violated"
            )

        if self.transition_detected:
            if self.previous_market_state_hash is None:
                raise DwellChangeLineageInvariantError(
                    "transition requires previous state hash"
                )
            if (
                self.previous_market_state_hash
                == self.current_market_state_hash
            ):
                raise DwellChangeLineageInvariantError(
                    "transition requires changed state hash"
                )
            if self.transition_id is None:
                raise DwellChangeLineageInvariantError(
                    "transition requires transition identity"
                )
            if self.state_changed_at != frame_time:
                raise DwellChangeLineageInvariantError(
                    "transition changed-at must equal current frame time"
                )
            if self.consecutive_frame_count != 1:
                raise DwellChangeLineageInvariantError(
                    "transition must reset consecutive frame count"
                )
            if first_time != frame_time:
                raise DwellChangeLineageInvariantError(
                    "transition must reset state first-observed time"
                )
        else:
            if self.transition_id is not None:
                raise DwellChangeLineageInvariantError(
                    "non-transition cannot carry transition identity"
                )
            if (
                self.previous_market_state_hash is not None
                and self.previous_market_state_hash
                != self.current_market_state_hash
            ):
                raise DwellChangeLineageInvariantError(
                    "non-transition state hash continuity violated"
                )

        authority = {
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

        expected_authority = {
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if authority != expected_authority:
            raise DwellChangeLineageInvariantError(
                "OLA-032 read-only authority invariants violated"
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "record_type": self.record_type,
            "lineage_version": self.lineage_version,
            "source_id": self.source_id,
            "source_market_id": self.source_market_id,
            "observation_id": self.observation_id,
            "fingerprint_id": self.fingerprint_id,
            "previous_fingerprint_id": self.previous_fingerprint_id,
            "previous_market_state_hash": (
                self.previous_market_state_hash
            ),
            "current_market_state_hash": (
                self.current_market_state_hash
            ),
            "state_first_observed_at": (
                self.state_first_observed_at.isoformat()
            ),
            "state_last_observed_at": (
                self.state_last_observed_at.isoformat()
            ),
            "current_frame_observed_at": (
                self.current_frame_observed_at.isoformat()
            ),
            "state_changed_at": (
                None
                if self.state_changed_at is None
                else self.state_changed_at.isoformat()
            ),
            "consecutive_frame_count": self.consecutive_frame_count,
            "dwell_seconds": self.dwell_seconds,
            "transition_detected": self.transition_detected,
            "transition_id": self.transition_id,
            "previous_lineage_hash": self.previous_lineage_hash,
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
            "lineage_hash": self.lineage_hash,
        }


class OracleCanonicalDwellChangeLineageContract:
    read_only = True
    execution_allowed = False

    def observe(
        self,
        *,
        current_fingerprint: CanonicalMarketStateFingerprint,
        current_frame_observed_at: datetime,
        previous_lineage: (
            CanonicalMarketStateDwellChangeLineage | None
        ) = None,
    ) -> CanonicalMarketStateDwellChangeLineage:
        return CanonicalMarketStateDwellChangeLineage.create(
            current_fingerprint=current_fingerprint,
            current_frame_observed_at=current_frame_observed_at,
            previous_lineage=previous_lineage,
        )
