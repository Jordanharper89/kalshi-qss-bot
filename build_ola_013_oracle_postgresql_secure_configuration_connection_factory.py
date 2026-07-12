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
    / "oracle_postgresql_secure_configuration_connection_factory.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_013_oracle_postgresql_secure_configuration_connection_factory.py"
)


MODULE_CONTENT = r'''
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
import json
import math
import os
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
            try:
                return connect_callable(
                    host=configuration.host,
                    port=configuration.port,
                    dbname=configuration.database,
                    user=configuration.username,
                    password=secret_value,
                    sslmode=configuration.sslmode,
                    connect_timeout=(
                        configuration.connect_timeout_seconds
                    ),
                    application_name=(
                        configuration.application_name
                    ),
                )

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
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLDriverLoadError,
    PostgreSQLSecretBoundaryError,
    PostgreSQLSecretEnvironmentContract,
)


CONFIGURED_AT = datetime(
    2026,
    7,
    12,
    4,
    0,
    0,
    tzinfo=timezone.utc,
)

CREATED_AT = datetime(
    2026,
    7,
    12,
    4,
    0,
    1,
    tzinfo=timezone.utc,
)

SECRET_VALUE = (
    "SUPER_SECRET_POSTGRES_PASSWORD_OLA_013"
)


class FakeConnection:
    pass


class FakeDriverModule:
    def __init__(self):
        self.calls = []

    def connect(
        self,
        **kwargs,
    ):
        self.calls.append(
            dict(kwargs)
        )

        return FakeConnection()


def build_secret_contract():
    return PostgreSQLSecretEnvironmentContract.create(
        password_environment_variable=(
            "ORACLE_POSTGRES_PASSWORD"
        ),
        driver_module="psycopg",
        driver_connect_attribute="connect",
    )


def build_configuration():
    engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    return engine.create_sanitized_configuration(
        host="db.oracle.internal",
        port=5432,
        database="oracle_intelligence",
        username="oracle_readonly_ingest",
        sslmode="require",
        connect_timeout_seconds=10,
        application_name="qseries_oracle_live_acquisition",
        secret_contract=build_secret_contract(),
        configured_at=CONFIGURED_AT,
        configuration_metadata={
            "environment": "production",
            "persistence_backend": (
                "backend.oracle.postgresql.canonical"
            ),
            "credential_provider": "environment",
        },
    )


def run_sanitized_configuration_test():
    first = build_configuration()
    second = build_configuration()

    assert first == second

    assert first.schema_version == "OLA-013"
    assert first.engine_id == "OLA-013"

    assert first.configuration_id.startswith(
        "postgresql_config."
    )

    assert first.host == "db.oracle.internal"
    assert first.port == 5432

    assert first.database == "oracle_intelligence"

    assert first.username == (
        "oracle_readonly_ingest"
    )

    assert first.sslmode == "require"

    assert first.connect_timeout_seconds == 10

    assert first.application_name == (
        "qseries_oracle_live_acquisition"
    )

    assert first.password_environment_variable == (
        "ORACLE_POSTGRES_PASSWORD"
    )

    assert first.driver_module == "psycopg"

    assert first.driver_connect_attribute == "connect"

    assert first.secret_value_present is False
    assert first.secret_value_canonicalized is False
    assert first.raw_dsn_stored is False

    assert (
        first.configuration_hash
        == second.configuration_hash
    )

    canonical = first.to_canonical_dict()

    serialized = str(
        canonical
    )

    assert SECRET_VALUE not in serialized

    assert "password" not in {
        key.lower()
        for key in canonical
        if key.lower() == "password"
    }

    assert "dsn" not in {
        key.lower()
        for key in canonical
        if key.lower() == "dsn"
    }

    assert first.immutable is True
    assert first.replayable is True
    assert first.auditable is True
    assert first.explainable is True

    assert first.read_only is True
    assert first.execution_allowed is False

    assert first.execution_adapter_resolved is False
    assert first.execution_adapter_invoked is False

    assert (
        first.trade_authorization_allowed
        is False
    )

    assert first.order_placement_allowed is False
    assert first.funds_moved is False
    assert first.portfolio_mutated is False

    try:
        first.host = "mutated"

        raise AssertionError(
            "sanitized configuration must be immutable"
        )

    except FrozenInstanceError:
        pass

    return first


def run_connection_factory_test():
    configuration = build_configuration()

    fake_driver = FakeDriverModule()

    def module_loader(
        module_name,
    ):
        assert module_name == "psycopg"

        return fake_driver

    engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    factory, evidence = engine.build_connection_factory(
        configuration=configuration,
        created_at=CREATED_AT,
        environment={
            "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
        },
        module_loader=module_loader,
    )

    assert callable(factory)

    assert evidence.schema_version == "OLA-013"
    assert evidence.engine_id == "OLA-013"

    assert evidence.configuration_id == (
        configuration.configuration_id
    )

    assert evidence.configuration_hash == (
        configuration.configuration_hash
    )

    assert evidence.driver_module == "psycopg"

    assert evidence.driver_connect_attribute == "connect"

    assert evidence.password_environment_variable == (
        "ORACLE_POSTGRES_PASSWORD"
    )

    assert evidence.factory_status == "ready"

    assert evidence.secret_value_read is True
    assert evidence.secret_value_canonicalized is False
    assert evidence.secret_value_returned is False
    assert evidence.raw_dsn_created is False

    evidence_serialized = str(
        evidence.to_canonical_dict()
    )

    assert SECRET_VALUE not in evidence_serialized

    connection = factory()

    assert isinstance(
        connection,
        FakeConnection,
    )

    assert len(fake_driver.calls) == 1

    call = fake_driver.calls[0]

    assert call == {
        "host": "db.oracle.internal",
        "port": 5432,
        "dbname": "oracle_intelligence",
        "user": "oracle_readonly_ingest",
        "password": SECRET_VALUE,
        "sslmode": "require",
        "connect_timeout": 10,
        "application_name": (
            "qseries_oracle_live_acquisition"
        ),
    }

    assert evidence.read_only is True
    assert evidence.execution_allowed is False

    assert evidence.execution_adapter_resolved is False
    assert evidence.execution_adapter_invoked is False

    assert (
        evidence.trade_authorization_allowed
        is False
    )

    assert evidence.order_placement_allowed is False
    assert evidence.funds_moved is False
    assert evidence.portfolio_mutated is False

    return configuration, evidence, fake_driver


def run_missing_secret_fail_closed_test():
    configuration = build_configuration()

    fake_driver = FakeDriverModule()

    try:
        (
            OraclePostgreSQLSecureConfigurationConnectionFactory()
            .build_connection_factory(
                configuration=configuration,
                created_at=CREATED_AT,
                environment={},
                module_loader=lambda _: fake_driver,
            )
        )

        raise AssertionError(
            "missing password secret must fail closed"
        )

    except PostgreSQLSecretBoundaryError:
        pass


def run_empty_secret_fail_closed_test():
    configuration = build_configuration()

    fake_driver = FakeDriverModule()

    try:
        (
            OraclePostgreSQLSecureConfigurationConnectionFactory()
            .build_connection_factory(
                configuration=configuration,
                created_at=CREATED_AT,
                environment={
                    "ORACLE_POSTGRES_PASSWORD": "",
                },
                module_loader=lambda _: fake_driver,
            )
        )

        raise AssertionError(
            "empty password secret must fail closed"
        )

    except PostgreSQLSecretBoundaryError:
        pass


def run_forbidden_metadata_fail_closed_test():
    engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    try:
        engine.create_sanitized_configuration(
            host="db.oracle.internal",
            port=5432,
            database="oracle_intelligence",
            username="oracle_readonly_ingest",
            sslmode="require",
            connect_timeout_seconds=10,
            application_name=(
                "qseries_oracle_live_acquisition"
            ),
            secret_contract=build_secret_contract(),
            configured_at=CONFIGURED_AT,
            configuration_metadata={
                "password": SECRET_VALUE,
            },
        )

        raise AssertionError(
            "password metadata key must fail closed"
        )

    except PostgreSQLSecretBoundaryError:
        pass

    try:
        engine.create_sanitized_configuration(
            host="db.oracle.internal",
            port=5432,
            database="oracle_intelligence",
            username="oracle_readonly_ingest",
            sslmode="require",
            connect_timeout_seconds=10,
            application_name=(
                "qseries_oracle_live_acquisition"
            ),
            secret_contract=build_secret_contract(),
            configured_at=CONFIGURED_AT,
            configuration_metadata={
                "database_url": (
                    "postgresql://user:secret@host/db"
                ),
            },
        )

        raise AssertionError(
            "database_url metadata key must fail closed"
        )

    except PostgreSQLSecretBoundaryError:
        pass


def run_driver_fail_closed_test():
    configuration = build_configuration()

    try:
        (
            OraclePostgreSQLSecureConfigurationConnectionFactory()
            .build_connection_factory(
                configuration=configuration,
                created_at=CREATED_AT,
                environment={
                    "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
                },
                module_loader=lambda _: (_ for _ in ()).throw(
                    ImportError("driver missing")
                ),
            )
        )

        raise AssertionError(
            "missing PostgreSQL driver must fail closed"
        )

    except PostgreSQLDriverLoadError:
        pass

    class MissingConnect:
        pass

    try:
        (
            OraclePostgreSQLSecureConfigurationConnectionFactory()
            .build_connection_factory(
                configuration=configuration,
                created_at=CREATED_AT,
                environment={
                    "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
                },
                module_loader=lambda _: MissingConnect(),
            )
        )

        raise AssertionError(
            "missing connect callable must fail closed"
        )

    except PostgreSQLDriverLoadError:
        pass


def run_deterministic_evidence_test():
    first_configuration = build_configuration()
    second_configuration = build_configuration()

    first_driver = FakeDriverModule()
    second_driver = FakeDriverModule()

    first_factory, first_evidence = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=first_configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: first_driver,
        )
    )

    second_factory, second_evidence = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=second_configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: second_driver,
        )
    )

    assert (
        first_configuration.configuration_hash
        == second_configuration.configuration_hash
    )

    assert first_evidence == second_evidence

    assert (
        first_evidence.evidence_hash
        == second_evidence.evidence_hash
    )

    first_factory()
    second_factory()

    assert first_driver.calls == second_driver.calls


def main():
    configuration = run_sanitized_configuration_test()

    (
        factory_configuration,
        evidence,
        fake_driver,
    ) = run_connection_factory_test()

    run_missing_secret_fail_closed_test()
    run_empty_secret_fail_closed_test()
    run_forbidden_metadata_fail_closed_test()
    run_driver_fail_closed_test()
    run_deterministic_evidence_test()

    result = {
        "schema_version": configuration.schema_version,
        "engine_id": configuration.engine_id,
        "status": "passed",
        "configuration_id": (
            configuration.configuration_id
        ),
        "host": configuration.host,
        "port": configuration.port,
        "database": configuration.database,
        "username": configuration.username,
        "sslmode": configuration.sslmode,
        "password_environment_variable": (
            configuration
            .password_environment_variable
        ),
        "driver_module": configuration.driver_module,
        "driver_connect_attribute": (
            configuration.driver_connect_attribute
        ),
        "secret_value_present_in_configuration": (
            configuration.secret_value_present
        ),
        "secret_value_canonicalized": (
            configuration.secret_value_canonicalized
        ),
        "raw_dsn_stored": configuration.raw_dsn_stored,
        "connection_factory_status": (
            evidence.factory_status
        ),
        "secret_value_read_at_factory_boundary": (
            evidence.secret_value_read
        ),
        "secret_value_returned": (
            evidence.secret_value_returned
        ),
        "missing_secret_blocked": True,
        "empty_secret_blocked": True,
        "forbidden_secret_metadata_blocked": True,
        "missing_driver_blocked": True,
        "deterministic_configuration_hashing": True,
        "deterministic_factory_evidence": True,
        "read_only": configuration.read_only,
        "execution_allowed": (
            configuration.execution_allowed
        ),
        "execution_adapter_resolved": (
            configuration.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            configuration.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            configuration.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            configuration.order_placement_allowed
        ),
        "funds_moved": configuration.funds_moved,
        "portfolio_mutated": (
            configuration.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-013 Oracle PostgreSQL Secure "
        "Configuration and Connection Factory"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLConfigurationContractError,
    PostgreSQLConfigurationInvariantError,
    PostgreSQLConnectionFactoryError,
    PostgreSQLConnectionFactoryEvidence,
    PostgreSQLDriverLoadError,
    PostgreSQLSecretBoundaryError,
    PostgreSQLSecretEnvironmentContract,
    SUPPORTED_SSL_MODES,
    SanitizedPostgreSQLConfiguration,
)
'''


EXPORT_NAMES = [
    "OraclePostgreSQLSecureConfigurationConnectionFactory",
    "PostgreSQLConfigurationContractError",
    "PostgreSQLConfigurationInvariantError",
    "PostgreSQLConnectionFactoryError",
    "PostgreSQLConnectionFactoryEvidence",
    "PostgreSQLDriverLoadError",
    "PostgreSQLSecretBoundaryError",
    "PostgreSQLSecretEnvironmentContract",
    "SUPPORTED_SSL_MODES",
    "SanitizedPostgreSQLConfiguration",
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
        "from .oracle_postgresql_secure_configuration_"
        "connection_factory import"
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
    print(" OLA-013 INSTALLER")
    print(" Oracle PostgreSQL Secure Configuration")
    print(" and Connection Factory")
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
    print("[DONE] OLA-013 installed")
    print()
    print("Run:")
    print(
        "py test_ola_013_oracle_postgresql_secure_"
        "configuration_connection_factory.py"
    )


if __name__ == "__main__":
    main()