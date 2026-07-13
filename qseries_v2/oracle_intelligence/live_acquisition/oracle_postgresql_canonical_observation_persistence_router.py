"""
OLA-015
Oracle PostgreSQL Canonical Observation Persistence Router

Production PostgreSQL-backed canonical observation routing boundary.

Architecture:

OLA-001 CANONICAL OBSERVATION
    |
OLA-003 DEDUPLICATION
    |
OLA-015 POSTGRESQL PERSISTENCE ROUTER
    |
OLA-012 POSTGRESQL CANONICAL BACKEND
    |
COMMITTED APPEND RESULT
    |
OLA-001 ROUTING EVIDENCE

Permanent rules:

- Only CanonicalObservation records may be routed.
- routed_at is caller supplied.
- PostgreSQL backend identity is explicit.
- OLA-011 append request contract is required.
- Expected terminal chain identity is captured before append.
- Persistence append must commit.
- Single routing preserves exactly-one append semantics.
- Batch routing uses the existing OLA-011 atomic_batch contract.
- One batch captures terminal state once, commits once, and verifies once.
- Returned persisted observation identity must match.
- Returned prior terminal chain hash must match the request.
- Returned terminal chain hash must differ after commit.
- Routing acceptance occurs only after committed persistence.
- Rejected persistence fails closed.
- Backend exceptions fail closed.
- Duplicate persistence conflicts fail closed.
- Routing records are immutable.
- Secret values do not enter routing metadata.
- Raw DSNs do not enter routing metadata.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains permanently read-only intelligence.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
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

from .oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceAppendResult,
    OracleCanonicalPersistenceBackend,
)

from .oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID,
    SCHEMA_VERSION as POSTGRESQL_BACKEND_SCHEMA_VERSION,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
    PostgreSQLPersistenceBackendError,
    PostgreSQLPersistenceIntegrityError,
)


SCHEMA_VERSION = "OLA-015"
ENGINE_ID = "OLA-015"

POSTGRESQL_ROUTING_RECORD_TYPE = (
    "oracle_postgresql_canonical_observation_persistence_routing_record"
)


class PostgreSQLPersistenceRoutingContractError(ValueError):
    """Raised when PostgreSQL routing contract data is malformed."""


class PostgreSQLPersistenceRoutingFailure(RuntimeError):
    """Raised when PostgreSQL-backed routing fails closed."""


class PostgreSQLPersistenceRoutingInvariantError(RuntimeError):
    """Raised when permanent routing invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostgreSQLPersistenceRoutingContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostgreSQLPersistenceRoutingContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PostgreSQLPersistenceRoutingContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PostgreSQLPersistenceRoutingContractError(
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
            raise PostgreSQLPersistenceRoutingContractError(
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
                raise PostgreSQLPersistenceRoutingContractError(
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

    raise PostgreSQLPersistenceRoutingContractError(
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
        raise PostgreSQLPersistenceRoutingContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PostgreSQLPersistenceRoutingContractError(
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


def _validate_metadata_secret_boundary(
    value: tuple[tuple[str, JSONValue], ...],
    field_name: str,
) -> None:
    forbidden_keys = {
        "password",
        "passwd",
        "secret",
        "dsn",
        "database_url",
        "connection_string",
        "uri",
    }

    for key, _ in value:
        if key.strip().lower() in forbidden_keys:
            raise PostgreSQLPersistenceRoutingContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )


@dataclass(frozen=True, slots=True)
class PostgreSQLCanonicalObservationPersistenceRoutingRecord:
    schema_version: str
    engine_id: str
    route_id: str
    backend_id: str
    observation_id: str
    source_id: str
    source_observation_id: str
    acquisition_batch_id: str
    content_hash: str
    observation_replay_hash: str
    routed_at: datetime
    append_request_id: str
    append_request_hash: str
    append_result_hash: str
    prior_terminal_chain_hash: str
    terminal_chain_hash: str
    persistence_sequence_number: int
    persistence_committed: bool
    persistence_atomic: bool
    persistence_verified: bool
    routing_accepted: bool
    routing_metadata: tuple[
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
            "backend_id": self.backend_id,
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "source_observation_id": (
                self.source_observation_id
            ),
            "acquisition_batch_id": (
                self.acquisition_batch_id
            ),
            "content_hash": self.content_hash,
            "observation_replay_hash": (
                self.observation_replay_hash
            ),
            "routed_at": self.routed_at.isoformat(),
            "append_request_id": self.append_request_id,
            "append_request_hash": self.append_request_hash,
            "append_result_hash": self.append_result_hash,
            "prior_terminal_chain_hash": (
                self.prior_terminal_chain_hash
            ),
            "terminal_chain_hash": self.terminal_chain_hash,
            "persistence_sequence_number": (
                self.persistence_sequence_number
            ),
            "persistence_committed": self.persistence_committed,
            "persistence_atomic": self.persistence_atomic,
            "persistence_verified": self.persistence_verified,
            "routing_accepted": self.routing_accepted,
            "routing_metadata": _mapping_from_immutable(
                self.routing_metadata
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


class OraclePostgreSQLCanonicalObservationPersistenceRouter:
    """
    OLA-001-compatible PostgreSQL-backed canonical observation router.

    The router supports both the original single-observation route and
    an atomic batch route. The atomic batch path captures PostgreSQL terminal
    state once, submits one OLA-011 atomic_batch append request, and verifies
    committed terminal state once after the append.

    Routing is accepted only when:
    - append status is committed,
    - committed is True,
    - atomic is True,
    - appended_count is exactly one,
    - the persisted observation id matches,
    - first and last sequence numbers match,
    - prior terminal chain hash matches the request,
    - terminal chain hash changes,
    - the backend reports the same committed terminal chain hash.

    No in-memory ledger is treated as the production persistence authority.
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
        persistence_backend: (
            OraclePostgreSQLCanonicalObservationPersistenceBackend
        ),
        route_id: str,
        routing_metadata: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> None:
        if not isinstance(
            persistence_backend,
            OraclePostgreSQLCanonicalObservationPersistenceBackend,
        ):
            raise PostgreSQLPersistenceRoutingContractError(
                "persistence_backend must be "
                "OraclePostgreSQLCanonicalObservationPersistenceBackend"
            )

        if not isinstance(
            persistence_backend,
            OracleCanonicalPersistenceBackend,
        ):
            raise PostgreSQLPersistenceRoutingContractError(
                "persistence_backend does not satisfy "
                "OracleCanonicalPersistenceBackend"
            )

        if persistence_backend.backend_id != BACKEND_ID:
            raise PostgreSQLPersistenceRoutingContractError(
                "persistence backend identity is incompatible"
            )

        self._persistence_backend = persistence_backend

        self._route_id = _require_non_empty_string(
            route_id,
            "route_id",
        )

        self._routing_metadata = _immutable_mapping(
            routing_metadata,
            "routing_metadata",
        )

        self._replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        self._audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        _validate_metadata_secret_boundary(
            self._routing_metadata,
            "routing_metadata",
        )

        _validate_metadata_secret_boundary(
            self._replay_metadata,
            "replay_metadata",
        )

        _validate_metadata_secret_boundary(
            self._audit_metadata,
            "audit_metadata",
        )

        self._routing_records: list[
            PostgreSQLCanonicalObservationPersistenceRoutingRecord
        ] = []

        self._routing_records_by_observation_id: dict[
            str,
            PostgreSQLCanonicalObservationPersistenceRoutingRecord,
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
            raise PostgreSQLPersistenceRoutingInvariantError(
                "Oracle PostgreSQL routing invariants violated"
            )

        if self._persistence_backend.read_only is not True:
            raise PostgreSQLPersistenceRoutingInvariantError(
                "PostgreSQL backend lost read_only invariant"
            )

        if (
            self._persistence_backend.execution_allowed
            is not False
        ):
            raise PostgreSQLPersistenceRoutingInvariantError(
                "PostgreSQL backend gained execution capability"
            )

    @property
    def route_id(self) -> str:
        return self._route_id

    @property
    def persistence_backend(
        self,
    ) -> OraclePostgreSQLCanonicalObservationPersistenceBackend:
        return self._persistence_backend

    @property
    def routing_record_count(self) -> int:
        return len(self._routing_records)

    @property
    def routing_records(
        self,
    ) -> tuple[
        PostgreSQLCanonicalObservationPersistenceRoutingRecord,
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
            raise PostgreSQLPersistenceRoutingContractError(
                "observation must be CanonicalObservation"
            )

        normalized_routed_at = _require_aware_datetime(
            routed_at,
            "routed_at",
        )

        if normalized_routed_at < observation.acquired_at:
            raise PostgreSQLPersistenceRoutingContractError(
                "routed_at cannot be before acquired_at"
            )

        if observation.read_only is not True:
            raise PostgreSQLPersistenceRoutingInvariantError(
                "canonical observation lost read_only invariant"
            )

        if observation.execution_allowed is not False:
            raise PostgreSQLPersistenceRoutingInvariantError(
                "canonical observation gained execution capability"
            )

        if (
            observation.observation_id
            in self._routing_records_by_observation_id
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "observation_id has already been routed"
            )

        try:
            expected_terminal_chain_hash = (
                self._persistence_backend
                .terminal_chain_hash()
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL terminal chain inspection failed closed"
            ) from exc

        append_request_id = "postgresql_append." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "postgresql_routing_append_identity",
                "route_id": self._route_id,
                "backend_id": (
                    self._persistence_backend.backend_id
                ),
                "observation_id": observation.observation_id,
                "content_hash": observation.content_hash,
                "observation_replay_hash": observation.replay_hash,
                "routed_at": normalized_routed_at,
                "expected_terminal_chain_hash": (
                    expected_terminal_chain_hash
                ),
            }
        )

        append_request = CanonicalPersistenceAppendRequest.create(
            request_id=append_request_id,
            backend_id=self._persistence_backend.backend_id,
            observations=(observation,),
            requested_at=normalized_routed_at,
            append_mode="single",
            expected_terminal_chain_hash=(
                expected_terminal_chain_hash
            ),
            request_metadata={
                "router_engine_id": ENGINE_ID,
                "route_id": self._route_id,
                "observation_id": observation.observation_id,
                "routing_metadata": _mapping_from_immutable(
                    self._routing_metadata
                ),
            },
        )

        try:
            append_result = self._persistence_backend.append(
                request=append_request,
                completed_at=normalized_routed_at,
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL canonical append failed closed"
            ) from exc

        self._validate_append_result(
            observation=observation,
            append_request=append_request,
            append_result=append_result,
            expected_terminal_chain_hash=(
                expected_terminal_chain_hash
            ),
        )

        try:
            committed_terminal_chain_hash = (
                self._persistence_backend
                .terminal_chain_hash()
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed PostgreSQL chain state could not be verified"
            ) from exc

        if (
            committed_terminal_chain_hash
            != append_result.terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "backend terminal chain state does not match "
                "committed append result"
            )

        routing_record = self._build_routing_record(
            observation=observation,
            routed_at=normalized_routed_at,
            append_request=append_request,
            append_result=append_result,
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
                "backend_id": self._persistence_backend.backend_id,
                "routing_record_hash": (
                    routing_record.routing_record_hash
                ),
                "persistence_verified": True,
                "persistence_committed": True,
                "persistence_atomic": True,
                "append_request_id": (
                    append_request.request_id
                ),
                "append_request_hash": (
                    append_request.request_hash
                ),
                "append_result_hash": (
                    append_result.result_hash
                ),
                "persistence_sequence_number": (
                    routing_record
                    .persistence_sequence_number
                ),
                "prior_terminal_chain_hash": (
                    append_result
                    .prior_terminal_chain_hash
                ),
                "terminal_chain_hash": (
                    append_result.terminal_chain_hash
                ),
                "observation_content_hash": (
                    observation.content_hash
                ),
                "observation_replay_hash": (
                    observation.replay_hash
                ),
                "destination": (
                    "oracle.postgresql.canonical.persistence"
                ),
            },
        )


    def route_batch(
        self,
        observations: tuple[CanonicalObservation, ...],
        routed_at: datetime,
    ) -> tuple[ObservationRoutingEvidence, ...]:
        self._assert_invariants()

        if not isinstance(observations, tuple):
            raise PostgreSQLPersistenceRoutingContractError(
                "observations must be a tuple"
            )

        if not observations:
            raise PostgreSQLPersistenceRoutingContractError(
                "observations must not be empty"
            )

        normalized_routed_at = _require_aware_datetime(
            routed_at,
            "routed_at",
        )

        observation_ids: set[str] = set()
        content_hashes: set[str] = set()

        for observation in observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise PostgreSQLPersistenceRoutingContractError(
                    "batch observations must be CanonicalObservation"
                )

            if normalized_routed_at < observation.acquired_at:
                raise PostgreSQLPersistenceRoutingContractError(
                    "routed_at cannot be before acquired_at"
                )

            if observation.read_only is not True:
                raise PostgreSQLPersistenceRoutingInvariantError(
                    "canonical observation lost read_only invariant"
                )

            if observation.execution_allowed is not False:
                raise PostgreSQLPersistenceRoutingInvariantError(
                    "canonical observation gained execution capability"
                )

            if observation.observation_id in observation_ids:
                raise PostgreSQLPersistenceRoutingContractError(
                    "batch contains duplicate observation_id"
                )

            if observation.content_hash in content_hashes:
                raise PostgreSQLPersistenceRoutingContractError(
                    "batch contains duplicate content_hash"
                )

            if (
                observation.observation_id
                in self._routing_records_by_observation_id
            ):
                raise PostgreSQLPersistenceRoutingFailure(
                    "observation_id has already been routed"
                )

            observation_ids.add(observation.observation_id)
            content_hashes.add(observation.content_hash)

        try:
            expected_terminal_chain_hash = (
                self._persistence_backend
                .terminal_chain_hash()
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL terminal chain inspection failed closed"
            ) from exc

        append_request_id = "postgresql_append_batch." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "postgresql_batch_routing_append_identity",
                "route_id": self._route_id,
                "backend_id": self._persistence_backend.backend_id,
                "observation_ids": [
                    observation.observation_id
                    for observation in observations
                ],
                "content_hashes": [
                    observation.content_hash
                    for observation in observations
                ],
                "observation_replay_hashes": [
                    observation.replay_hash
                    for observation in observations
                ],
                "routed_at": normalized_routed_at,
                "expected_terminal_chain_hash": (
                    expected_terminal_chain_hash
                ),
            }
        )

        append_request = CanonicalPersistenceAppendRequest.create(
            request_id=append_request_id,
            backend_id=self._persistence_backend.backend_id,
            observations=observations,
            requested_at=normalized_routed_at,
            append_mode="atomic_batch",
            expected_terminal_chain_hash=(
                expected_terminal_chain_hash
            ),
            request_metadata={
                "router_engine_id": ENGINE_ID,
                "route_id": self._route_id,
                "routing_mode": "atomic_batch",
                "observation_count": len(observations),
                "routing_metadata": _mapping_from_immutable(
                    self._routing_metadata
                ),
            },
        )

        try:
            append_result = self._persistence_backend.append(
                request=append_request,
                completed_at=normalized_routed_at,
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL canonical batch append failed closed"
            ) from exc

        self._validate_batch_append_result(
            observations=observations,
            append_request=append_request,
            append_result=append_result,
            expected_terminal_chain_hash=(
                expected_terminal_chain_hash
            ),
        )

        chain_links = self._reconstruct_batch_chain_links(
            observations=observations,
            first_sequence_number=(
                append_result.first_sequence_number
            ),
            prior_terminal_chain_hash=(
                append_result.prior_terminal_chain_hash
            ),
            persisted_at=normalized_routed_at,
        )

        if chain_links[-1][2] != append_result.terminal_chain_hash:
            raise PostgreSQLPersistenceRoutingFailure(
                "reconstructed batch terminal chain hash mismatch"
            )

        try:
            committed_terminal_chain_hash = (
                self._persistence_backend
                .terminal_chain_hash()
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed PostgreSQL batch chain state could not be verified"
            ) from exc

        if (
            committed_terminal_chain_hash
            != append_result.terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "backend terminal chain state does not match committed batch append result"
            )

        evidences: list[ObservationRoutingEvidence] = []

        for observation, chain_link in zip(
            observations,
            chain_links,
            strict=True,
        ):
            (
                sequence_number,
                previous_chain_hash,
                chain_hash,
            ) = chain_link

            routing_record = self._build_routing_record(
                observation=observation,
                routed_at=normalized_routed_at,
                append_request=append_request,
                append_result=append_result,
                persistence_sequence_number=sequence_number,
                prior_terminal_chain_hash=previous_chain_hash,
                terminal_chain_hash=chain_hash,
            )

            self._routing_records.append(routing_record)
            self._routing_records_by_observation_id[
                observation.observation_id
            ] = routing_record

            evidences.append(
                ObservationRoutingEvidence.create(
                    observation_id=observation.observation_id,
                    route_id=self._route_id,
                    routed_at=normalized_routed_at,
                    accepted=True,
                    metadata={
                        "router_engine_id": ENGINE_ID,
                        "backend_id": self._persistence_backend.backend_id,
                        "routing_mode": "atomic_batch",
                        "batch_observation_count": len(observations),
                        "routing_record_hash": (
                            routing_record.routing_record_hash
                        ),
                        "persistence_verified": True,
                        "persistence_committed": True,
                        "persistence_atomic": True,
                        "append_request_id": append_request.request_id,
                        "append_request_hash": append_request.request_hash,
                        "append_result_hash": append_result.result_hash,
                        "persistence_sequence_number": sequence_number,
                        "prior_terminal_chain_hash": previous_chain_hash,
                        "terminal_chain_hash": chain_hash,
                        "observation_content_hash": observation.content_hash,
                        "observation_replay_hash": observation.replay_hash,
                        "production_persistence": "postgresql",
                    },
                )
            )

        return tuple(evidences)

    __call__ = route


    @staticmethod
    def _validate_batch_append_result(
        *,
        observations: tuple[CanonicalObservation, ...],
        append_request: CanonicalPersistenceAppendRequest,
        append_result: CanonicalPersistenceAppendResult,
        expected_terminal_chain_hash: str,
    ) -> None:
        if not isinstance(
            append_result,
            CanonicalPersistenceAppendResult,
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL backend returned incompatible batch append result"
            )

        if append_result.backend_id != BACKEND_ID:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append result backend identity mismatch"
            )

        if append_result.request_id != append_request.request_id:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append result request identity mismatch"
            )

        if append_result.request_hash != append_request.request_hash:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append result request hash mismatch"
            )

        if append_result.append_status != "committed":
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL batch append was not committed"
            )

        if append_result.committed is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL batch append committed flag is false"
            )

        if append_result.atomic is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL batch append was not atomic"
            )

        if append_result.appended_count != len(observations):
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append count does not match routed observations"
            )

        expected_ids = tuple(
            observation.observation_id
            for observation in observations
        )

        if append_result.persisted_observation_ids != expected_ids:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch persisted observation identity mismatch"
            )

        if append_result.first_sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed batch append lacks first sequence number"
            )

        if append_result.last_sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed batch append lacks last sequence number"
            )

        expected_last_sequence = (
            append_result.first_sequence_number
            + len(observations)
            - 1
        )

        if append_result.last_sequence_number != expected_last_sequence:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append sequence range mismatch"
            )

        if (
            append_result.prior_terminal_chain_hash
            != expected_terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "batch prior terminal chain identity mismatch"
            )

        if (
            append_result.terminal_chain_hash
            == append_result.prior_terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "committed batch append did not advance terminal chain state"
            )

        if append_result.read_only is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append result lost read_only invariant"
            )

        false_invariants = {
            "execution_allowed": append_result.execution_allowed,
            "execution_adapter_resolved": append_result.execution_adapter_resolved,
            "execution_adapter_invoked": append_result.execution_adapter_invoked,
            "trade_authorization_allowed": append_result.trade_authorization_allowed,
            "order_placement_allowed": append_result.order_placement_allowed,
            "funds_moved": append_result.funds_moved,
            "portfolio_mutated": append_result.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise PostgreSQLPersistenceRoutingFailure(
                "batch append result gained execution capability"
            )

    @staticmethod
    def _reconstruct_batch_chain_links(
        *,
        observations: tuple[CanonicalObservation, ...],
        first_sequence_number: int | None,
        prior_terminal_chain_hash: str,
        persisted_at: datetime,
    ) -> tuple[tuple[int, str, str], ...]:
        if first_sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "validated batch append lost first sequence number"
            )

        previous_chain_hash = prior_terminal_chain_hash
        chain_links: list[tuple[int, str, str]] = []

        for offset, observation in enumerate(observations):
            sequence_number = first_sequence_number + offset
            chain_hash = stable_hash(
                {
                    "schema_version": POSTGRESQL_BACKEND_SCHEMA_VERSION,
                    "record_type": "postgresql_canonical_chain_link",
                    "sequence_number": sequence_number,
                    "previous_chain_hash": previous_chain_hash,
                    "observation_id": observation.observation_id,
                    "content_hash": observation.content_hash,
                    "observation_replay_hash": observation.replay_hash,
                    "canonical_observation": observation.to_canonical_dict(),
                    "persisted_at": persisted_at.isoformat(),
                }
            )

            chain_links.append(
                (
                    sequence_number,
                    previous_chain_hash,
                    chain_hash,
                )
            )
            previous_chain_hash = chain_hash

        return tuple(chain_links)

    @staticmethod
    def _validate_append_result(
        *,
        observation: CanonicalObservation,
        append_request: CanonicalPersistenceAppendRequest,
        append_result: CanonicalPersistenceAppendResult,
        expected_terminal_chain_hash: str,
    ) -> None:
        if not isinstance(
            append_result,
            CanonicalPersistenceAppendResult,
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL backend returned incompatible append result"
            )

        if append_result.backend_id != BACKEND_ID:
            raise PostgreSQLPersistenceRoutingFailure(
                "append result backend identity mismatch"
            )

        if (
            append_result.request_id
            != append_request.request_id
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "append result request identity mismatch"
            )

        if (
            append_result.request_hash
            != append_request.request_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "append result request hash mismatch"
            )

        if append_result.append_status != "committed":
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL append was not committed"
            )

        if append_result.committed is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL append committed flag is false"
            )

        if append_result.atomic is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "PostgreSQL append was not atomic"
            )

        if append_result.appended_count != 1:
            raise PostgreSQLPersistenceRoutingFailure(
                "routing append must commit exactly one observation"
            )

        if (
            append_result.persisted_observation_ids
            != (observation.observation_id,)
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "persisted observation identity mismatch"
            )

        if append_result.first_sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed routing append lacks first sequence number"
            )

        if append_result.last_sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "committed routing append lacks last sequence number"
            )

        if (
            append_result.first_sequence_number
            != append_result.last_sequence_number
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "single observation routing append sequence mismatch"
            )

        if (
            append_result.prior_terminal_chain_hash
            != expected_terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "prior terminal chain identity mismatch"
            )

        if (
            append_result.terminal_chain_hash
            == append_result.prior_terminal_chain_hash
        ):
            raise PostgreSQLPersistenceRoutingFailure(
                "committed append did not advance terminal chain state"
            )

        if append_result.read_only is not True:
            raise PostgreSQLPersistenceRoutingFailure(
                "append result lost read_only invariant"
            )

        false_invariants = {
            "execution_allowed": append_result.execution_allowed,
            "execution_adapter_resolved": (
                append_result.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                append_result.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                append_result.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                append_result.order_placement_allowed
            ),
            "funds_moved": append_result.funds_moved,
            "portfolio_mutated": append_result.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise PostgreSQLPersistenceRoutingFailure(
                "append result gained execution capability"
            )

    def _build_routing_record(
        self,
        *,
        observation: CanonicalObservation,
        routed_at: datetime,
        append_request: CanonicalPersistenceAppendRequest,
        append_result: CanonicalPersistenceAppendResult,
        persistence_sequence_number: int | None = None,
        prior_terminal_chain_hash: str | None = None,
        terminal_chain_hash: str | None = None,
    ) -> PostgreSQLCanonicalObservationPersistenceRoutingRecord:
        sequence_number = (
            append_result.first_sequence_number
            if persistence_sequence_number is None
            else persistence_sequence_number
        )

        if sequence_number is None:
            raise PostgreSQLPersistenceRoutingFailure(
                "validated append result lost sequence number"
            )

        provisional = (
            PostgreSQLCanonicalObservationPersistenceRoutingRecord(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                route_id=self._route_id,
                backend_id=self._persistence_backend.backend_id,
                observation_id=observation.observation_id,
                source_id=observation.source_id,
                source_observation_id=(
                    observation.source_observation_id
                ),
                acquisition_batch_id=(
                    observation.acquisition_batch_id
                ),
                content_hash=observation.content_hash,
                observation_replay_hash=(
                    observation.replay_hash
                ),
                routed_at=routed_at,
                append_request_id=append_request.request_id,
                append_request_hash=append_request.request_hash,
                append_result_hash=append_result.result_hash,
                prior_terminal_chain_hash=(
                    append_result.prior_terminal_chain_hash
                    if prior_terminal_chain_hash is None
                    else prior_terminal_chain_hash
                ),
                terminal_chain_hash=(
                    append_result.terminal_chain_hash
                    if terminal_chain_hash is None
                    else terminal_chain_hash
                ),
                persistence_sequence_number=sequence_number,
                persistence_committed=True,
                persistence_atomic=True,
                persistence_verified=True,
                routing_accepted=True,
                routing_metadata=self._routing_metadata,
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
                "record_type": POSTGRESQL_ROUTING_RECORD_TYPE,
                "routing_record": (
                    provisional.to_canonical_dict(
                        include_routing_record_hash=False
                    )
                ),
            }
        )

        return PostgreSQLCanonicalObservationPersistenceRoutingRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            route_id=provisional.route_id,
            backend_id=provisional.backend_id,
            observation_id=provisional.observation_id,
            source_id=provisional.source_id,
            source_observation_id=(
                provisional.source_observation_id
            ),
            acquisition_batch_id=(
                provisional.acquisition_batch_id
            ),
            content_hash=provisional.content_hash,
            observation_replay_hash=(
                provisional.observation_replay_hash
            ),
            routed_at=provisional.routed_at,
            append_request_id=provisional.append_request_id,
            append_request_hash=provisional.append_request_hash,
            append_result_hash=provisional.append_result_hash,
            prior_terminal_chain_hash=(
                provisional.prior_terminal_chain_hash
            ),
            terminal_chain_hash=(
                provisional.terminal_chain_hash
            ),
            persistence_sequence_number=(
                provisional.persistence_sequence_number
            ),
            persistence_committed=True,
            persistence_atomic=True,
            persistence_verified=True,
            routing_accepted=True,
            routing_metadata=provisional.routing_metadata,
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
    ) -> PostgreSQLCanonicalObservationPersistenceRoutingRecord | None:
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
    "PostgreSQLPersistenceRoutingContractError",
    "PostgreSQLPersistenceRoutingFailure",
    "PostgreSQLPersistenceRoutingInvariantError",
    "PostgreSQLCanonicalObservationPersistenceRoutingRecord",
    "OraclePostgreSQLCanonicalObservationPersistenceRouter",
    "canonical_json",
    "stable_hash",
]
