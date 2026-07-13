from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLDriverLoadError,
    PostgreSQLConnectionReachabilityError,
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


def successful_reachability_probe(
    *,
    host,
    port,
    timeout_seconds,
):
    assert host == "db.oracle.internal"
    assert port == 5432
    assert timeout_seconds == 10
    return "203.0.113.17"


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
        reachability_probe=successful_reachability_probe,
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
        "hostaddr": "203.0.113.17",
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
                reachability_probe=successful_reachability_probe,
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
                reachability_probe=successful_reachability_probe,
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
                reachability_probe=successful_reachability_probe,
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
                reachability_probe=successful_reachability_probe,
            )
        )

        raise AssertionError(
            "missing connect callable must fail closed"
        )

    except PostgreSQLDriverLoadError:
        pass



def run_reachability_probe_fail_closed_test():
    configuration = build_configuration()
    fake_driver = FakeDriverModule()
    probe_calls = []

    def failing_probe(
        *,
        host,
        port,
        timeout_seconds,
    ):
        probe_calls.append(
            {
                "host": host,
                "port": port,
                "timeout_seconds": timeout_seconds,
            }
        )
        raise PostgreSQLConnectionReachabilityError(
            "PostgreSQL physical endpoint reachability probe timed out"
        )

    factory, _ = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: fake_driver,
            reachability_probe=failing_probe,
        )
    )

    try:
        factory()
        raise AssertionError(
            "unreachable PostgreSQL endpoint must fail closed"
        )
    except PostgreSQLConnectionReachabilityError as exc:
        assert str(exc) == (
            "PostgreSQL physical endpoint reachability probe timed out"
        )

    assert probe_calls == [
        {
            "host": "db.oracle.internal",
            "port": 5432,
            "timeout_seconds": 10,
        }
    ]
    assert fake_driver.calls == []


def run_reachability_probe_precedes_secret_driver_connect_test():
    configuration = build_configuration()
    event_order = []

    class OrderedDriver:
        def connect(self, **kwargs):
            event_order.append("driver_connect")
            assert kwargs["password"] == SECRET_VALUE
            return FakeConnection()

    def ordered_probe(**kwargs):
        event_order.append("reachability_probe")
        assert kwargs == {
            "host": "db.oracle.internal",
            "port": 5432,
            "timeout_seconds": 10,
        }
        return "203.0.113.17"

    factory, _ = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: OrderedDriver(),
            reachability_probe=ordered_probe,
        )
    )

    connection = factory()
    assert isinstance(connection, FakeConnection)
    assert event_order == [
        "reachability_probe",
        "driver_connect",
    ]

def run_resolved_hostaddr_binding_test():
    configuration = build_configuration()
    fake_driver = FakeDriverModule()

    factory, _ = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: fake_driver,
            reachability_probe=lambda **_: "2001:db8::17",
        )
    )

    factory()
    call = fake_driver.calls[0]
    assert call["host"] == "db.oracle.internal"
    assert call["hostaddr"] == "2001:db8::17"
    assert call["connect_timeout"] == 10

    blocked_driver = FakeDriverModule()
    blocked_factory, _ = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .build_connection_factory(
            configuration=configuration,
            created_at=CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: blocked_driver,
            reachability_probe=lambda **_: "not-an-ip-address",
        )
    )
    try:
        blocked_factory()
        raise AssertionError("invalid resolved host address must fail closed")
    except PostgreSQLConnectionReachabilityError:
        pass
    assert blocked_driver.calls == []


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
            reachability_probe=successful_reachability_probe,
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
            reachability_probe=successful_reachability_probe,
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
    run_reachability_probe_fail_closed_test()
    run_reachability_probe_precedes_secret_driver_connect_test()
    run_resolved_hostaddr_binding_test()
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
        "bounded_endpoint_reachability_probe": True,
        "unreachable_endpoint_fails_closed": True,
        "reachability_probe_precedes_secret_driver_connect": True,
        "driver_connect_timeout_preserved": True,
        "resolved_hostaddr_bound_to_driver": True,
        "canonical_hostname_preserved_for_ssl_identity": True,
        "driver_dns_reresolution_avoided": True,
        "invalid_resolved_hostaddr_fails_closed": True,
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
