"""
OLA-040
Oracle Canonical Persisted Cohort Capture Port

In-process exact-object handoff boundary for one successfully persisted
canonical acquisition cohort.

Purpose:
- capture the exact CanonicalObservation objects produced by the OLA-017 cycle
  before scheduler result projection removes non-canonical objects
- key captures by acquisition_batch_id
- preserve exact observation ordering and object identity
- enforce one write per acquisition batch
- enforce one consume per acquisition batch
- expose immutable metadata for audit without serializing observation objects
  into scheduler kwargs or scheduler results

This is a capture port only. It does not perform persistence, lineage,
intelligence interpretation, scoring, alerting, Q Series handoff,
authorization, or execution.

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
)


SCHEMA_VERSION = "OLA-040"
ENGINE_ID = "OLA-040"
CAPTURE_TYPE = "oracle_canonical_persisted_cohort_capture"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class CanonicalPersistedCohortCaptureContractError(ValueError):
    """Raised when OLA-040 capture input is malformed."""


class CanonicalPersistedCohortCaptureInvariantError(RuntimeError):
    """Raised when permanent OLA-040 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise CanonicalPersistedCohortCaptureContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise CanonicalPersistedCohortCaptureContractError(
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
class CanonicalPersistedCohortCapture:
    schema_version: str
    engine_id: str
    capture_type: str
    acquisition_batch_id: str
    canonical_count: int
    canonical_observations: tuple[CanonicalObservation, ...]
    observation_ids: tuple[str, ...]
    source_market_ids: tuple[str, ...]
    content_hashes: tuple[str, ...]
    replay_hashes: tuple[str, ...]
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    capture_hash: str

    @classmethod
    def create(
        cls,
        *,
        canonical_observations: Sequence[CanonicalObservation],
    ) -> "CanonicalPersistedCohortCapture":
        observations = tuple(canonical_observations)

        if not observations:
            raise CanonicalPersistedCohortCaptureContractError(
                "canonical_observations must not be empty"
            )

        batch_ids: set[str] = set()
        observation_ids: list[str] = []
        observation_id_set: set[str] = set()
        source_market_ids: list[str] = []
        source_market_id_set: set[str] = set()
        content_hashes: list[str] = []
        replay_hashes: list[str] = []

        for observation in observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise CanonicalPersistedCohortCaptureContractError(
                    "capture requires CanonicalObservation records"
                )

            if observation.observation_type != "market_snapshot":
                raise CanonicalPersistedCohortCaptureContractError(
                    "OLA-040 accepts only market_snapshot observations"
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
                raise CanonicalPersistedCohortCaptureContractError(
                    "duplicate observation_id within capture"
                )

            if source_market_id in source_market_id_set:
                raise CanonicalPersistedCohortCaptureContractError(
                    "duplicate source_market_id within capture"
                )

            batch_ids.add(batch_id)
            observation_id_set.add(observation_id)
            source_market_id_set.add(source_market_id)
            observation_ids.append(observation_id)
            source_market_ids.append(source_market_id)
            content_hashes.append(
                _require_non_empty_string(
                    observation.content_hash,
                    "observation.content_hash",
                )
            )
            replay_hashes.append(
                _require_non_empty_string(
                    observation.replay_hash,
                    "observation.replay_hash",
                )
            )

        if len(batch_ids) != 1:
            raise CanonicalPersistedCohortCaptureContractError(
                "captured cohort must share one acquisition_batch_id"
            )

        acquisition_batch_id = next(iter(batch_ids))

        metadata_payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "capture_type": CAPTURE_TYPE,
            "acquisition_batch_id": acquisition_batch_id,
            "canonical_count": len(observations),
            "observation_ids": observation_ids,
            "source_market_ids": source_market_ids,
            "content_hashes": content_hashes,
            "replay_hashes": replay_hashes,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        capture = cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            capture_type=CAPTURE_TYPE,
            acquisition_batch_id=acquisition_batch_id,
            canonical_count=len(observations),
            canonical_observations=observations,
            observation_ids=tuple(observation_ids),
            source_market_ids=tuple(source_market_ids),
            content_hashes=tuple(content_hashes),
            replay_hashes=tuple(replay_hashes),
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            capture_hash=_stable_hash(metadata_payload),
        )

        capture.assert_invariants()
        return capture

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "engine identity invariant violated"
            )

        if self.capture_type != CAPTURE_TYPE:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "capture type invariant violated"
            )

        if self.canonical_count <= 0:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "canonical count must be positive"
            )

        if self.canonical_count != len(
            self.canonical_observations
        ):
            raise CanonicalPersistedCohortCaptureInvariantError(
                "canonical observation count invariant violated"
            )

        if len(self.observation_ids) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "observation identity count invariant violated"
            )

        if len(self.source_market_ids) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "market identity count invariant violated"
            )

        if len(self.content_hashes) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "content hash count invariant violated"
            )

        if len(self.replay_hashes) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "replay hash count invariant violated"
            )

        if len(set(self.observation_ids)) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "observation identity uniqueness invariant violated"
            )

        if len(set(self.source_market_ids)) != self.canonical_count:
            raise CanonicalPersistedCohortCaptureInvariantError(
                "market identity uniqueness invariant violated"
            )

        if self.observation_ids != tuple(
            observation.observation_id
            for observation in self.canonical_observations
        ):
            raise CanonicalPersistedCohortCaptureInvariantError(
                "exact observation ordering invariant violated"
            )

        if self.content_hashes != tuple(
            observation.content_hash
            for observation in self.canonical_observations
        ):
            raise CanonicalPersistedCohortCaptureInvariantError(
                "content hash binding invariant violated"
            )

        if self.replay_hashes != tuple(
            observation.replay_hash
            for observation in self.canonical_observations
        ):
            raise CanonicalPersistedCohortCaptureInvariantError(
                "replay hash binding invariant violated"
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
            raise CanonicalPersistedCohortCaptureInvariantError(
                "OLA-040 read-only authority invariants violated"
            )

    def to_canonical_metadata(
        self,
    ) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "engine_id": self.engine_id,
                "capture_type": self.capture_type,
                "acquisition_batch_id": self.acquisition_batch_id,
                "canonical_count": self.canonical_count,
                "observation_ids": self.observation_ids,
                "source_market_ids": self.source_market_ids,
                "content_hashes": self.content_hashes,
                "replay_hashes": self.replay_hashes,
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
                "capture_hash": self.capture_hash,
            }
        )


class OracleCanonicalPersistedCohortCapturePort:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lock = RLock()
        self._pending: dict[
            str,
            CanonicalPersistedCohortCapture,
        ] = {}
        self._consumed_batch_ids: set[str] = set()

    def capture(
        self,
        *,
        canonical_observations: Sequence[CanonicalObservation],
    ) -> CanonicalPersistedCohortCapture:
        capture = CanonicalPersistedCohortCapture.create(
            canonical_observations=canonical_observations,
        )

        batch_id = capture.acquisition_batch_id

        with self._lock:
            if batch_id in self._pending:
                raise CanonicalPersistedCohortCaptureContractError(
                    "acquisition batch already captured"
                )

            if batch_id in self._consumed_batch_ids:
                raise CanonicalPersistedCohortCaptureContractError(
                    "consumed acquisition batch cannot be recaptured"
                )

            self._pending[batch_id] = capture

        return capture

    def consume(
        self,
        *,
        acquisition_batch_id: str,
    ) -> CanonicalPersistedCohortCapture:
        batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        with self._lock:
            if batch_id in self._consumed_batch_ids:
                raise CanonicalPersistedCohortCaptureContractError(
                    "acquisition batch already consumed"
                )

            capture = self._pending.pop(
                batch_id,
                None,
            )

            if capture is None:
                raise CanonicalPersistedCohortCaptureContractError(
                    "no pending canonical cohort capture for batch"
                )

            capture.assert_invariants()
            self._consumed_batch_ids.add(batch_id)

        return capture

    def peek_metadata(
        self,
        *,
        acquisition_batch_id: str,
    ) -> Mapping[str, Any] | None:
        batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        with self._lock:
            capture = self._pending.get(batch_id)

            if capture is None:
                return None

            return capture.to_canonical_metadata()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    @property
    def consumed_count(self) -> int:
        with self._lock:
            return len(self._consumed_batch_ids)


_GLOBAL_CAPTURE_PORT = OracleCanonicalPersistedCohortCapturePort()


def canonical_persisted_cohort_capture_port(
) -> OracleCanonicalPersistedCohortCapturePort:
    return _GLOBAL_CAPTURE_PORT
