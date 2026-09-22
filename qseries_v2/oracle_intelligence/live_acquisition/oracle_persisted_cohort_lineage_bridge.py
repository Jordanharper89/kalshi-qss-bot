"""
OLA-039
Oracle Persisted Cohort Lineage Bridge

Canonical adapter boundary connecting:
- OLA-038 persisted-cycle canonical cohort bundle
to:
- OLA-037 post-persistence lineage cycle coordinator

Purpose:
- consume one immutable OLA-038 bundle
- derive OLA-037 persistence evidence without reinterpreting cycle semantics
- pass the exact OLA-038 CanonicalObservation cohort into OLA-037
- preserve acquisition batch identity, canonical count, persistence count,
  cycle completion time, and upstream OLA-017 identity
- return one immutable deterministic bridge receipt

This boundary performs no acquisition, persistence, intelligence interpretation,
signal scoring, alerting, Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .oracle_persisted_cycle_canonical_cohort_bundle_contract import (
    OraclePersistedCycleCanonicalCohortBundle,
    PersistedCycleCanonicalCohortBundleInvariantError,
)
from .oracle_post_persistence_lineage_cycle_coordinator import (
    OraclePostPersistenceLineageCycleCoordinator,
    PersistedAcquisitionCycleEvidence,
    PostPersistenceLineageCycleContractError,
    PostPersistenceLineageCycleInvariantError,
    PostPersistenceLineageCycleReceipt,
)


SCHEMA_VERSION = "OLA-039"
ENGINE_ID = "OLA-039"
RECEIPT_TYPE = "oracle_persisted_cohort_lineage_bridge_receipt"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PersistedCohortLineageBridgeContractError(ValueError):
    """Raised when OLA-039 bridge input is malformed."""


class PersistedCohortLineageBridgeInvariantError(RuntimeError):
    """Raised when permanent OLA-039 invariants are violated."""


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
class PersistedCohortLineageBridgeReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    bundle_hash: str
    upstream_schema_version: str
    upstream_engine_id: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    cycle_completed_at: str
    coordination_hash: str
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
    bridge_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PersistedCohortLineageBridgeInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise PersistedCohortLineageBridgeInvariantError(
                "engine identity invariant violated"
            )

        if self.receipt_type != RECEIPT_TYPE:
            raise PersistedCohortLineageBridgeInvariantError(
                "receipt type invariant violated"
            )

        if self.upstream_schema_version != "OLA-017":
            raise PersistedCohortLineageBridgeInvariantError(
                "upstream schema identity invariant violated"
            )

        if self.upstream_engine_id != "OLA-017":
            raise PersistedCohortLineageBridgeInvariantError(
                "upstream engine identity invariant violated"
            )

        if self.canonical_count <= 0:
            raise PersistedCohortLineageBridgeInvariantError(
                "canonical count must be positive"
            )

        if self.persistence_count != self.canonical_count:
            raise PersistedCohortLineageBridgeInvariantError(
                "persistence equality invariant violated"
            )

        if self.lineage_record_count_after < self.canonical_count:
            raise PersistedCohortLineageBridgeInvariantError(
                "lineage record count cannot trail canonical count"
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
            raise PersistedCohortLineageBridgeInvariantError(
                "OLA-039 read-only authority invariants violated"
            )


class OraclePersistedCohortLineageBridge:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        coordinator: (
            OraclePostPersistenceLineageCycleCoordinator | None
        ) = None,
    ) -> None:
        self._coordinator = (
            coordinator
            if coordinator is not None
            else OraclePostPersistenceLineageCycleCoordinator()
        )

        if not isinstance(
            self._coordinator,
            OraclePostPersistenceLineageCycleCoordinator,
        ):
            raise PersistedCohortLineageBridgeContractError(
                "coordinator must be an OLA-037 "
                "OraclePostPersistenceLineageCycleCoordinator"
            )

    @property
    def coordinator(
        self,
    ) -> OraclePostPersistenceLineageCycleCoordinator:
        return self._coordinator

    def advance(
        self,
        *,
        bundle: OraclePersistedCycleCanonicalCohortBundle,
    ) -> PersistedCohortLineageBridgeReceipt:
        if not isinstance(
            bundle,
            OraclePersistedCycleCanonicalCohortBundle,
        ):
            raise PersistedCohortLineageBridgeContractError(
                "bundle must be an OLA-038 "
                "OraclePersistedCycleCanonicalCohortBundle"
            )

        try:
            bundle.assert_invariants()
        except PersistedCycleCanonicalCohortBundleInvariantError as exc:
            raise PersistedCohortLineageBridgeInvariantError(
                f"OLA-038 bundle invariant failed: {exc}"
            ) from exc

        evidence = PersistedAcquisitionCycleEvidence.create(
            schema_version=bundle.upstream_schema_version,
            engine_id=bundle.upstream_engine_id,
            cycle_status=bundle.cycle_status,
            acquisition_batch_id=bundle.acquisition_batch_id,
            canonical_count=bundle.canonical_count,
            persistence_count=bundle.persistence_count,
            cycle_completed_at=bundle.cycle_completed_at,
            read_only=bundle.read_only,
            execution_allowed=bundle.execution_allowed,
        )

        try:
            coordination = self._coordinator.coordinate(
                cycle_evidence=evidence,
                canonical_observations=bundle.canonical_observations,
            )
        except PostPersistenceLineageCycleContractError as exc:
            raise PersistedCohortLineageBridgeContractError(
                f"OLA-037 coordinator rejected bundle: {exc}"
            ) from exc
        except PostPersistenceLineageCycleInvariantError as exc:
            raise PersistedCohortLineageBridgeInvariantError(
                f"OLA-037 coordinator invariant failed: {exc}"
            ) from exc

        self._assert_binding(
            bundle=bundle,
            coordination=coordination,
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "bundle_hash": bundle.bundle_hash,
            "upstream_schema_version": bundle.upstream_schema_version,
            "upstream_engine_id": bundle.upstream_engine_id,
            "acquisition_batch_id": bundle.acquisition_batch_id,
            "canonical_count": bundle.canonical_count,
            "persistence_count": bundle.persistence_count,
            "cycle_completed_at": bundle.cycle_completed_at.isoformat(),
            "coordination_hash": coordination.coordination_hash,
            "transition_count": coordination.transition_count,
            "lineage_market_count_after": (
                coordination.lineage_market_count_after
            ),
            "lineage_record_count_after": (
                coordination.lineage_record_count_after
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

        receipt = PersistedCohortLineageBridgeReceipt(
            **payload,
            bridge_hash=_stable_hash(payload),
        )

        receipt.assert_invariants()
        return receipt

    @staticmethod
    def _assert_binding(
        *,
        bundle: OraclePersistedCycleCanonicalCohortBundle,
        coordination: PostPersistenceLineageCycleReceipt,
    ) -> None:
        if (
            coordination.upstream_schema_version
            != bundle.upstream_schema_version
        ):
            raise PersistedCohortLineageBridgeInvariantError(
                "upstream schema binding invariant violated"
            )

        if (
            coordination.upstream_engine_id
            != bundle.upstream_engine_id
        ):
            raise PersistedCohortLineageBridgeInvariantError(
                "upstream engine binding invariant violated"
            )

        if (
            coordination.acquisition_batch_id
            != bundle.acquisition_batch_id
        ):
            raise PersistedCohortLineageBridgeInvariantError(
                "acquisition batch binding invariant violated"
            )

        if coordination.canonical_count != bundle.canonical_count:
            raise PersistedCohortLineageBridgeInvariantError(
                "canonical count binding invariant violated"
            )

        if coordination.persistence_count != bundle.persistence_count:
            raise PersistedCohortLineageBridgeInvariantError(
                "persistence count binding invariant violated"
            )

        if (
            coordination.cycle_completed_at
            != bundle.cycle_completed_at.isoformat()
        ):
            raise PersistedCohortLineageBridgeInvariantError(
                "cycle completion clock binding invariant violated"
            )
