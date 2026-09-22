"""
OLA-037
Oracle Post-Persistence Lineage Cycle Coordinator

Canonical boundary between a completed persisted acquisition cycle and OLA-036.

Purpose:
- require explicit successful persistence evidence before lineage advancement
- require the exact canonical observations produced by the completed cycle
- require persisted count equality with the supplied canonical cohort
- bind cycle completion time to OLA-036 lineage advancement
- preserve fail-closed behavior before any lineage mutation
- return one immutable coordination receipt

This contract does not perform acquisition or persistence itself.
It does not interpret intelligence, score signals, alert, hand off to Q Series,
authorize trading, place orders, move funds, or mutate portfolios.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable

from .oracle_live_acquisition_lineage_cycle_bridge import (
    LiveAcquisitionLineageCycleContractError,
    LiveAcquisitionLineageCycleInvariantError,
    LiveAcquisitionLineageCycleReceipt,
    OracleLiveAcquisitionLineageCycleBridge,
)
from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-037"
ENGINE_ID = "OLA-037"
RECEIPT_TYPE = "oracle_post_persistence_lineage_cycle_receipt"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PostPersistenceLineageCycleContractError(ValueError):
    """Raised when OLA-037 coordination input is malformed."""


class PostPersistenceLineageCycleInvariantError(RuntimeError):
    """Raised when OLA-037 permanent invariants are violated."""


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None:
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must be an integer"
        )
    if value < 0:
        raise PostPersistenceLineageCycleContractError(
            f"{field_name} must not be negative"
        )

    return value


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
class PersistedAcquisitionCycleEvidence:
    schema_version: str
    engine_id: str
    cycle_status: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    cycle_completed_at: datetime
    read_only: bool
    execution_allowed: bool

    @classmethod
    def create(
        cls,
        *,
        schema_version: str,
        engine_id: str,
        cycle_status: str,
        acquisition_batch_id: str,
        canonical_count: int,
        persistence_count: int,
        cycle_completed_at: datetime,
        read_only: bool,
        execution_allowed: bool,
    ) -> "PersistedAcquisitionCycleEvidence":
        record = cls(
            schema_version=_require_non_empty_string(
                schema_version,
                "schema_version",
            ),
            engine_id=_require_non_empty_string(
                engine_id,
                "engine_id",
            ),
            cycle_status=_require_non_empty_string(
                cycle_status,
                "cycle_status",
            ),
            acquisition_batch_id=_require_non_empty_string(
                acquisition_batch_id,
                "acquisition_batch_id",
            ),
            canonical_count=_require_non_negative_int(
                canonical_count,
                "canonical_count",
            ),
            persistence_count=_require_non_negative_int(
                persistence_count,
                "persistence_count",
            ),
            cycle_completed_at=_require_utc_datetime(
                cycle_completed_at,
                "cycle_completed_at",
            ),
            read_only=read_only,
            execution_allowed=execution_allowed,
        )

        record.assert_invariants()
        return record

    def assert_invariants(self) -> None:
        if self.cycle_status != "completed":
            raise PostPersistenceLineageCycleContractError(
                "persisted cycle status must be completed"
            )
        if self.read_only is not True:
            raise PostPersistenceLineageCycleInvariantError(
                "persisted cycle lost read-only invariant"
            )
        if self.execution_allowed is not False:
            raise PostPersistenceLineageCycleInvariantError(
                "persisted cycle gained execution capability"
            )
        if self.canonical_count <= 0:
            raise PostPersistenceLineageCycleContractError(
                "canonical_count must be positive"
            )
        if self.persistence_count != self.canonical_count:
            raise PostPersistenceLineageCycleContractError(
                "persistence_count must equal canonical_count"
            )


@dataclass(frozen=True, slots=True)
class PostPersistenceLineageCycleReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    upstream_schema_version: str
    upstream_engine_id: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    cycle_completed_at: str
    lineage_cycle_receipt: LiveAcquisitionLineageCycleReceipt
    transition_count: int
    lineage_market_count_after: int
    lineage_record_count_after: int
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    coordination_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PostPersistenceLineageCycleInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise PostPersistenceLineageCycleInvariantError(
                "engine identity invariant violated"
            )
        if self.receipt_type != RECEIPT_TYPE:
            raise PostPersistenceLineageCycleInvariantError(
                "receipt type invariant violated"
            )
        if self.canonical_count <= 0:
            raise PostPersistenceLineageCycleInvariantError(
                "canonical count must be positive"
            )
        if self.persistence_count != self.canonical_count:
            raise PostPersistenceLineageCycleInvariantError(
                "persistence equality invariant violated"
            )
        if (
            self.acquisition_batch_id
            != self.lineage_cycle_receipt.acquisition_batch_id
        ):
            raise PostPersistenceLineageCycleInvariantError(
                "acquisition batch binding invariant violated"
            )
        if (
            self.canonical_count
            != self.lineage_cycle_receipt.cohort_observation_count
        ):
            raise PostPersistenceLineageCycleInvariantError(
                "canonical cohort count binding invariant violated"
            )
        if (
            self.cycle_completed_at
            != self.lineage_cycle_receipt.cycle_observed_at
        ):
            raise PostPersistenceLineageCycleInvariantError(
                "cycle completion clock binding invariant violated"
            )
        if (
            self.transition_count
            != self.lineage_cycle_receipt.transition_count
        ):
            raise PostPersistenceLineageCycleInvariantError(
                "transition count binding invariant violated"
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
            raise PostPersistenceLineageCycleInvariantError(
                "OLA-037 read-only authority invariants violated"
            )


class OraclePostPersistenceLineageCycleCoordinator:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        lineage_cycle_bridge: (
            OracleLiveAcquisitionLineageCycleBridge | None
        ) = None,
    ) -> None:
        self._lineage_cycle_bridge = (
            lineage_cycle_bridge
            if lineage_cycle_bridge is not None
            else OracleLiveAcquisitionLineageCycleBridge()
        )

        if not isinstance(
            self._lineage_cycle_bridge,
            OracleLiveAcquisitionLineageCycleBridge,
        ):
            raise PostPersistenceLineageCycleContractError(
                "lineage_cycle_bridge must be an OLA-036 "
                "OracleLiveAcquisitionLineageCycleBridge"
            )

    @property
    def lineage_cycle_bridge(
        self,
    ) -> OracleLiveAcquisitionLineageCycleBridge:
        return self._lineage_cycle_bridge

    def coordinate(
        self,
        *,
        cycle_evidence: PersistedAcquisitionCycleEvidence,
        canonical_observations: Iterable[CanonicalObservation],
    ) -> PostPersistenceLineageCycleReceipt:
        if not isinstance(
            cycle_evidence,
            PersistedAcquisitionCycleEvidence,
        ):
            raise PostPersistenceLineageCycleContractError(
                "cycle_evidence must be PersistedAcquisitionCycleEvidence"
            )

        cycle_evidence.assert_invariants()

        observations = tuple(canonical_observations)

        if not observations:
            raise PostPersistenceLineageCycleContractError(
                "canonical_observations must not be empty"
            )

        if len(observations) != cycle_evidence.canonical_count:
            raise PostPersistenceLineageCycleContractError(
                "supplied canonical observation count does not match "
                "persisted cycle evidence"
            )

        batch_ids: set[str] = set()

        for observation in observations:
            if not isinstance(observation, CanonicalObservation):
                raise PostPersistenceLineageCycleContractError(
                    "all canonical_observations must be canonical"
                )

            if observation.observation_type != "market_snapshot":
                raise PostPersistenceLineageCycleContractError(
                    "OLA-037 accepts only market_snapshot observations"
                )

            batch_ids.add(
                _require_non_empty_string(
                    observation.acquisition_batch_id,
                    "observation.acquisition_batch_id",
                )
            )

        if batch_ids != {cycle_evidence.acquisition_batch_id}:
            raise PostPersistenceLineageCycleContractError(
                "canonical observation batch identity does not match "
                "persisted cycle evidence"
            )

        before_record_count = (
            self._lineage_cycle_bridge
            .batch_router
            .bridge
            .ledger
            .record_count
        )

        try:
            lineage_receipt = (
                self._lineage_cycle_bridge.advance_cycle(
                    observations=observations,
                    cycle_observed_at=(
                        cycle_evidence.cycle_completed_at
                    ),
                )
            )
        except LiveAcquisitionLineageCycleContractError as exc:
            raise PostPersistenceLineageCycleContractError(
                f"OLA-036 lineage cycle rejected persisted cohort: {exc}"
            ) from exc
        except LiveAcquisitionLineageCycleInvariantError as exc:
            raise PostPersistenceLineageCycleInvariantError(
                f"OLA-036 lineage cycle invariant failed: {exc}"
            ) from exc

        expected_after_record_count = (
            before_record_count
            + cycle_evidence.canonical_count
        )

        if (
            lineage_receipt.ledger_record_count_after
            != expected_after_record_count
        ):
            raise PostPersistenceLineageCycleInvariantError(
                "lineage record delta does not match persisted canonical count"
            )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "upstream_schema_version": cycle_evidence.schema_version,
            "upstream_engine_id": cycle_evidence.engine_id,
            "acquisition_batch_id": (
                cycle_evidence.acquisition_batch_id
            ),
            "canonical_count": cycle_evidence.canonical_count,
            "persistence_count": cycle_evidence.persistence_count,
            "cycle_completed_at": (
                cycle_evidence.cycle_completed_at.isoformat()
            ),
            "lineage_cycle_receipt_hash": (
                lineage_receipt.cycle_receipt_hash
            ),
            "transition_count": lineage_receipt.transition_count,
            "lineage_market_count_after": (
                lineage_receipt.ledger_market_count_after
            ),
            "lineage_record_count_after": (
                lineage_receipt.ledger_record_count_after
            ),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = PostPersistenceLineageCycleReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            receipt_type=RECEIPT_TYPE,
            upstream_schema_version=cycle_evidence.schema_version,
            upstream_engine_id=cycle_evidence.engine_id,
            acquisition_batch_id=(
                cycle_evidence.acquisition_batch_id
            ),
            canonical_count=cycle_evidence.canonical_count,
            persistence_count=cycle_evidence.persistence_count,
            cycle_completed_at=(
                cycle_evidence.cycle_completed_at.isoformat()
            ),
            lineage_cycle_receipt=lineage_receipt,
            transition_count=lineage_receipt.transition_count,
            lineage_market_count_after=(
                lineage_receipt.ledger_market_count_after
            ),
            lineage_record_count_after=(
                lineage_receipt.ledger_record_count_after
            ),
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            coordination_hash=_stable_hash(payload),
        )

        receipt.assert_invariants()
        return receipt
