"""
OLA-036
Oracle Live Acquisition Lineage Cycle Bridge

Canonical cycle-boundary integration above OLA-035.

Purpose:
- accept one completed canonical live acquisition market cohort
- bind every observation in the cohort to one exact cycle observed-at time
- preserve canonical acquisition batch identity across the cohort
- route the complete cohort atomically through OLA-035
- return one immutable cycle receipt binding acquisition-cycle identity to
  exact market-state dwell/change lineage advancement

This boundary does not acquire data itself and owns no persistence,
intelligence interpretation, scoring, alerting, Q Series handoff,
authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable

from .oracle_atomic_market_lineage_batch_router import (
    AtomicMarketLineageBatchContractError,
    AtomicMarketLineageBatchFrame,
    AtomicMarketLineageBatchInvariantError,
    AtomicMarketLineageBatchReceipt,
    OracleAtomicMarketLineageBatchRouter,
)
from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-036"
ENGINE_ID = "OLA-036"
RECEIPT_TYPE = "oracle_live_acquisition_lineage_cycle_receipt"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class LiveAcquisitionLineageCycleContractError(ValueError):
    """Raised when OLA-036 cycle input is malformed."""


class LiveAcquisitionLineageCycleInvariantError(RuntimeError):
    """Raised when permanent OLA-036 invariants are violated."""


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise LiveAcquisitionLineageCycleContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None:
        raise LiveAcquisitionLineageCycleContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class LiveAcquisitionLineageCycleReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    acquisition_batch_id: str
    cycle_observed_at: str
    cohort_observation_count: int
    cohort_market_count: int
    transition_count: int
    ledger_market_count_before: int
    ledger_record_count_before: int
    ledger_market_count_after: int
    ledger_record_count_after: int
    lineage_batch_receipt: AtomicMarketLineageBatchReceipt
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    cycle_receipt_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise LiveAcquisitionLineageCycleInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise LiveAcquisitionLineageCycleInvariantError(
                "engine identity invariant violated"
            )
        if self.receipt_type != RECEIPT_TYPE:
            raise LiveAcquisitionLineageCycleInvariantError(
                "receipt type invariant violated"
            )
        if self.cohort_observation_count <= 0:
            raise LiveAcquisitionLineageCycleInvariantError(
                "cohort observation count must be positive"
            )
        if self.cohort_market_count <= 0:
            raise LiveAcquisitionLineageCycleInvariantError(
                "cohort market count must be positive"
            )
        if (
            self.cohort_observation_count
            != self.lineage_batch_receipt.batch_frame_count
        ):
            raise LiveAcquisitionLineageCycleInvariantError(
                "cycle and lineage batch frame counts diverged"
            )
        if (
            self.cohort_market_count
            != self.lineage_batch_receipt.batch_market_count
        ):
            raise LiveAcquisitionLineageCycleInvariantError(
                "cycle and lineage batch market counts diverged"
            )
        if (
            self.transition_count
            != self.lineage_batch_receipt.transition_count
        ):
            raise LiveAcquisitionLineageCycleInvariantError(
                "cycle transition count diverged"
            )

        authority = (
            self.read_only,
            self.execution_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if authority != (
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ):
            raise LiveAcquisitionLineageCycleInvariantError(
                "OLA-036 read-only authority invariants violated"
            )


class OracleLiveAcquisitionLineageCycleBridge:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        batch_router: OracleAtomicMarketLineageBatchRouter | None = None,
    ) -> None:
        self._batch_router = (
            batch_router
            if batch_router is not None
            else OracleAtomicMarketLineageBatchRouter()
        )

        if not isinstance(
            self._batch_router,
            OracleAtomicMarketLineageBatchRouter,
        ):
            raise LiveAcquisitionLineageCycleContractError(
                "batch_router must be an OLA-035 "
                "OracleAtomicMarketLineageBatchRouter"
            )

    @property
    def batch_router(self) -> OracleAtomicMarketLineageBatchRouter:
        return self._batch_router

    def advance_cycle(
        self,
        *,
        observations: Iterable[CanonicalObservation],
        cycle_observed_at: datetime,
    ) -> LiveAcquisitionLineageCycleReceipt:
        normalized_observations = tuple(observations)

        if not normalized_observations:
            raise LiveAcquisitionLineageCycleContractError(
                "cycle must contain at least one canonical observation"
            )

        cycle_time = _require_utc_datetime(
            cycle_observed_at,
            "cycle_observed_at",
        )

        acquisition_batch_ids: set[str] = set()

        for observation in normalized_observations:
            if not isinstance(observation, CanonicalObservation):
                raise LiveAcquisitionLineageCycleContractError(
                    "cycle observations must be canonical observations"
                )
            if observation.observation_type != "market_snapshot":
                raise LiveAcquisitionLineageCycleContractError(
                    "cycle accepts only market_snapshot observations"
                )

            acquisition_batch_id = observation.acquisition_batch_id

            if not isinstance(acquisition_batch_id, str):
                raise LiveAcquisitionLineageCycleContractError(
                    "acquisition_batch_id must be a string"
                )

            normalized_batch_id = acquisition_batch_id.strip()

            if not normalized_batch_id:
                raise LiveAcquisitionLineageCycleContractError(
                    "acquisition_batch_id must not be empty"
                )

            acquisition_batch_ids.add(normalized_batch_id)

        if len(acquisition_batch_ids) != 1:
            raise LiveAcquisitionLineageCycleContractError(
                "all cycle observations must share one acquisition_batch_id"
            )

        acquisition_batch_id = next(iter(acquisition_batch_ids))

        frames = tuple(
            AtomicMarketLineageBatchFrame(
                observation=observation,
                frame_observed_at=cycle_time,
            )
            for observation in normalized_observations
        )

        try:
            batch_receipt = self._batch_router.route(
                frames=frames
            )
        except AtomicMarketLineageBatchContractError as exc:
            raise LiveAcquisitionLineageCycleContractError(
                f"OLA-035 lineage batch rejected cycle: {exc}"
            ) from exc
        except AtomicMarketLineageBatchInvariantError as exc:
            raise LiveAcquisitionLineageCycleInvariantError(
                f"OLA-035 lineage batch invariant failed: {exc}"
            ) from exc

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "acquisition_batch_id": acquisition_batch_id,
            "cycle_observed_at": cycle_time.isoformat(),
            "cohort_observation_count": len(normalized_observations),
            "cohort_market_count": batch_receipt.batch_market_count,
            "transition_count": batch_receipt.transition_count,
            "ledger_market_count_before": (
                batch_receipt.ledger_market_count_before
            ),
            "ledger_record_count_before": (
                batch_receipt.ledger_record_count_before
            ),
            "ledger_market_count_after": (
                batch_receipt.ledger_market_count_after
            ),
            "ledger_record_count_after": (
                batch_receipt.ledger_record_count_after
            ),
            "lineage_batch_receipt": {
                "schema_version": batch_receipt.schema_version,
                "engine_id": batch_receipt.engine_id,
                "status": batch_receipt.status,
                "batch_frame_count": batch_receipt.batch_frame_count,
                "batch_market_count": batch_receipt.batch_market_count,
                "transition_count": batch_receipt.transition_count,
                "receipt_hashes": [
                    receipt.receipt_hash
                    for receipt in batch_receipt.receipts
                ],
            },
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = LiveAcquisitionLineageCycleReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            receipt_type=RECEIPT_TYPE,
            acquisition_batch_id=acquisition_batch_id,
            cycle_observed_at=cycle_time.isoformat(),
            cohort_observation_count=len(normalized_observations),
            cohort_market_count=batch_receipt.batch_market_count,
            transition_count=batch_receipt.transition_count,
            ledger_market_count_before=(
                batch_receipt.ledger_market_count_before
            ),
            ledger_record_count_before=(
                batch_receipt.ledger_record_count_before
            ),
            ledger_market_count_after=(
                batch_receipt.ledger_market_count_after
            ),
            ledger_record_count_after=(
                batch_receipt.ledger_record_count_after
            ),
            lineage_batch_receipt=batch_receipt,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            cycle_receipt_hash=_stable_hash(payload),
        )

        receipt.assert_invariants()
        return receipt
