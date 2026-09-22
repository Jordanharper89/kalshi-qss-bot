"""
OLA-009
Oracle Canonical Observation Persistence Router

Canonical read-only bridge between the OLA-001 canonical observation
routing contract and the OLA-008 append-only persistence ledger.

Architecture:

OLA-001 ACQUISITION
    |
CANONICAL OBSERVATION
    |
OLA-003 DEDUPLICATION
    |
OLA-009 PERSISTENCE ROUTER
    |
OLA-008 APPEND-ONLY PERSISTENCE LEDGER
    |
OLA-001 ROUTING EVIDENCE

Permanent rules:

- Only CanonicalObservation records may be routed.
- routed_at is caller supplied by OLA-001.
- Persistence occurs before accepted routing evidence is emitted.
- Successful persistence entry identity is preserved.
- Persistence sequence identity is preserved.
- Persistence chain identity is preserved.
- Observation identity is preserved.
- Source identity is preserved.
- Content hash is preserved.
- Replay hash is preserved.
- Duplicate persistence conflicts fail closed.
- Persistence failures fail closed.
- Routing evidence is accepted only after validated persistence.
- No alternate non-persistent success path exists.
- No default persistence backend exists.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
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


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    JSONValue,
    ObservationRoutingEvidence,
)

from .oracle_canonical_observation_persistence_ledger import (
    CanonicalObservationPersistenceEntry,
    ObservationPersistenceConflictError,
    ObservationPersistenceContractError,
    ObservationPersistenceInvariantError,
    OracleCanonicalObservationPersistenceLedger,
)


SCHEMA_VERSION = "OLA-009"
ENGINE_ID = "OLA-009"

PERSISTENCE_ROUTING_RECORD_TYPE = (
    "canonical_observation_persistence_routing_record"
)


class PersistenceRoutingContractError(ValueError):
    """Raised when persistence routing contract data is malformed."""


class PersistenceRoutingFailure(RuntimeError):
    """Raised when canonical persistence routing fails closed."""


class PersistenceRoutingInvariantError(RuntimeError):
    """Raised when permanent persistence routing invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PersistenceRoutingContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PersistenceRoutingContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PersistenceRoutingContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PersistenceRoutingContractError(
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
            raise PersistenceRoutingContractError(
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
                raise PersistenceRoutingContractError(
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

    raise PersistenceRoutingContractError(
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
        raise PersistenceRoutingContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PersistenceRoutingContractError(
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
class CanonicalObservationPersistenceRoutingRecord:
    schema_version: str
    engine_id: str
    route_id: str
    observation_id: str
    source_id: str
    acquisition_batch_id: str
    content_hash: str
    observation_replay_hash: str
    routed_at: datetime
    persistence_entry_id: str
    persistence_sequence_number: int
    persistence_entry_hash: str
    persistence_chain_hash: str
    persistence_previous_chain_hash: str
    persistence_verified: bool
    routing_accepted: bool
    persistence_metadata: tuple[
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
    routing_record_hash: str
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
        include_routing_record_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "route_id": self.route_id,
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "acquisition_batch_id": (
                self.acquisition_batch_id
            ),
            "content_hash": self.content_hash,
            "observation_replay_hash": (
                self.observation_replay_hash
            ),
            "routed_at": self.routed_at.isoformat(),
            "persistence_entry_id": (
                self.persistence_entry_id
            ),
            "persistence_sequence_number": (
                self.persistence_sequence_number
            ),
            "persistence_entry_hash": (
                self.persistence_entry_hash
            ),
            "persistence_chain_hash": (
                self.persistence_chain_hash
            ),
            "persistence_previous_chain_hash": (
                self.persistence_previous_chain_hash
            ),
            "persistence_verified": self.persistence_verified,
            "routing_accepted": self.routing_accepted,
            "persistence_metadata": _mapping_from_immutable(
                self.persistence_metadata
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

        if include_routing_record_hash:
            result["routing_record_hash"] = (
                self.routing_record_hash
            )

        return result


class OracleCanonicalObservationPersistenceRouter:
    """
    OLA-001-compatible canonical observation router backed by OLA-008.

    Usage:

        ledger = OracleCanonicalObservationPersistenceLedger()

        router = OracleCanonicalObservationPersistenceRouter(
            persistence_ledger=ledger,
            route_id="oracle.persistence.router.v1",
            persistence_metadata={...},
            replay_metadata={...},
            audit_metadata={...},
        )

        runtime = OracleLiveReadOnlyAcquisitionRuntime(
            ...,
            canonical_observation_router=router,
        )

    The router is callable and matches the OLA-001 router hook contract:

        router(
            observation: CanonicalObservation,
            routed_at: datetime,
        ) -> ObservationRoutingEvidence

    A routing result is accepted only after OLA-008 persistence succeeds
    and the appended persistence entry is independently validated.
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
        persistence_ledger: (
            OracleCanonicalObservationPersistenceLedger
        ),
        route_id: str,
        persistence_metadata: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> None:
        if not isinstance(
            persistence_ledger,
            OracleCanonicalObservationPersistenceLedger,
        ):
            raise PersistenceRoutingContractError(
                "persistence_ledger must be "
                "OracleCanonicalObservationPersistenceLedger"
            )

        self._persistence_ledger = persistence_ledger

        self._route_id = _require_non_empty_string(
            route_id,
            "route_id",
        )

        self._persistence_metadata = _immutable_mapping(
            persistence_metadata,
            "persistence_metadata",
        )

        self._replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        self._audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        self._routing_records: list[
            CanonicalObservationPersistenceRoutingRecord
        ] = []

        self._routing_records_by_observation_id: dict[
            str,
            CanonicalObservationPersistenceRoutingRecord,
        ] = {}

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
            raise PersistenceRoutingInvariantError(
                "Oracle persistence router invariants violated"
            )

        if self._persistence_ledger.read_only is not True:
            raise PersistenceRoutingInvariantError(
                "persistence ledger lost read_only invariant"
            )

        if (
            self._persistence_ledger.execution_allowed
            is not False
        ):
            raise PersistenceRoutingInvariantError(
                "persistence ledger gained execution capability"
            )

    @property
    def route_id(self) -> str:
        return self._route_id

    @property
    def persistence_ledger(
        self,
    ) -> OracleCanonicalObservationPersistenceLedger:
        return self._persistence_ledger

    @property
    def routing_record_count(self) -> int:
        return len(self._routing_records)

    @property
    def routing_records(
        self,
    ) -> tuple[
        CanonicalObservationPersistenceRoutingRecord,
        ...
    ]:
        return tuple(self._routing_records)

    def route(
        self,
        observation: CanonicalObservation,
        routed_at: datetime,
    ) -> ObservationRoutingEvidence:
        self._assert_invariants()

        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise PersistenceRoutingContractError(
                "observation must be CanonicalObservation"
            )

        normalized_routed_at = _require_aware_datetime(
            routed_at,
            "routed_at",
        )

        if normalized_routed_at < observation.acquired_at:
            raise PersistenceRoutingContractError(
                "routed_at cannot be before acquired_at"
            )

        if (
            observation.observation_id
            in self._routing_records_by_observation_id
        ):
            raise PersistenceRoutingFailure(
                "observation_id has already been routed "
                "through persistence router"
            )

        try:
            entry = self._persistence_ledger.append(
                observation=observation,
                persisted_at=normalized_routed_at,
                persistence_metadata=(
                    _mapping_from_immutable(
                        self._persistence_metadata
                    )
                ),
            )
        except (
            ObservationPersistenceConflictError,
            ObservationPersistenceContractError,
            ObservationPersistenceInvariantError,
        ) as exc:
            raise PersistenceRoutingFailure(
                "canonical observation persistence failed closed"
            ) from exc

        self._validate_persistence_entry(
            observation=observation,
            entry=entry,
            routed_at=normalized_routed_at,
        )

        routing_record = self._build_routing_record(
            observation=observation,
            entry=entry,
            routed_at=normalized_routed_at,
        )

        self._routing_records.append(
            routing_record
        )

        self._routing_records_by_observation_id[
            observation.observation_id
        ] = routing_record

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            route_id=self._route_id,
            routed_at=normalized_routed_at,
            accepted=True,
            metadata={
                "router_engine_id": ENGINE_ID,
                "routing_record_hash": (
                    routing_record.routing_record_hash
                ),
                "persistence_verified": True,
                "persistence_entry_id": (
                    entry.persistence_entry_id
                ),
                "persistence_sequence_number": (
                    entry.sequence_number
                ),
                "persistence_entry_hash": (
                    entry.entry_hash
                ),
                "persistence_chain_hash": (
                    entry.chain_hash
                ),
                "persistence_previous_chain_hash": (
                    entry.previous_chain_hash
                ),
                "observation_content_hash": (
                    observation.content_hash
                ),
                "observation_replay_hash": (
                    observation.replay_hash
                ),
                "destination": (
                    "oracle.canonical.persistence"
                ),
            },
        )

    __call__ = route

    @staticmethod
    def _validate_persistence_entry(
        *,
        observation: CanonicalObservation,
        entry: CanonicalObservationPersistenceEntry,
        routed_at: datetime,
    ) -> None:
        if not isinstance(
            entry,
            CanonicalObservationPersistenceEntry,
        ):
            raise PersistenceRoutingFailure(
                "persistence ledger returned incompatible entry"
            )

        if entry.observation_id != observation.observation_id:
            raise PersistenceRoutingFailure(
                "persisted observation identity mismatch"
            )

        if entry.source_id != observation.source_id:
            raise PersistenceRoutingFailure(
                "persisted source identity mismatch"
            )

        if (
            entry.source_observation_id
            != observation.source_observation_id
        ):
            raise PersistenceRoutingFailure(
                "persisted source observation identity mismatch"
            )

        if (
            entry.acquisition_batch_id
            != observation.acquisition_batch_id
        ):
            raise PersistenceRoutingFailure(
                "persisted acquisition batch identity mismatch"
            )

        if entry.content_hash != observation.content_hash:
            raise PersistenceRoutingFailure(
                "persisted content hash mismatch"
            )

        if (
            entry.observation_replay_hash
            != observation.replay_hash
        ):
            raise PersistenceRoutingFailure(
                "persisted replay hash mismatch"
            )

        if entry.persisted_at != routed_at:
            raise PersistenceRoutingFailure(
                "persisted_at does not match routed_at"
            )

        if entry.calculate_entry_hash() != entry.entry_hash:
            raise PersistenceRoutingFailure(
                "persistence entry hash validation failed"
            )

        if entry.calculate_chain_hash() != entry.chain_hash:
            raise PersistenceRoutingFailure(
                "persistence chain hash validation failed"
            )

        if entry.read_only is not True:
            raise PersistenceRoutingFailure(
                "persistence entry lost read_only invariant"
            )

        false_invariants = {
            "execution_allowed": entry.execution_allowed,
            "execution_adapter_resolved": (
                entry.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                entry.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                entry.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                entry.order_placement_allowed
            ),
            "funds_moved": entry.funds_moved,
            "portfolio_mutated": entry.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise PersistenceRoutingFailure(
                "persistence entry gained execution capability"
            )

    def _build_routing_record(
        self,
        *,
        observation: CanonicalObservation,
        entry: CanonicalObservationPersistenceEntry,
        routed_at: datetime,
    ) -> CanonicalObservationPersistenceRoutingRecord:
        provisional = (
            CanonicalObservationPersistenceRoutingRecord(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                route_id=self._route_id,
                observation_id=observation.observation_id,
                source_id=observation.source_id,
                acquisition_batch_id=(
                    observation.acquisition_batch_id
                ),
                content_hash=observation.content_hash,
                observation_replay_hash=(
                    observation.replay_hash
                ),
                routed_at=routed_at,
                persistence_entry_id=(
                    entry.persistence_entry_id
                ),
                persistence_sequence_number=(
                    entry.sequence_number
                ),
                persistence_entry_hash=entry.entry_hash,
                persistence_chain_hash=entry.chain_hash,
                persistence_previous_chain_hash=(
                    entry.previous_chain_hash
                ),
                persistence_verified=True,
                routing_accepted=True,
                persistence_metadata=(
                    self._persistence_metadata
                ),
                replay_metadata=self._replay_metadata,
                audit_metadata=self._audit_metadata,
                routing_record_hash="",
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
        )

        routing_record_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    PERSISTENCE_ROUTING_RECORD_TYPE
                ),
                "routing_record": (
                    provisional.to_canonical_dict(
                        include_routing_record_hash=False
                    )
                ),
            }
        )

        return CanonicalObservationPersistenceRoutingRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            route_id=provisional.route_id,
            observation_id=provisional.observation_id,
            source_id=provisional.source_id,
            acquisition_batch_id=(
                provisional.acquisition_batch_id
            ),
            content_hash=provisional.content_hash,
            observation_replay_hash=(
                provisional.observation_replay_hash
            ),
            routed_at=provisional.routed_at,
            persistence_entry_id=(
                provisional.persistence_entry_id
            ),
            persistence_sequence_number=(
                provisional.persistence_sequence_number
            ),
            persistence_entry_hash=(
                provisional.persistence_entry_hash
            ),
            persistence_chain_hash=(
                provisional.persistence_chain_hash
            ),
            persistence_previous_chain_hash=(
                provisional.persistence_previous_chain_hash
            ),
            persistence_verified=True,
            routing_accepted=True,
            persistence_metadata=(
                provisional.persistence_metadata
            ),
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            routing_record_hash=routing_record_hash,
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

    def get_routing_record(
        self,
        *,
        observation_id: str,
    ) -> CanonicalObservationPersistenceRoutingRecord | None:
        normalized_observation_id = _require_non_empty_string(
            observation_id,
            "observation_id",
        )

        return self._routing_records_by_observation_id.get(
            normalized_observation_id
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PersistenceRoutingContractError",
    "PersistenceRoutingFailure",
    "PersistenceRoutingInvariantError",
    "CanonicalObservationPersistenceRoutingRecord",
    "OracleCanonicalObservationPersistenceRouter",
    "canonical_json",
    "stable_hash",
]
