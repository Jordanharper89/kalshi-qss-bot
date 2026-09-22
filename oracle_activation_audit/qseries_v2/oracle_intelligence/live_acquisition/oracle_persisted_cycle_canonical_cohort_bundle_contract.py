"""
OLA-038
Oracle Persisted Cycle Canonical Cohort Bundle Contract

Canonical carrier boundary between successful OLA-017 persistence evidence and
the exact CanonicalObservation cohort that produced that persisted cycle.

Purpose:
- bind one successful OLA-017 cycle result to the exact canonical observations
- require OLA-017 cycle_status == completed
- require PostgreSQL routing record delta == canonical observation count
- require one acquisition_batch_id across the exact canonical cohort
- bind cycle_completed_at to the persisted-cycle bundle
- preserve exact immutable CanonicalObservation objects for OLA-037
- expose deterministic canonical metadata without serializing observation
  objects into scheduler kwargs

This boundary does not alter OLA-021 scheduler canonicalization.
It does not perform acquisition, persistence, intelligence interpretation,
signal scoring, alerting, Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-038"
ENGINE_ID = "OLA-038"
BUNDLE_TYPE = "oracle_persisted_cycle_canonical_cohort_bundle"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PersistedCycleCanonicalCohortBundleContractError(ValueError):
    """Raised when OLA-038 bundle input is malformed."""


class PersistedCycleCanonicalCohortBundleInvariantError(RuntimeError):
    """Raised when permanent OLA-038 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PersistedCycleCanonicalCohortBundleContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PersistedCycleCanonicalCohortBundleContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistedCycleCanonicalCohortBundleContractError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise PersistedCycleCanonicalCohortBundleContractError(
            f"{field_name} must not be negative"
        )

    return value


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PersistedCycleCanonicalCohortBundleContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None:
        raise PersistedCycleCanonicalCohortBundleContractError(
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


def _cycle_payload(
    cycle_result: Any,
) -> dict[str, Any]:
    if hasattr(
        cycle_result,
        "to_canonical_dict",
    ):
        payload = cycle_result.to_canonical_dict()
    elif isinstance(cycle_result, Mapping):
        payload = cycle_result
    else:
        raise PersistedCycleCanonicalCohortBundleContractError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if not isinstance(payload, Mapping):
        raise PersistedCycleCanonicalCohortBundleContractError(
            "OLA-017 canonical cycle evidence must be a mapping"
        )

    return dict(payload)


@dataclass(frozen=True, slots=True)
class OraclePersistedCycleCanonicalCohortBundle:
    schema_version: str
    engine_id: str
    bundle_type: str
    upstream_schema_version: str
    upstream_engine_id: str
    cycle_status: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    cycle_completed_at: datetime
    canonical_observations: tuple[CanonicalObservation, ...]
    observation_ids: tuple[str, ...]
    source_market_ids: tuple[str, ...]
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    bundle_hash: str

    @classmethod
    def create(
        cls,
        *,
        ola_017_cycle_result: Any,
        canonical_observations: Sequence[CanonicalObservation],
        cycle_completed_at: datetime,
    ) -> "OraclePersistedCycleCanonicalCohortBundle":
        cycle_payload = _cycle_payload(
            ola_017_cycle_result
        )

        upstream_schema_version = _require_non_empty_string(
            cycle_payload.get("schema_version"),
            "ola_017_cycle_result.schema_version",
        )
        upstream_engine_id = _require_non_empty_string(
            cycle_payload.get("engine_id"),
            "ola_017_cycle_result.engine_id",
        )

        if upstream_schema_version != "OLA-017":
            raise PersistedCycleCanonicalCohortBundleContractError(
                "upstream schema_version must be OLA-017"
            )

        if upstream_engine_id != "OLA-017":
            raise PersistedCycleCanonicalCohortBundleContractError(
                "upstream engine_id must be OLA-017"
            )

        cycle_status = _require_non_empty_string(
            cycle_payload.get(
                "cycle_status",
                cycle_payload.get("status"),
            ),
            "ola_017_cycle_result.cycle_status",
        )

        if cycle_status != "completed":
            raise PersistedCycleCanonicalCohortBundleContractError(
                "only completed OLA-017 cycles can form a persisted bundle"
            )

        canonical_count = _require_non_negative_int(
            cycle_payload.get("canonical_count"),
            "ola_017_cycle_result.canonical_count",
        )

        persistence_count = _require_non_negative_int(
            cycle_payload.get(
                "postgresql_routing_record_delta",
                cycle_payload.get(
                    "postgresql_persistence_count"
                ),
            ),
            "ola_017_cycle_result.postgresql_routing_record_delta",
        )

        if canonical_count <= 0:
            raise PersistedCycleCanonicalCohortBundleContractError(
                "canonical_count must be positive"
            )

        if persistence_count != canonical_count:
            raise PersistedCycleCanonicalCohortBundleContractError(
                "PostgreSQL persistence count must equal canonical_count"
            )

        upstream_read_only = cycle_payload.get("read_only")

        if upstream_read_only is not True:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "OLA-017 cycle result lost read-only invariant"
            )

        upstream_execution_allowed = cycle_payload.get(
            "execution_allowed"
        )

        if upstream_execution_allowed is not False:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "OLA-017 cycle result gained execution capability"
            )

        observations = tuple(canonical_observations)

        if len(observations) != canonical_count:
            raise PersistedCycleCanonicalCohortBundleContractError(
                "exact canonical cohort count must equal OLA-017 canonical_count"
            )

        completed_at = _require_utc_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )

        batch_ids: set[str] = set()
        observation_ids: list[str] = []
        observation_id_set: set[str] = set()
        source_market_ids: list[str] = []
        source_market_id_set: set[str] = set()

        for observation in observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise PersistedCycleCanonicalCohortBundleContractError(
                    "canonical cohort must contain CanonicalObservation records"
                )

            if observation.observation_type != "market_snapshot":
                raise PersistedCycleCanonicalCohortBundleContractError(
                    "OLA-038 accepts only market_snapshot observations"
                )

            batch_id = _require_non_empty_string(
                observation.acquisition_batch_id,
                "observation.acquisition_batch_id",
            )
            observation_id = _require_non_empty_string(
                observation.observation_id,
                "observation.observation_id",
            )

            if observation_id in observation_id_set:
                raise PersistedCycleCanonicalCohortBundleContractError(
                    "duplicate observation_id within canonical cohort"
                )

            payload = dict(observation.payload)

            source_market_id = _require_non_empty_string(
                payload.get("source_market_id"),
                "observation.payload.source_market_id",
            )

            if source_market_id in source_market_id_set:
                raise PersistedCycleCanonicalCohortBundleContractError(
                    "duplicate source_market_id within canonical cohort"
                )

            batch_ids.add(batch_id)
            observation_id_set.add(observation_id)
            observation_ids.append(observation_id)
            source_market_id_set.add(source_market_id)
            source_market_ids.append(source_market_id)

        if len(batch_ids) != 1:
            raise PersistedCycleCanonicalCohortBundleContractError(
                "canonical cohort must share one acquisition_batch_id"
            )

        acquisition_batch_id = next(iter(batch_ids))

        metadata_payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "bundle_type": BUNDLE_TYPE,
            "upstream_schema_version": upstream_schema_version,
            "upstream_engine_id": upstream_engine_id,
            "cycle_status": cycle_status,
            "acquisition_batch_id": acquisition_batch_id,
            "canonical_count": canonical_count,
            "persistence_count": persistence_count,
            "cycle_completed_at": completed_at.isoformat(),
            "observation_ids": observation_ids,
            "source_market_ids": source_market_ids,
            "observation_content_hashes": [
                observation.content_hash
                for observation in observations
            ],
            "observation_replay_hashes": [
                observation.replay_hash
                for observation in observations
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

        bundle = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            bundle_type=BUNDLE_TYPE,
            upstream_schema_version=upstream_schema_version,
            upstream_engine_id=upstream_engine_id,
            cycle_status=cycle_status,
            acquisition_batch_id=acquisition_batch_id,
            canonical_count=canonical_count,
            persistence_count=persistence_count,
            cycle_completed_at=completed_at,
            canonical_observations=observations,
            observation_ids=tuple(observation_ids),
            source_market_ids=tuple(source_market_ids),
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            bundle_hash=_stable_hash(metadata_payload),
        )

        bundle.assert_invariants()
        return bundle

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "engine identity invariant violated"
            )

        if self.bundle_type != BUNDLE_TYPE:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "bundle type invariant violated"
            )

        if self.upstream_schema_version != "OLA-017":
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "upstream schema invariant violated"
            )

        if self.upstream_engine_id != "OLA-017":
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "upstream engine invariant violated"
            )

        if self.cycle_status != "completed":
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "cycle completion invariant violated"
            )

        if self.canonical_count != len(
            self.canonical_observations
        ):
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "canonical cohort count invariant violated"
            )

        if self.persistence_count != self.canonical_count:
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "persistence equality invariant violated"
            )

        if self.observation_ids != tuple(
            observation.observation_id
            for observation in self.canonical_observations
        ):
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "observation identity ordering invariant violated"
            )

        if len(set(self.observation_ids)) != len(
            self.observation_ids
        ):
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "observation identity uniqueness invariant violated"
            )

        if len(set(self.source_market_ids)) != len(
            self.source_market_ids
        ):
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "market identity uniqueness invariant violated"
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
            raise PersistedCycleCanonicalCohortBundleInvariantError(
                "OLA-038 read-only authority invariants violated"
            )

    def to_canonical_metadata(
        self,
    ) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "bundle_type": self.bundle_type,
                "upstream_schema_version": (
                    self.upstream_schema_version
                ),
                "upstream_engine_id": self.upstream_engine_id,
                "cycle_status": self.cycle_status,
                "acquisition_batch_id": self.acquisition_batch_id,
                "canonical_count": self.canonical_count,
                "persistence_count": self.persistence_count,
                "cycle_completed_at": (
                    self.cycle_completed_at.isoformat()
                ),
                "observation_ids": self.observation_ids,
                "source_market_ids": self.source_market_ids,
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
                "bundle_hash": self.bundle_hash,
            }
        )
