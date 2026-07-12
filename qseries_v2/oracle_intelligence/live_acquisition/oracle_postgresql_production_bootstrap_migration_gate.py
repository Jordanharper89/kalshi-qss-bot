"""
OLA-014
Oracle PostgreSQL Production Bootstrap and Migration Gate

Controlled production bootstrap boundary for the Oracle PostgreSQL
canonical persistence backend.

Architecture:

SANITIZED POSTGRESQL CONFIGURATION
    |
SECURE CONNECTION FACTORY
    |
OLA-012 POSTGRESQL BACKEND
    |
SCHEMA INITIALIZATION
    |
OLA-011 CONTRACT VALIDATION
    |
BACKEND HEALTH VALIDATION
    |
CHAIN STATE / GENESIS VALIDATION
    |
PRODUCTION BOOTSTRAP EVIDENCE         <- OLA-014

Permanent rules:

- Bootstrap must occur before live acquisition writes.
- Bootstrap does not acquire market data.
- Bootstrap does not route observations.
- Bootstrap does not authorize execution.
- PostgreSQL schema initialization is explicit.
- OLA-011 capability validation is required.
- Backend health validation is required.
- Backend identity is explicit.
- Backend type is explicit.
- Sanitized configuration identity is preserved.
- Secret values may not enter bootstrap evidence.
- Raw DSNs may not enter bootstrap evidence.
- Empty database state must use the approved OLA-012 genesis hash.
- Non-empty database state must preserve an explicit terminal chain hash.
- A foreign genesis hash fails closed.
- Missing canonical state fails closed.
- Incompatible backend contract fails closed.
- Unhealthy backend fails closed.
- Caller supplies bootstrap timestamps.
- Bootstrap evidence is immutable.
- Bootstrap evidence is replayable.
- Bootstrap evidence is auditable.
- Bootstrap evidence is explainable.
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


from .oracle_canonical_persistence_backend_contract import (
    OraclePersistenceBackendContractValidator,
    PersistenceBackendCapabilityError,
    PersistenceBackendCapabilityRecord,
    PersistenceBackendHealthRecord,
)

from .oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID,
    BACKEND_TYPE,
    GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
    PostgreSQLPersistenceBackendError,
    PostgreSQLPersistenceIntegrityError,
    PostgreSQLPersistenceSchemaError,
)

from .oracle_postgresql_secure_configuration_connection_factory import (
    PostgreSQLConnectionFactoryEvidence,
    SanitizedPostgreSQLConfiguration,
)


SCHEMA_VERSION = "OLA-014"
ENGINE_ID = "OLA-014"

BOOTSTRAP_RECORD_TYPE = (
    "oracle_postgresql_production_bootstrap_record"
)


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class PostgreSQLBootstrapContractError(ValueError):
    """Raised when bootstrap contract data is malformed."""


class PostgreSQLBootstrapCompatibilityError(
    PostgreSQLBootstrapContractError
):
    """Raised when physical backend state is incompatible."""


class PostgreSQLBootstrapInvariantError(RuntimeError):
    """Raised when permanent bootstrap invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostgreSQLBootstrapContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostgreSQLBootstrapContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PostgreSQLBootstrapContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PostgreSQLBootstrapContractError(
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
            raise PostgreSQLBootstrapContractError(
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
                raise PostgreSQLBootstrapContractError(
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

    raise PostgreSQLBootstrapContractError(
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
        raise PostgreSQLBootstrapContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PostgreSQLBootstrapContractError(
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
class PostgreSQLProductionBootstrapRecord:
    schema_version: str
    engine_id: str
    bootstrap_id: str
    bootstrap_status: str
    backend_id: str
    backend_type: str
    configuration_id: str
    configuration_hash: str
    connection_factory_evidence_hash: str
    bootstrap_started_at: datetime
    bootstrap_completed_at: datetime
    schema_initialized: bool
    backend_contract_satisfied: bool
    backend_health_status: str
    backend_healthy: bool
    expected_genesis_chain_hash: str
    observed_terminal_chain_hash: str
    empty_backend_state: bool
    chain_state_compatible: bool
    live_write_ready: bool
    acquisition_performed: bool
    routing_performed: bool
    reason_codes: tuple[str, ...]
    bootstrap_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    bootstrap_hash: str
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
        include_bootstrap_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "bootstrap_id": self.bootstrap_id,
            "bootstrap_status": self.bootstrap_status,
            "backend_id": self.backend_id,
            "backend_type": self.backend_type,
            "configuration_id": self.configuration_id,
            "configuration_hash": self.configuration_hash,
            "connection_factory_evidence_hash": (
                self.connection_factory_evidence_hash
            ),
            "bootstrap_started_at": (
                self.bootstrap_started_at.isoformat()
            ),
            "bootstrap_completed_at": (
                self.bootstrap_completed_at.isoformat()
            ),
            "schema_initialized": self.schema_initialized,
            "backend_contract_satisfied": (
                self.backend_contract_satisfied
            ),
            "backend_health_status": (
                self.backend_health_status
            ),
            "backend_healthy": self.backend_healthy,
            "expected_genesis_chain_hash": (
                self.expected_genesis_chain_hash
            ),
            "observed_terminal_chain_hash": (
                self.observed_terminal_chain_hash
            ),
            "empty_backend_state": self.empty_backend_state,
            "chain_state_compatible": (
                self.chain_state_compatible
            ),
            "live_write_ready": self.live_write_ready,
            "acquisition_performed": (
                self.acquisition_performed
            ),
            "routing_performed": self.routing_performed,
            "reason_codes": list(self.reason_codes),
            "bootstrap_metadata": _mapping_from_immutable(
                self.bootstrap_metadata
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

        if include_bootstrap_hash:
            result["bootstrap_hash"] = self.bootstrap_hash

        return result


class OraclePostgreSQLProductionBootstrapMigrationGate:
    """
    Validates one physical PostgreSQL backend before live Oracle writes.

    This gate initializes the OLA-012 schema, validates the OLA-011
    capability contract, validates backend health, and verifies canonical
    chain state.

    It does not perform market acquisition.
    It does not persist a live observation.
    It does not route a canonical observation.
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

    def __init__(self) -> None:
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
            raise PostgreSQLBootstrapInvariantError(
                "Oracle PostgreSQL bootstrap invariants violated"
            )

    def bootstrap(
        self,
        *,
        configuration: SanitizedPostgreSQLConfiguration,
        connection_factory_evidence: PostgreSQLConnectionFactoryEvidence,
        connection_factory,
        bootstrap_started_at: datetime,
        bootstrap_completed_at: datetime,
        bootstrap_metadata: Mapping[str, Any],
    ) -> PostgreSQLProductionBootstrapRecord:
        self._assert_invariants()

        if not isinstance(
            configuration,
            SanitizedPostgreSQLConfiguration,
        ):
            raise PostgreSQLBootstrapContractError(
                "configuration must be "
                "SanitizedPostgreSQLConfiguration"
            )

        if not isinstance(
            connection_factory_evidence,
            PostgreSQLConnectionFactoryEvidence,
        ):
            raise PostgreSQLBootstrapContractError(
                "connection_factory_evidence must be "
                "PostgreSQLConnectionFactoryEvidence"
            )

        if not callable(connection_factory):
            raise PostgreSQLBootstrapContractError(
                "connection_factory must be callable"
            )

        normalized_started_at = _require_aware_datetime(
            bootstrap_started_at,
            "bootstrap_started_at",
        )

        normalized_completed_at = _require_aware_datetime(
            bootstrap_completed_at,
            "bootstrap_completed_at",
        )

        if normalized_completed_at < normalized_started_at:
            raise PostgreSQLBootstrapContractError(
                "bootstrap_completed_at cannot be before "
                "bootstrap_started_at"
            )

        if (
            connection_factory_evidence.configuration_id
            != configuration.configuration_id
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "connection factory configuration identity mismatch"
            )

        if (
            connection_factory_evidence.configuration_hash
            != configuration.configuration_hash
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "connection factory configuration hash mismatch"
            )

        if (
            connection_factory_evidence.factory_status
            != "ready"
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "connection factory is not ready"
            )

        if (
            configuration.secret_value_present is not False
            or configuration.secret_value_canonicalized is not False
            or configuration.raw_dsn_stored is not False
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "configuration secret boundary is incompatible"
            )

        immutable_metadata = _immutable_mapping(
            bootstrap_metadata,
            "bootstrap_metadata",
        )

        forbidden_metadata_keys = {
            "password",
            "passwd",
            "secret",
            "dsn",
            "database_url",
            "connection_string",
            "uri",
        }

        for key, _ in immutable_metadata:
            if key.strip().lower() in forbidden_metadata_keys:
                raise PostgreSQLBootstrapContractError(
                    "bootstrap metadata contains forbidden "
                    f"secret-bearing key: {key}"
                )

        backend = (
            OraclePostgreSQLCanonicalObservationPersistenceBackend(
                connection_factory=connection_factory,
                auto_initialize_schema=False,
            )
        )

        if backend.backend_id != BACKEND_ID:
            raise PostgreSQLBootstrapCompatibilityError(
                "PostgreSQL backend identity mismatch"
            )

        if backend.backend_type != BACKEND_TYPE:
            raise PostgreSQLBootstrapCompatibilityError(
                "PostgreSQL backend type mismatch"
            )

        try:
            backend.initialize_schema()

        except (
            PostgreSQLPersistenceSchemaError,
            PostgreSQLPersistenceBackendError,
        ) as exc:
            raise PostgreSQLBootstrapCompatibilityError(
                "PostgreSQL schema initialization failed closed"
            ) from exc

        validator = OraclePersistenceBackendContractValidator()

        try:
            capability, health = validator.validate_backend(
                backend=backend,
                checked_at=normalized_completed_at,
            )

        except PersistenceBackendCapabilityError as exc:
            raise PostgreSQLBootstrapCompatibilityError(
                "PostgreSQL backend contract or health validation "
                "failed closed"
            ) from exc

        self._validate_capability_record(
            capability
        )

        self._validate_health_record(
            health
        )

        try:
            terminal_chain_hash = (
                backend.terminal_chain_hash()
            )

        except (
            PostgreSQLPersistenceBackendError,
            PostgreSQLPersistenceIntegrityError,
        ) as exc:
            raise PostgreSQLBootstrapCompatibilityError(
                "PostgreSQL terminal chain state could not be "
                "validated"
            ) from exc

        normalized_terminal_chain_hash = (
            _require_non_empty_string(
                terminal_chain_hash,
                "terminal_chain_hash",
            )
        )

        empty_backend_state = (
            normalized_terminal_chain_hash
            == GENESIS_CHAIN_HASH
        )

        chain_state_compatible = True

        bootstrap_id = "postgresql_bootstrap." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "postgresql_bootstrap_identity",
                "backend_id": backend.backend_id,
                "configuration_id": (
                    configuration.configuration_id
                ),
                "configuration_hash": (
                    configuration.configuration_hash
                ),
                "connection_factory_evidence_hash": (
                    connection_factory_evidence.evidence_hash
                ),
                "bootstrap_started_at": normalized_started_at,
                "bootstrap_completed_at": normalized_completed_at,
                "observed_terminal_chain_hash": (
                    normalized_terminal_chain_hash
                ),
            }
        )

        reason_codes = [
            "secure_configuration_verified",
            "connection_factory_evidence_verified",
            "postgresql_schema_initialized",
            "ola_011_backend_contract_verified",
            "backend_health_verified",
            "terminal_chain_state_verified",
        ]

        if empty_backend_state:
            reason_codes.extend(
                (
                    "approved_genesis_chain_verified",
                    "empty_backend_ready_for_first_canonical_write",
                )
            )

        else:
            reason_codes.extend(
                (
                    "existing_terminal_chain_preserved",
                    "existing_backend_state_accepted",
                )
            )

        reason_codes.append(
            "production_bootstrap_gate_passed"
        )

        provisional = PostgreSQLProductionBootstrapRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            bootstrap_id=bootstrap_id,
            bootstrap_status="passed",
            backend_id=backend.backend_id,
            backend_type=backend.backend_type,
            configuration_id=configuration.configuration_id,
            configuration_hash=configuration.configuration_hash,
            connection_factory_evidence_hash=(
                connection_factory_evidence.evidence_hash
            ),
            bootstrap_started_at=normalized_started_at,
            bootstrap_completed_at=normalized_completed_at,
            schema_initialized=True,
            backend_contract_satisfied=(
                capability.contract_satisfied
            ),
            backend_health_status=health.health_status,
            backend_healthy=health.healthy,
            expected_genesis_chain_hash=GENESIS_CHAIN_HASH,
            observed_terminal_chain_hash=(
                normalized_terminal_chain_hash
            ),
            empty_backend_state=empty_backend_state,
            chain_state_compatible=chain_state_compatible,
            live_write_ready=True,
            acquisition_performed=False,
            routing_performed=False,
            reason_codes=tuple(reason_codes),
            bootstrap_metadata=immutable_metadata,
            bootstrap_hash="",
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

        bootstrap_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": BOOTSTRAP_RECORD_TYPE,
                "bootstrap_record": (
                    provisional.to_canonical_dict(
                        include_bootstrap_hash=False
                    )
                ),
            }
        )

        return PostgreSQLProductionBootstrapRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            bootstrap_id=provisional.bootstrap_id,
            bootstrap_status=provisional.bootstrap_status,
            backend_id=provisional.backend_id,
            backend_type=provisional.backend_type,
            configuration_id=provisional.configuration_id,
            configuration_hash=provisional.configuration_hash,
            connection_factory_evidence_hash=(
                provisional.connection_factory_evidence_hash
            ),
            bootstrap_started_at=(
                provisional.bootstrap_started_at
            ),
            bootstrap_completed_at=(
                provisional.bootstrap_completed_at
            ),
            schema_initialized=True,
            backend_contract_satisfied=True,
            backend_health_status=(
                provisional.backend_health_status
            ),
            backend_healthy=True,
            expected_genesis_chain_hash=(
                provisional.expected_genesis_chain_hash
            ),
            observed_terminal_chain_hash=(
                provisional.observed_terminal_chain_hash
            ),
            empty_backend_state=(
                provisional.empty_backend_state
            ),
            chain_state_compatible=True,
            live_write_ready=True,
            acquisition_performed=False,
            routing_performed=False,
            reason_codes=provisional.reason_codes,
            bootstrap_metadata=provisional.bootstrap_metadata,
            bootstrap_hash=bootstrap_hash,
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

    @staticmethod
    def _validate_capability_record(
        capability: PersistenceBackendCapabilityRecord,
    ) -> None:
        if not isinstance(
            capability,
            PersistenceBackendCapabilityRecord,
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "backend capability record is incompatible"
            )

        if capability.backend_id != BACKEND_ID:
            raise PostgreSQLBootstrapCompatibilityError(
                "capability backend identity mismatch"
            )

        if capability.backend_type != BACKEND_TYPE:
            raise PostgreSQLBootstrapCompatibilityError(
                "capability backend type mismatch"
            )

        if capability.contract_satisfied is not True:
            raise PostgreSQLBootstrapCompatibilityError(
                "OLA-011 backend contract is not satisfied"
            )

        if capability.read_only is not True:
            raise PostgreSQLBootstrapCompatibilityError(
                "capability record lost read_only invariant"
            )

        if capability.execution_allowed is not False:
            raise PostgreSQLBootstrapCompatibilityError(
                "capability record gained execution capability"
            )

    @staticmethod
    def _validate_health_record(
        health: PersistenceBackendHealthRecord,
    ) -> None:
        if not isinstance(
            health,
            PersistenceBackendHealthRecord,
        ):
            raise PostgreSQLBootstrapCompatibilityError(
                "backend health record is incompatible"
            )

        if health.backend_id != BACKEND_ID:
            raise PostgreSQLBootstrapCompatibilityError(
                "health backend identity mismatch"
            )

        if health.healthy is not True:
            raise PostgreSQLBootstrapCompatibilityError(
                "backend is not healthy"
            )

        if health.health_status != "healthy":
            raise PostgreSQLBootstrapCompatibilityError(
                "backend health status is incompatible"
            )

        if health.read_only is not True:
            raise PostgreSQLBootstrapCompatibilityError(
                "health record lost read_only invariant"
            )

        if health.execution_allowed is not False:
            raise PostgreSQLBootstrapCompatibilityError(
                "health record gained execution capability"
            )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PostgreSQLBootstrapContractError",
    "PostgreSQLBootstrapCompatibilityError",
    "PostgreSQLBootstrapInvariantError",
    "PostgreSQLProductionBootstrapRecord",
    "OraclePostgreSQLProductionBootstrapMigrationGate",
    "canonical_json",
    "stable_hash",
]
