from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_postgresql_canonical_observation_persistence_router.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_015_oracle_postgresql_canonical_observation_persistence_router.py"
)


MODULE_CONTENT = r'''
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
- Exactly one observation must be appended per routing call.
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

    The router captures the current PostgreSQL terminal chain hash,
    constructs one OLA-011 single-observation append request, and invokes
    OLA-012.

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

    __call__ = route

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
    ) -> PostgreSQLCanonicalObservationPersistenceRoutingRecord:
        sequence_number = append_result.first_sequence_number

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
                ),
                terminal_chain_hash=(
                    append_result.terminal_chain_hash
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
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal


from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    RawSourceObservation,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
    PostgreSQLPersistenceRoutingContractError,
    PostgreSQLPersistenceRoutingFailure,
)


OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    6,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    6,
    0,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    6,
    1,
    0,
    tzinfo=timezone.utc,
)

ROUTED_AT_ONE = datetime(
    2026,
    7,
    12,
    6,
    1,
    1,
    tzinfo=timezone.utc,
)

ROUTED_AT_TWO = datetime(
    2026,
    7,
    12,
    6,
    1,
    2,
    tzinfo=timezone.utc,
)


class FakePostgreSQLState:
    def __init__(self):
        self.sequence_number = 0
        self.terminal_chain_hash = GENESIS_CHAIN_HASH
        self.observations = []
        self.checkpoints = {}
        self.schema_markers = set()


class FakeCursor:
    def __init__(
        self,
        state,
    ):
        self.state = state
        self._one = None
        self._all = []

    def execute(
        self,
        sql,
        params=None,
    ):
        params = (
            ()
            if params is None
            else params
        )

        if "ola012:create_" in sql:
            self.state.schema_markers.add(
                sql.split("ola012:")[1].split()[0]
            )
            return

        if "ola012:insert_genesis_state" in sql:
            return

        if "ola012:select_state_for_update" in sql:
            self._one = (
                self.state.sequence_number,
                self.state.terminal_chain_hash,
            )
            return

        if (
            "ola012:select_state" in sql
            and "for_update" not in sql
        ):
            self._one = (
                self.state.sequence_number,
                self.state.terminal_chain_hash,
            )
            return

        if "ola012:select_duplicate" in sql:
            observation_id = params[0]
            content_hash = params[1]

            self._one = None

            for row in self.state.observations:
                if (
                    row["observation_id"]
                    == observation_id
                    or row["content_hash"]
                    == content_hash
                ):
                    self._one = (
                        row["observation_id"],
                        row["content_hash"],
                    )
                    break

            return

        if "ola012:insert_observation" in sql:
            self.state.observations.append(
                {
                    "sequence_number": params[0],
                    "observation_id": params[1],
                    "content_hash": params[2],
                    "source_id": params[3],
                    "source_observation_id": params[4],
                    "observation_type": params[5],
                    "acquisition_batch_id": params[6],
                    "observed_at": params[7],
                    "acquired_at": params[8],
                    "persisted_at": params[9],
                    "observation_replay_hash": params[10],
                    "canonical_observation_json": params[11],
                    "previous_chain_hash": params[12],
                    "chain_hash": params[13],
                }
            )
            return

        if "ola012:update_state" in sql:
            self.state.sequence_number = int(
                params[0]
            )

            self.state.terminal_chain_hash = str(
                params[1]
            )
            return

        raise AssertionError(
            f"unexpected SQL marker: {sql}"
        )

    def fetchone(self):
        return self._one

    def fetchall(self):
        return list(
            self._all
        )

    def close(self):
        return None


class FakeConnection:
    def __init__(
        self,
        state,
    ):
        self.state = state

    def cursor(self):
        return FakeCursor(
            self.state
        )

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


def build_backend():
    state = FakePostgreSQLState()

    def connection_factory():
        return FakeConnection(
            state
        )

    backend = (
        OraclePostgreSQLCanonicalObservationPersistenceBackend(
            connection_factory=connection_factory,
            auto_initialize_schema=True,
        )
    )

    return backend, state


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id=(
            "postgresql.router.snapshot.001"
        ),
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "market_id": "POSTGRESQL-ROUTER-1",
            "price": Decimal("0.31"),
        },
        provenance={
            "source_id": (
                "source.test.postgresql.router"
            ),
            "adapter_id": (
                "adapter.oracle.test.postgresql.router"
            ),
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.postgresql.router",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.015.001",
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id=(
            "postgresql.router.snapshot.002"
        ),
        observed_at=OBSERVED_AT_TWO,
        observation_type="market_snapshot",
        payload={
            "market_id": "POSTGRESQL-ROUTER-2",
            "price": Decimal("0.44"),
        },
        provenance={
            "source_id": (
                "source.test.postgresql.router"
            ),
            "adapter_id": (
                "adapter.oracle.test.postgresql.router"
            ),
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.postgresql.router",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.015.001",
    )


def build_router():
    backend, state = build_backend()

    router = (
        OraclePostgreSQLCanonicalObservationPersistenceRouter(
            persistence_backend=backend,
            route_id=(
                "oracle.postgresql.canonical.persistence.router.v1"
            ),
            routing_metadata={
                "persistence_policy_id": (
                    "oracle.postgresql.canonical.v1"
                ),
                "production_path": True,
            },
            replay_metadata={
                "replay_source": "postgresql_persistence_router",
                "replay_version": 1,
            },
            audit_metadata={
                "request_id": "audit-ola-015",
                "operator": "automated_runtime",
            },
        )
    )

    return router, backend, state


def run_primary_routing_test():
    router, backend, state = build_router()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    first_evidence = router.route(
        observation_one,
        ROUTED_AT_ONE,
    )

    first_chain_hash = (
        backend.terminal_chain_hash()
    )

    second_evidence = router(
        observation_two,
        ROUTED_AT_TWO,
    )

    second_chain_hash = (
        backend.terminal_chain_hash()
    )

    assert first_evidence.accepted is True
    assert second_evidence.accepted is True

    assert first_evidence.route_id == (
        "oracle.postgresql.canonical.persistence.router.v1"
    )

    assert (
        first_evidence.observation_id
        == observation_one.observation_id
    )

    assert (
        second_evidence.observation_id
        == observation_two.observation_id
    )

    assert first_evidence.routed_at == ROUTED_AT_ONE
    assert second_evidence.routed_at == ROUTED_AT_TWO

    assert len(state.observations) == 2
    assert state.sequence_number == 2

    assert first_chain_hash != GENESIS_CHAIN_HASH

    assert second_chain_hash != first_chain_hash

    assert (
        state.observations[0]["previous_chain_hash"]
        == GENESIS_CHAIN_HASH
    )

    assert (
        state.observations[1]["previous_chain_hash"]
        == state.observations[0]["chain_hash"]
    )

    assert (
        state.terminal_chain_hash
        == state.observations[1]["chain_hash"]
    )

    assert router.routing_record_count == 2

    first_record = router.get_routing_record(
        observation_id=observation_one.observation_id
    )

    second_record = router.get_routing_record(
        observation_id=observation_two.observation_id
    )

    assert first_record is not None
    assert second_record is not None

    assert first_record.schema_version == "OLA-015"
    assert first_record.engine_id == "OLA-015"

    assert first_record.backend_id == (
        "backend.oracle.postgresql.canonical"
    )

    assert first_record.persistence_committed is True
    assert first_record.persistence_atomic is True
    assert first_record.persistence_verified is True
    assert first_record.routing_accepted is True

    assert (
        first_record.observation_id
        == observation_one.observation_id
    )

    assert (
        first_record.source_id
        == observation_one.source_id
    )

    assert (
        first_record.source_observation_id
        == observation_one.source_observation_id
    )

    assert (
        first_record.acquisition_batch_id
        == observation_one.acquisition_batch_id
    )

    assert (
        first_record.content_hash
        == observation_one.content_hash
    )

    assert (
        first_record.observation_replay_hash
        == observation_one.replay_hash
    )

    assert first_record.persistence_sequence_number == 1

    assert (
        second_record.persistence_sequence_number
        == 2
    )

    assert (
        first_record.prior_terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert (
        second_record.prior_terminal_chain_hash
        == first_record.terminal_chain_hash
    )

    assert (
        second_record.terminal_chain_hash
        == second_chain_hash
    )

    assert first_record.immutable is True
    assert first_record.replayable is True
    assert first_record.auditable is True
    assert first_record.explainable is True

    assert first_record.read_only is True
    assert first_record.execution_allowed is False

    assert (
        first_record.execution_adapter_resolved
        is False
    )

    assert (
        first_record.execution_adapter_invoked
        is False
    )

    assert (
        first_record.trade_authorization_allowed
        is False
    )

    assert (
        first_record.order_placement_allowed
        is False
    )

    assert first_record.funds_moved is False
    assert first_record.portfolio_mutated is False

    first_metadata = dict(
        first_evidence.metadata
    )

    assert first_metadata["persistence_verified"] is True

    assert first_metadata["persistence_committed"] is True

    assert first_metadata["persistence_atomic"] is True

    assert (
        first_metadata["backend_id"]
        == "backend.oracle.postgresql.canonical"
    )

    assert (
        first_metadata["persistence_sequence_number"]
        == 1
    )

    assert (
        first_metadata["prior_terminal_chain_hash"]
        == GENESIS_CHAIN_HASH
    )

    assert (
        first_metadata["terminal_chain_hash"]
        == first_record.terminal_chain_hash
    )

    assert (
        first_metadata["observation_content_hash"]
        == observation_one.content_hash
    )

    assert (
        first_metadata["observation_replay_hash"]
        == observation_one.replay_hash
    )

    try:
        first_record.routing_accepted = False

        raise AssertionError(
            "PostgreSQL routing record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return (
        router,
        backend,
        state,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    )


def run_duplicate_route_fail_closed_test():
    router, backend, state = build_router()

    observation = build_observation_one()

    router(
        observation,
        ROUTED_AT_ONE,
    )

    prior_hash = backend.terminal_chain_hash()

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "duplicate router invocation must fail closed"
        )

    except PostgreSQLPersistenceRoutingFailure:
        pass

    assert len(state.observations) == 1

    assert (
        backend.terminal_chain_hash()
        == prior_hash
    )

    assert router.routing_record_count == 1


def run_external_duplicate_persistence_fail_closed_test():
    router, backend, state = build_router()

    observation = build_observation_one()

    expected_hash = backend.terminal_chain_hash()

    from qseries_v2.oracle_intelligence.live_acquisition import (
        CanonicalPersistenceAppendRequest,
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.external.ola.015",
        backend_id=backend.backend_id,
        observations=(observation,),
        requested_at=ROUTED_AT_ONE,
        append_mode="single",
        expected_terminal_chain_hash=expected_hash,
        request_metadata={
            "external_test": True,
        },
    )

    result = backend.append(
        request=request,
        completed_at=ROUTED_AT_ONE,
    )

    assert result.committed is True

    prior_hash = backend.terminal_chain_hash()

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "pre-persisted canonical observation must fail closed"
        )

    except PostgreSQLPersistenceRoutingFailure:
        pass

    assert len(state.observations) == 1

    assert (
        backend.terminal_chain_hash()
        == prior_hash
    )

    assert router.routing_record_count == 0


def run_timestamp_fail_closed_test():
    router, backend, state = build_router()

    observation = build_observation_one()

    try:
        router(
            observation,
            datetime(
                2026,
                7,
                12,
                6,
                1,
                1,
            ),
        )

        raise AssertionError(
            "naive routed_at must fail closed"
        )

    except PostgreSQLPersistenceRoutingContractError:
        pass

    assert len(state.observations) == 0
    assert router.routing_record_count == 0

    try:
        router(
            observation,
            OBSERVED_AT_ONE,
        )

        raise AssertionError(
            "routing before acquired_at must fail closed"
        )

    except PostgreSQLPersistenceRoutingContractError:
        pass

    assert len(state.observations) == 0
    assert router.routing_record_count == 0


def run_secret_metadata_fail_closed_test():
    backend, state = build_backend()

    try:
        (
            OraclePostgreSQLCanonicalObservationPersistenceRouter(
                persistence_backend=backend,
                route_id="router.secret.test",
                routing_metadata={
                    "password": "do-not-store-this",
                },
                replay_metadata={},
                audit_metadata={},
            )
        )

        raise AssertionError(
            "secret-bearing routing metadata must fail closed"
        )

    except PostgreSQLPersistenceRoutingContractError:
        pass

    try:
        (
            OraclePostgreSQLCanonicalObservationPersistenceRouter(
                persistence_backend=backend,
                route_id="router.dsn.test",
                routing_metadata={},
                replay_metadata={
                    "database_url": (
                        "postgresql://user:secret@host/db"
                    ),
                },
                audit_metadata={},
            )
        )

        raise AssertionError(
            "secret-bearing replay metadata must fail closed"
        )

    except PostgreSQLPersistenceRoutingContractError:
        pass


def run_deterministic_replay_test():
    first_router, first_backend, first_state = (
        build_router()
    )

    second_router, second_backend, second_state = (
        build_router()
    )

    first_one = build_observation_one()
    first_two = build_observation_two()

    second_one = build_observation_one()
    second_two = build_observation_two()

    first_evidence_one = first_router(
        first_one,
        ROUTED_AT_ONE,
    )

    first_evidence_two = first_router(
        first_two,
        ROUTED_AT_TWO,
    )

    second_evidence_one = second_router(
        second_one,
        ROUTED_AT_ONE,
    )

    second_evidence_two = second_router(
        second_two,
        ROUTED_AT_TWO,
    )

    assert first_evidence_one == second_evidence_one

    assert first_evidence_two == second_evidence_two

    assert (
        first_router.routing_records
        == second_router.routing_records
    )

    assert (
        first_backend.terminal_chain_hash()
        == second_backend.terminal_chain_hash()
    )

    assert (
        first_state.observations
        == second_state.observations
    )

    return first_router


def main():
    (
        router,
        backend,
        state,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    ) = run_primary_routing_test()

    run_duplicate_route_fail_closed_test()

    run_external_duplicate_persistence_fail_closed_test()

    run_timestamp_fail_closed_test()

    run_secret_metadata_fail_closed_test()

    replay_router = run_deterministic_replay_test()

    result = {
        "schema_version": first_record.schema_version,
        "engine_id": first_record.engine_id,
        "status": "passed",
        "route_id": router.route_id,
        "backend_id": first_record.backend_id,
        "routing_record_count": (
            router.routing_record_count
        ),
        "postgresql_persistence_count": (
            len(state.observations)
        ),
        "first_routing_accepted": (
            first_evidence.accepted
        ),
        "second_routing_accepted": (
            second_evidence.accepted
        ),
        "persistence_before_acceptance": True,
        "persistence_committed": (
            first_record.persistence_committed
        ),
        "persistence_atomic": (
            first_record.persistence_atomic
        ),
        "persistence_verified": (
            first_record.persistence_verified
        ),
        "observation_identity_preserved": True,
        "source_identity_preserved": True,
        "source_observation_identity_preserved": True,
        "acquisition_batch_identity_preserved": True,
        "content_hash_preserved": True,
        "observation_replay_hash_preserved": True,
        "persistence_sequence_preserved": True,
        "postgresql_chain_continuity_preserved": True,
        "duplicate_route_blocked": True,
        "external_duplicate_persistence_blocked": True,
        "secret_metadata_blocked": True,
        "deterministic_replay_valid": (
            replay_router.routing_record_count == 2
        ),
        "read_only": first_record.read_only,
        "execution_allowed": (
            first_record.execution_allowed
        ),
        "execution_adapter_resolved": (
            first_record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            first_record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            first_record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            first_record.order_placement_allowed
        ),
        "funds_moved": first_record.funds_moved,
        "portfolio_mutated": (
            first_record.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-015 Oracle PostgreSQL Canonical "
        "Observation Persistence Router"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
    PostgreSQLCanonicalObservationPersistenceRoutingRecord,
    PostgreSQLPersistenceRoutingContractError,
    PostgreSQLPersistenceRoutingFailure,
    PostgreSQLPersistenceRoutingInvariantError,
)
'''


EXPORT_NAMES = [
    "OraclePostgreSQLCanonicalObservationPersistenceRouter",
    "PostgreSQLCanonicalObservationPersistenceRoutingRecord",
    "PostgreSQLPersistenceRoutingContractError",
    "PostgreSQLPersistenceRoutingFailure",
    "PostgreSQLPersistenceRoutingInvariantError",
]


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_postgresql_canonical_observation_"
        "persistence_router import"
    )

    updated = existing

    if import_marker not in updated:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated:
            continue

        closing_index = updated.rfind("]")

        if closing_index == -1:
            raise RuntimeError(
                "__init__.py does not contain __all__ closing bracket"
            )

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-015 INSTALLER")
    print(" Oracle PostgreSQL Canonical Observation")
    print(" Persistence Router")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-015 installed")
    print()
    print("Run:")
    print(
        "py test_ola_015_oracle_postgresql_canonical_"
        "observation_persistence_router.py"
    )


if __name__ == "__main__":
    main()