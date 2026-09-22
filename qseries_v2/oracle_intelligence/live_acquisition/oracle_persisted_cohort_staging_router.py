"""
OLA-042
Oracle Persisted Cohort Staging Router

Canonical production integration boundary around the existing PostgreSQL
canonical observation persistence router.

Purpose:
- delegate canonical observation routing to the existing persistence router
- preserve the exact CanonicalObservation objects presented to route_batch
- stage the exact cohort only after successful delegated atomic batch routing
- key staged cohorts by acquisition_batch_id
- never promote staged cohorts into OLA-040 capture by itself
- allow later OLA-017 completion reconciliation to promote the exact staged
  cohort through OLA-041

This boundary does not own PostgreSQL persistence semantics.
It does not weaken OLA-015 routing.
It does not perform lineage advancement.
It does not interpret intelligence, score signals, alert, hand off to Q Series,
authorize trading, place orders, move funds, or mutate portfolios.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from threading import RLock
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    ObservationRoutingEvidence,
)


SCHEMA_VERSION = "OLA-042"
ENGINE_ID = "OLA-042"
STAGE_TYPE = "oracle_persisted_canonical_cohort_stage"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PersistedCohortStagingRouterContractError(ValueError):
    """Raised when OLA-042 staging input is malformed."""


class PersistedCohortStagingRouterInvariantError(RuntimeError):
    """Raised when permanent OLA-042 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PersistedCohortStagingRouterContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PersistedCohortStagingRouterContractError(
            f"{field_name} must not be empty"
        )

    return normalized


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
class PersistedCanonicalCohortStage:
    schema_version: str
    engine_id: str
    stage_type: str
    acquisition_batch_id: str
    canonical_count: int
    canonical_observations: tuple[CanonicalObservation, ...]
    observation_ids: tuple[str, ...]
    source_market_ids: tuple[str, ...]
    delegated_routing_evidence: tuple[ObservationRoutingEvidence, ...]
    routing_evidence_observation_ids: tuple[str, ...]
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    stage_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PersistedCohortStagingRouterInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise PersistedCohortStagingRouterInvariantError(
                "engine identity invariant violated"
            )

        if self.stage_type != STAGE_TYPE:
            raise PersistedCohortStagingRouterInvariantError(
                "stage type invariant violated"
            )

        if self.canonical_count <= 0:
            raise PersistedCohortStagingRouterInvariantError(
                "canonical count must be positive"
            )

        if self.canonical_count != len(
            self.canonical_observations
        ):
            raise PersistedCohortStagingRouterInvariantError(
                "canonical observation count invariant violated"
            )

        if self.canonical_count != len(
            self.delegated_routing_evidence
        ):
            raise PersistedCohortStagingRouterInvariantError(
                "routing evidence count invariant violated"
            )

        if self.observation_ids != tuple(
            observation.observation_id
            for observation in self.canonical_observations
        ):
            raise PersistedCohortStagingRouterInvariantError(
                "observation ordering invariant violated"
            )

        if (
            self.routing_evidence_observation_ids
            != self.observation_ids
        ):
            raise PersistedCohortStagingRouterInvariantError(
                "routing evidence identity ordering invariant violated"
            )

        if len(set(self.observation_ids)) != self.canonical_count:
            raise PersistedCohortStagingRouterInvariantError(
                "observation identity uniqueness invariant violated"
            )

        if len(set(self.source_market_ids)) != self.canonical_count:
            raise PersistedCohortStagingRouterInvariantError(
                "market identity uniqueness invariant violated"
            )

        if any(
            evidence.accepted is not True
            for evidence in self.delegated_routing_evidence
        ):
            raise PersistedCohortStagingRouterInvariantError(
                "staged cohort contains rejected routing evidence"
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
            raise PersistedCohortStagingRouterInvariantError(
                "OLA-042 read-only authority invariants violated"
            )

    def to_canonical_metadata(
        self,
    ) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "stage_type": self.stage_type,
                "acquisition_batch_id": self.acquisition_batch_id,
                "canonical_count": self.canonical_count,
                "observation_ids": self.observation_ids,
                "source_market_ids": self.source_market_ids,
                "routing_evidence_observation_ids": (
                    self.routing_evidence_observation_ids
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
                "stage_hash": self.stage_hash,
            }
        )


class OraclePersistedCohortStagingRouter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        persistence_router: Any,
    ) -> None:
        route_batch = getattr(
            persistence_router,
            "route_batch",
            None,
        )

        if not callable(route_batch):
            raise PersistedCohortStagingRouterContractError(
                "persistence_router must expose callable route_batch"
            )

        self._persistence_router = persistence_router
        self._lock = RLock()
        self._pending: dict[
            str,
            PersistedCanonicalCohortStage,
        ] = {}
        self._consumed_batch_ids: set[str] = set()

    @property
    def persistence_router(self) -> Any:
        return self._persistence_router

    def __call__(
        self,
        observation: CanonicalObservation,
        routed_at: Any,
    ) -> ObservationRoutingEvidence:
        route = getattr(
            self._persistence_router,
            "__call__",
            None,
        )

        if not callable(route):
            raise PersistedCohortStagingRouterContractError(
                "persistence_router must remain callable"
            )

        return route(
            observation,
            routed_at,
        )

    def route_batch(
        self,
        observations: Sequence[CanonicalObservation],
        routed_at: Any,
    ) -> tuple[ObservationRoutingEvidence, ...]:
        canonical_observations = tuple(observations)

        if not canonical_observations:
            raise PersistedCohortStagingRouterContractError(
                "route_batch observations must not be empty"
            )

        batch_ids: set[str] = set()
        observation_ids: list[str] = []
        observation_id_set: set[str] = set()
        source_market_ids: list[str] = []
        source_market_id_set: set[str] = set()

        for observation in canonical_observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise PersistedCohortStagingRouterContractError(
                    "route_batch requires CanonicalObservation records"
                )

            if observation.observation_type != "market_snapshot":
                raise PersistedCohortStagingRouterContractError(
                    "OLA-042 accepts only market_snapshot observations"
                )

            batch_id = _require_non_empty_string(
                observation.acquisition_batch_id,
                "observation.acquisition_batch_id",
            )
            observation_id = _require_non_empty_string(
                observation.observation_id,
                "observation.observation_id",
            )

            payload = dict(observation.payload)
            source_market_id = _require_non_empty_string(
                payload.get("source_market_id"),
                "observation.payload.source_market_id",
            )

            if observation_id in observation_id_set:
                raise PersistedCohortStagingRouterContractError(
                    "duplicate observation_id within batch"
                )

            if source_market_id in source_market_id_set:
                raise PersistedCohortStagingRouterContractError(
                    "duplicate source_market_id within batch"
                )

            batch_ids.add(batch_id)
            observation_id_set.add(observation_id)
            observation_ids.append(observation_id)
            source_market_id_set.add(source_market_id)
            source_market_ids.append(source_market_id)

        if len(batch_ids) != 1:
            raise PersistedCohortStagingRouterContractError(
                "batch must share one acquisition_batch_id"
            )

        acquisition_batch_id = next(iter(batch_ids))

        with self._lock:
            if acquisition_batch_id in self._pending:
                raise PersistedCohortStagingRouterContractError(
                    "acquisition batch already staged"
                )

            if acquisition_batch_id in self._consumed_batch_ids:
                raise PersistedCohortStagingRouterContractError(
                    "consumed acquisition batch cannot be restaged"
                )

        delegated = self._persistence_router.route_batch(
            canonical_observations,
            routed_at,
        )

        if not isinstance(delegated, tuple):
            try:
                delegated = tuple(delegated)
            except TypeError as exc:
                raise PersistedCohortStagingRouterInvariantError(
                    "delegated route_batch returned non-iterable evidence"
                ) from exc

        if len(delegated) != len(canonical_observations):
            raise PersistedCohortStagingRouterInvariantError(
                "delegated routing evidence count mismatch"
            )

        evidence_by_observation_id: dict[
            str,
            ObservationRoutingEvidence,
        ] = {}

        for evidence in delegated:
            if not isinstance(
                evidence,
                ObservationRoutingEvidence,
            ):
                raise PersistedCohortStagingRouterInvariantError(
                    "delegated route_batch returned incompatible evidence"
                )

            if evidence.accepted is not True:
                raise PersistedCohortStagingRouterInvariantError(
                    "delegated route_batch returned rejected evidence"
                )

            if evidence.observation_id in evidence_by_observation_id:
                raise PersistedCohortStagingRouterInvariantError(
                    "duplicate delegated routing evidence identity"
                )

            evidence_by_observation_id[
                evidence.observation_id
            ] = evidence

        if set(evidence_by_observation_id) != set(observation_ids):
            raise PersistedCohortStagingRouterInvariantError(
                "delegated routing evidence identity set mismatch"
            )

        ordered_evidence = tuple(
            evidence_by_observation_id[observation_id]
            for observation_id in observation_ids
        )

        metadata_payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "stage_type": STAGE_TYPE,
            "acquisition_batch_id": acquisition_batch_id,
            "canonical_count": len(canonical_observations),
            "observation_ids": observation_ids,
            "source_market_ids": source_market_ids,
            "content_hashes": [
                observation.content_hash
                for observation in canonical_observations
            ],
            "replay_hashes": [
                observation.replay_hash
                for observation in canonical_observations
            ],
            "routing_evidence_observation_ids": [
                evidence.observation_id
                for evidence in ordered_evidence
            ],
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        stage = PersistedCanonicalCohortStage(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            stage_type=STAGE_TYPE,
            acquisition_batch_id=acquisition_batch_id,
            canonical_count=len(canonical_observations),
            canonical_observations=canonical_observations,
            observation_ids=tuple(observation_ids),
            source_market_ids=tuple(source_market_ids),
            delegated_routing_evidence=ordered_evidence,
            routing_evidence_observation_ids=tuple(
                evidence.observation_id
                for evidence in ordered_evidence
            ),
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            stage_hash=_stable_hash(metadata_payload),
        )

        stage.assert_invariants()

        with self._lock:
            if acquisition_batch_id in self._pending:
                raise PersistedCohortStagingRouterInvariantError(
                    "staging race detected for acquisition batch"
                )

            self._pending[acquisition_batch_id] = stage

        return ordered_evidence

    def consume_stage(
        self,
        *,
        acquisition_batch_id: str,
    ) -> PersistedCanonicalCohortStage:
        batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        with self._lock:
            if batch_id in self._consumed_batch_ids:
                raise PersistedCohortStagingRouterContractError(
                    "acquisition batch stage already consumed"
                )

            stage = self._pending.pop(
                batch_id,
                None,
            )

            if stage is None:
                raise PersistedCohortStagingRouterContractError(
                    "no pending persisted cohort stage for batch"
                )

            stage.assert_invariants()
            self._consumed_batch_ids.add(batch_id)

        return stage

    def peek_stage_metadata(
        self,
        *,
        acquisition_batch_id: str,
    ) -> Mapping[str, Any] | None:
        batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        with self._lock:
            stage = self._pending.get(batch_id)

            if stage is None:
                return None

            return stage.to_canonical_metadata()

    @property
    def pending_stage_count(self) -> int:
        with self._lock:
            return len(self._pending)

    @property
    def consumed_stage_count(self) -> int:
        with self._lock:
            return len(self._consumed_batch_ids)
