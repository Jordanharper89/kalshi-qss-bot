"""
OLA-013
Oracle PostgreSQL Secure Configuration and Connection Factory

Secure production configuration and credential boundary for the Oracle
PostgreSQL canonical persistence backend.

Architecture:

ENVIRONMENT / SECRET PROVIDER
    |
OLA-013 SECRET BOUNDARY
    |
SANITIZED CANONICAL DATABASE CONFIGURATION
    |
SECRET-BEARING CONNECTION FACTORY
    |
OLA-012 POSTGRESQL PERSISTENCE BACKEND

Permanent rules:

- Database passwords are secrets.
- Raw database DSNs are secrets when they contain credentials.
- Secrets may be consumed to open a physical connection.
- Secrets may not enter canonical Oracle records.
- Secrets may not enter stable hashes.
- Secrets may not enter replay metadata.
- Secrets may not enter audit metadata.
- Secrets may not be exposed in repr().
- Secrets may not be returned from sanitized configuration records.
- Environment variable names may be canonical evidence.
- Secret values may not be canonical evidence.
- Caller supplies contract timestamps.
- Missing required configuration fails closed.
- Empty secret values fail closed.
- Unsupported SSL modes fail closed.
- Port ranges are validated.
- Connection factories are explicit.
- Driver loading is explicit.
- No database driver is silently installed.
- Oracle remains permanently read-only intelligence.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
- Canonical stable hashing is used.
- repr() is never used for canonical hashing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import ipaddress
import json
import math
import os
import queue
import socket
import threading
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "OLA-013"
ENGINE_ID = "OLA-013"

CONFIG_RECORD_TYPE = (
    "oracle_postgresql_sanitized_configuration"
)

CONNECTION_FACTORY_RECORD_TYPE = (
    "oracle_postgresql_connection_factory_evidence"
)


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


SUPPORTED_SSL_MODES = (
    "disable",
    "allow",
    "prefer",
    "require",
    "verify-ca",
    "verify-full",
)


class PostgreSQLConfigurationContractError(ValueError):
    """Raised when PostgreSQL configuration is malformed."""


class PostgreSQLSecretBoundaryError(
    PostgreSQLConfigurationContractError
):
    """Raised when secret-boundary rules are violated."""


class PostgreSQLDriverLoadError(RuntimeError):
    """Raised when an approved PostgreSQL driver cannot be loaded."""


class PostgreSQLConnectionFactoryError(RuntimeError):
    """Raised when a physical PostgreSQL connection cannot be created."""


class PostgreSQLConnectionReachabilityError(
    PostgreSQLConnectionFactoryError
):
    """Raised when the physical PostgreSQL endpoint is not reachable."""


class PostgreSQLConfigurationInvariantError(RuntimeError):
    """Raised when permanent no-execution invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostgreSQLConfigurationContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostgreSQLConfigurationContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PostgreSQLConfigurationContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PostgreSQLConfigurationContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_port(
    value: Any,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PostgreSQLConfigurationContractError(
            "port must be an int"
        )

    if value < 1 or value > 65535:
        raise PostgreSQLConfigurationContractError(
            "port must be between 1 and 65535"
        )

    return value



def _bounded_endpoint_reachability_probe(
    *,
    host: str,
    port: int,
    timeout_seconds: int,
) -> str:
    result_queue: queue.Queue[str | BaseException] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            connection = socket.create_connection(
                (host, port),
                timeout=timeout_seconds,
            )
            try:
                peer_address = connection.getpeername()[0]
            finally:
                connection.close()
            result_queue.put_nowait(str(ipaddress.ip_address(peer_address)))
        except BaseException as exc:
            try:
                result_queue.put_nowait(exc)
            except queue.Full:
                pass

    thread = threading.Thread(
        target=worker,
        name="ola013-postgresql-reachability-probe",
        daemon=True,
    )
    thread.start()

    try:
        result = result_queue.get(timeout=timeout_seconds)
    except queue.Empty as exc:
        raise PostgreSQLConnectionReachabilityError(
            "PostgreSQL physical endpoint reachability probe timed out"
        ) from exc

    if isinstance(result, BaseException):
        raise PostgreSQLConnectionReachabilityError(
            "PostgreSQL physical endpoint reachability probe failed closed"
        ) from result

    return result

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
            raise PostgreSQLConfigurationContractError(
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
                raise PostgreSQLConfigurationContractError(
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

    raise PostgreSQLConfigurationContractError(
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
        raise PostgreSQLConfigurationContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PostgreSQLConfigurationContractError(
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


def _assert_secret_not_present(
    *,
    secret_value: str,
    payload: Any,
    field_name: str,
) -> None:
    if not secret_value:
        raise PostgreSQLSecretBoundaryError(
            f"{field_name} secret value must not be empty"
        )

    serialized = canonical_json(
        payload
    )

    if secret_value in serialized:
        raise PostgreSQLSecretBoundaryError(
            f"{field_name} leaked into canonical payload"
        )


@dataclass(frozen=True, slots=True)
class PostgreSQLSecretEnvironmentContract:
    password_environment_variable: str
    driver_module: str
    driver_connect_attribute: str
    contract_hash: str

    @classmethod
    def create(
        cls,
        *,
        password_environment_variable: str,
        driver_module: str,
        driver_connect_attribute: str,
    ) -> "PostgreSQLSecretEnvironmentContract":
        normalized_password_environment_variable = (
            _require_non_empty_string(
                password_environment_variable,
                "password_environment_variable",
            )
        )

        normalized_driver_module = _require_non_empty_string(
            driver_module,
            "driver_module",
        )

        normalized_driver_connect_attribute = (
            _require_non_empty_string(
                driver_connect_attribute,
                "driver_connect_attribute",
            )
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": (
                "postgresql_secret_environment_contract"
            ),
            "password_environment_variable": (
                normalized_password_environment_variable
            ),
            "driver_module": normalized_driver_module,
            "driver_connect_attribute": (
                normalized_driver_connect_attribute
            ),
        }

        return cls(
            password_environment_variable=(
                normalized_password_environment_variable
            ),
            driver_module=normalized_driver_module,
            driver_connect_attribute=(
                normalized_driver_connect_attribute
            ),
            contract_hash=stable_hash(payload),
        )


@dataclass(frozen=True, slots=True)
class SanitizedPostgreSQLConfiguration:
    schema_version: str
    engine_id: str
    configuration_id: str
    host: str
    port: int
    database: str
    username: str
    sslmode: str
    connect_timeout_seconds: int
    application_name: str
    password_environment_variable: str
    driver_module: str
    driver_connect_attribute: str
    configured_at: datetime
    configuration_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    secret_value_present: bool
    secret_value_canonicalized: bool
    raw_dsn_stored: bool
    configuration_hash: str
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
        include_configuration_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "configuration_id": self.configuration_id,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "sslmode": self.sslmode,
            "connect_timeout_seconds": (
                self.connect_timeout_seconds
            ),
            "application_name": self.application_name,
            "password_environment_variable": (
                self.password_environment_variable
            ),
            "driver_module": self.driver_module,
            "driver_connect_attribute": (
                self.driver_connect_attribute
            ),
            "configured_at": self.configured_at.isoformat(),
            "configuration_metadata": (
                _mapping_from_immutable(
                    self.configuration_metadata
                )
            ),
            "secret_value_present": self.secret_value_present,
            "secret_value_canonicalized": (
                self.secret_value_canonicalized
            ),
            "raw_dsn_stored": self.raw_dsn_stored,
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

        if include_configuration_hash:
            result["configuration_hash"] = (
                self.configuration_hash
            )

        return result


@dataclass(frozen=True, slots=True)
class PostgreSQLConnectionFactoryEvidence:
    schema_version: str
    engine_id: str
    configuration_id: str
    configuration_hash: str
    driver_module: str
    driver_connect_attribute: str
    password_environment_variable: str
    created_at: datetime
    factory_status: str
    reason_codes: tuple[str, ...]
    secret_value_read: bool
    secret_value_canonicalized: bool
    secret_value_returned: bool
    raw_dsn_created: bool
    evidence_hash: str
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
        include_evidence_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "configuration_id": self.configuration_id,
            "configuration_hash": self.configuration_hash,
            "driver_module": self.driver_module,
            "driver_connect_attribute": (
                self.driver_connect_attribute
            ),
            "password_environment_variable": (
                self.password_environment_variable
            ),
            "created_at": self.created_at.isoformat(),
            "factory_status": self.factory_status,
            "reason_codes": list(self.reason_codes),
            "secret_value_read": self.secret_value_read,
            "secret_value_canonicalized": (
                self.secret_value_canonicalized
            ),
            "secret_value_returned": (
                self.secret_value_returned
            ),
            "raw_dsn_created": self.raw_dsn_created,
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

        if include_evidence_hash:
            result["evidence_hash"] = self.evidence_hash

        return result


class OraclePostgreSQLSecureConfigurationConnectionFactory:
    """
    Secure PostgreSQL configuration and connection-factory boundary.

    The sanitized configuration contains:
    - host
    - port
    - database
    - username
    - SSL mode
    - timeout
    - application name
    - secret environment variable NAME
    - driver module identity

    It never contains the password environment variable VALUE.

    The physical connection factory reads the secret only at connection
    creation time and passes it directly to the approved driver connect
    callable.
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
            raise PostgreSQLConfigurationInvariantError(
                "Oracle PostgreSQL configuration invariants violated"
            )

    def create_sanitized_configuration(
        self,
        *,
        host: str,
        port: int,
        database: str,
        username: str,
        sslmode: str,
        connect_timeout_seconds: int,
        application_name: str,
        secret_contract: PostgreSQLSecretEnvironmentContract,
        configured_at: datetime,
        configuration_metadata: Mapping[str, Any],
    ) -> SanitizedPostgreSQLConfiguration:
        self._assert_invariants()

        normalized_host = _require_non_empty_string(
            host,
            "host",
        )

        normalized_port = _require_port(
            port
        )

        normalized_database = _require_non_empty_string(
            database,
            "database",
        )

        normalized_username = _require_non_empty_string(
            username,
            "username",
        )

        normalized_sslmode = _require_non_empty_string(
            sslmode,
            "sslmode",
        )

        if normalized_sslmode not in SUPPORTED_SSL_MODES:
            raise PostgreSQLConfigurationContractError(
                "unsupported sslmode"
            )

        if (
            isinstance(connect_timeout_seconds, bool)
            or not isinstance(connect_timeout_seconds, int)
        ):
            raise PostgreSQLConfigurationContractError(
                "connect_timeout_seconds must be an int"
            )

        if connect_timeout_seconds <= 0:
            raise PostgreSQLConfigurationContractError(
                "connect_timeout_seconds must be greater than zero"
            )

        normalized_application_name = _require_non_empty_string(
            application_name,
            "application_name",
        )

        if not isinstance(
            secret_contract,
            PostgreSQLSecretEnvironmentContract,
        ):
            raise PostgreSQLConfigurationContractError(
                "secret_contract must be "
                "PostgreSQLSecretEnvironmentContract"
            )

        normalized_configured_at = _require_aware_datetime(
            configured_at,
            "configured_at",
        )

        immutable_metadata = _immutable_mapping(
            configuration_metadata,
            "configuration_metadata",
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
                raise PostgreSQLSecretBoundaryError(
                    "configuration metadata contains forbidden "
                    f"secret-bearing key: {key}"
                )

        configuration_id = "postgresql_config." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    "postgresql_configuration_identity"
                ),
                "host": normalized_host,
                "port": normalized_port,
                "database": normalized_database,
                "username": normalized_username,
                "sslmode": normalized_sslmode,
                "application_name": (
                    normalized_application_name
                ),
                "password_environment_variable": (
                    secret_contract
                    .password_environment_variable
                ),
                "driver_module": (
                    secret_contract.driver_module
                ),
                "driver_connect_attribute": (
                    secret_contract
                    .driver_connect_attribute
                ),
            }
        )

        provisional = SanitizedPostgreSQLConfiguration(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            configuration_id=configuration_id,
            host=normalized_host,
            port=normalized_port,
            database=normalized_database,
            username=normalized_username,
            sslmode=normalized_sslmode,
            connect_timeout_seconds=(
                connect_timeout_seconds
            ),
            application_name=normalized_application_name,
            password_environment_variable=(
                secret_contract
                .password_environment_variable
            ),
            driver_module=secret_contract.driver_module,
            driver_connect_attribute=(
                secret_contract.driver_connect_attribute
            ),
            configured_at=normalized_configured_at,
            configuration_metadata=immutable_metadata,
            secret_value_present=False,
            secret_value_canonicalized=False,
            raw_dsn_stored=False,
            configuration_hash="",
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

        configuration_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": CONFIG_RECORD_TYPE,
                "configuration": (
                    provisional.to_canonical_dict(
                        include_configuration_hash=False
                    )
                ),
            }
        )

        return SanitizedPostgreSQLConfiguration(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            configuration_id=provisional.configuration_id,
            host=provisional.host,
            port=provisional.port,
            database=provisional.database,
            username=provisional.username,
            sslmode=provisional.sslmode,
            connect_timeout_seconds=(
                provisional.connect_timeout_seconds
            ),
            application_name=provisional.application_name,
            password_environment_variable=(
                provisional.password_environment_variable
            ),
            driver_module=provisional.driver_module,
            driver_connect_attribute=(
                provisional.driver_connect_attribute
            ),
            configured_at=provisional.configured_at,
            configuration_metadata=(
                provisional.configuration_metadata
            ),
            secret_value_present=False,
            secret_value_canonicalized=False,
            raw_dsn_stored=False,
            configuration_hash=configuration_hash,
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

    def build_connection_factory(
        self,
        *,
        configuration: SanitizedPostgreSQLConfiguration,
        created_at: datetime,
        environment: Mapping[str, str] | None = None,
        module_loader: Callable[[str], Any] | None = None,
        reachability_probe: Callable[..., None] | None = None,
    ) -> tuple[
        Callable[[], Any],
        PostgreSQLConnectionFactoryEvidence,
    ]:
        self._assert_invariants()

        if not isinstance(
            configuration,
            SanitizedPostgreSQLConfiguration,
        ):
            raise PostgreSQLConfigurationContractError(
                "configuration must be "
                "SanitizedPostgreSQLConfiguration"
            )

        normalized_created_at = _require_aware_datetime(
            created_at,
            "created_at",
        )

        environment_source = (
            os.environ
            if environment is None
            else environment
        )

        if not isinstance(
            environment_source,
            Mapping,
        ):
            raise PostgreSQLConfigurationContractError(
                "environment must be a mapping"
            )

        secret_value = environment_source.get(
            configuration.password_environment_variable
        )

        if not isinstance(secret_value, str):
            raise PostgreSQLSecretBoundaryError(
                "required PostgreSQL password environment "
                "variable is missing"
            )

        if not secret_value:
            raise PostgreSQLSecretBoundaryError(
                "PostgreSQL password secret must not be empty"
            )

        loader = (
            importlib.import_module
            if module_loader is None
            else module_loader
        )

        if not callable(loader):
            raise PostgreSQLConfigurationContractError(
                "module_loader must be callable"
            )

        try:
            driver_module = loader(
                configuration.driver_module
            )
        except Exception as exc:
            raise PostgreSQLDriverLoadError(
                "approved PostgreSQL driver module could not be loaded"
            ) from exc

        if reachability_probe is not None:
            endpoint_probe = reachability_probe
        elif module_loader is None:
            endpoint_probe = _bounded_endpoint_reachability_probe
        else:
            def endpoint_probe(
                *,
                host: str,
                port: int,
                timeout_seconds: int,
            ) -> None:
                return None

        if not callable(endpoint_probe):
            raise PostgreSQLConfigurationContractError(
                "reachability_probe must be callable"
            )

        connect_callable = getattr(
            driver_module,
            configuration.driver_connect_attribute,
            None,
        )

        if not callable(connect_callable):
            raise PostgreSQLDriverLoadError(
                "approved PostgreSQL driver connect callable "
                "could not be loaded"
            )

        def connection_factory():
            reachable_host_address = endpoint_probe(
                host=configuration.host,
                port=configuration.port,
                timeout_seconds=configuration.connect_timeout_seconds,
            )

            connection_kwargs = {
                "host": configuration.host,
                "port": configuration.port,
                "dbname": configuration.database,
                "user": configuration.username,
                "password": secret_value,
                "sslmode": configuration.sslmode,
                "connect_timeout": configuration.connect_timeout_seconds,
                "application_name": configuration.application_name,
            }

            if reachable_host_address is not None:
                if not isinstance(reachable_host_address, str):
                    raise PostgreSQLConnectionReachabilityError(
                        "PostgreSQL reachability probe must return a numeric host address"
                    )
                try:
                    canonical_host_address = str(
                        ipaddress.ip_address(reachable_host_address.strip())
                    )
                except ValueError as exc:
                    raise PostgreSQLConnectionReachabilityError(
                        "PostgreSQL reachability probe returned an invalid host address"
                    ) from exc
                connection_kwargs["hostaddr"] = canonical_host_address

            try:
                return connect_callable(**connection_kwargs)

            except Exception as exc:
                raise PostgreSQLConnectionFactoryError(
                    "PostgreSQL physical connection failed closed"
                ) from exc

        provisional_evidence = PostgreSQLConnectionFactoryEvidence(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            configuration_id=configuration.configuration_id,
            configuration_hash=configuration.configuration_hash,
            driver_module=configuration.driver_module,
            driver_connect_attribute=(
                configuration.driver_connect_attribute
            ),
            password_environment_variable=(
                configuration.password_environment_variable
            ),
            created_at=normalized_created_at,
            factory_status="ready",
            reason_codes=(
                "sanitized_configuration_verified",
                "password_secret_environment_variable_resolved",
                "driver_module_loaded",
                "driver_connect_callable_loaded",
                "connection_factory_ready",
                "secret_value_not_canonicalized",
            ),
            secret_value_read=True,
            secret_value_canonicalized=False,
            secret_value_returned=False,
            raw_dsn_created=False,
            evidence_hash="",
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        evidence_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": CONNECTION_FACTORY_RECORD_TYPE,
                "evidence": (
                    provisional_evidence.to_canonical_dict(
                        include_evidence_hash=False
                    )
                ),
            }
        )

        evidence = PostgreSQLConnectionFactoryEvidence(
            schema_version=provisional_evidence.schema_version,
            engine_id=provisional_evidence.engine_id,
            configuration_id=(
                provisional_evidence.configuration_id
            ),
            configuration_hash=(
                provisional_evidence.configuration_hash
            ),
            driver_module=provisional_evidence.driver_module,
            driver_connect_attribute=(
                provisional_evidence.driver_connect_attribute
            ),
            password_environment_variable=(
                provisional_evidence
                .password_environment_variable
            ),
            created_at=provisional_evidence.created_at,
            factory_status=provisional_evidence.factory_status,
            reason_codes=provisional_evidence.reason_codes,
            secret_value_read=True,
            secret_value_canonicalized=False,
            secret_value_returned=False,
            raw_dsn_created=False,
            evidence_hash=evidence_hash,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        _assert_secret_not_present(
            secret_value=secret_value,
            payload=configuration.to_canonical_dict(),
            field_name="PostgreSQL password",
        )

        _assert_secret_not_present(
            secret_value=secret_value,
            payload=evidence.to_canonical_dict(),
            field_name="PostgreSQL password",
        )

        return connection_factory, evidence


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SUPPORTED_SSL_MODES",
    "PostgreSQLConfigurationContractError",
    "PostgreSQLSecretBoundaryError",
    "PostgreSQLDriverLoadError",
    "PostgreSQLConnectionFactoryError",
    "PostgreSQLConfigurationInvariantError",
    "PostgreSQLSecretEnvironmentContract",
    "SanitizedPostgreSQLConfiguration",
    "PostgreSQLConnectionFactoryEvidence",
    "OraclePostgreSQLSecureConfigurationConnectionFactory",
    "canonical_json",
    "stable_hash",
]
