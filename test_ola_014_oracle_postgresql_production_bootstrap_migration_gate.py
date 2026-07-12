from dataclasses import FrozenInstanceError
from datetime import datetime, timezone


from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    GENESIS_CHAIN_HASH,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLSecretEnvironmentContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_production_bootstrap_migration_gate import (
    OraclePostgreSQLProductionBootstrapMigrationGate,
    PostgreSQLBootstrapCompatibilityError,
    PostgreSQLBootstrapContractError,
)


CONFIGURED_AT = datetime(
    2026,
    7,
    12,
    5,
    0,
    0,
    tzinfo=timezone.utc,
)

FACTORY_CREATED_AT = datetime(
    2026,
    7,
    12,
    5,
    0,
    1,
    tzinfo=timezone.utc,
)

BOOTSTRAP_STARTED_AT = datetime(
    2026,
    7,
    12,
    5,
    0,
    2,
    tzinfo=timezone.utc,
)

BOOTSTRAP_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    5,
    0,
    3,
    tzinfo=timezone.utc,
)

SECRET_VALUE = (
    "OLA_014_TEST_POSTGRES_SECRET_VALUE"
)


class FakePostgreSQLState:
    def __init__(
        self,
        *,
        terminal_chain_hash=GENESIS_CHAIN_HASH,
        state_present=True,
        healthy=True,
    ):
        self.sequence_number = 0

        self.terminal_chain_hash = (
            terminal_chain_hash
        )

        self.state_present = state_present
        self.healthy = healthy

        self.schema_markers = set()


class FakeCursor:
    def __init__(
        self,
        state,
    ):
        self.state = state

        self._one = None

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
            if self.state.state_present:
                return

            self.state.state_present = True
            self.state.sequence_number = 0
            self.state.terminal_chain_hash = params[0]

            return

        if "ola012:health" in sql:
            if not self.state.healthy:
                raise RuntimeError(
                    "database unavailable"
                )

            self._one = (1,)
            return

        if "ola012:select_state" in sql:
            if not self.state.healthy:
                raise RuntimeError(
                    "database unavailable"
                )

            if not self.state.state_present:
                self._one = None

            else:
                self._one = (
                    self.state.sequence_number,
                    self.state.terminal_chain_hash,
                )

            return

        raise AssertionError(
            f"unexpected SQL marker: {sql}"
        )

    def fetchone(self):
        return self._one

    def fetchall(self):
        return []

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


class FakeDriverModule:
    def __init__(
        self,
        state,
    ):
        self.state = state
        self.calls = []

    def connect(
        self,
        **kwargs,
    ):
        self.calls.append(
            dict(kwargs)
        )

        return FakeConnection(
            self.state
        )


def build_configuration_and_factory(
    *,
    state,
):
    secret_contract = (
        PostgreSQLSecretEnvironmentContract.create(
            password_environment_variable=(
                "ORACLE_POSTGRES_PASSWORD"
            ),
            driver_module="psycopg",
            driver_connect_attribute="connect",
        )
    )

    engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    configuration = engine.create_sanitized_configuration(
        host="db.oracle.internal",
        port=5432,
        database="oracle_intelligence",
        username="oracle_readonly_ingest",
        sslmode="require",
        connect_timeout_seconds=10,
        application_name=(
            "qseries_oracle_live_acquisition"
        ),
        secret_contract=secret_contract,
        configured_at=CONFIGURED_AT,
        configuration_metadata={
            "environment": "production",
            "bootstrap_required": True,
        },
    )

    driver = FakeDriverModule(
        state
    )

    factory, evidence = engine.build_connection_factory(
        configuration=configuration,
        created_at=FACTORY_CREATED_AT,
        environment={
            "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
        },
        module_loader=lambda _: driver,
    )

    return (
        configuration,
        factory,
        evidence,
        driver,
    )


def run_empty_backend_bootstrap_test():
    state = FakePostgreSQLState()

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    first = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=configuration,
            connection_factory_evidence=evidence,
            connection_factory=factory,
            bootstrap_started_at=BOOTSTRAP_STARTED_AT,
            bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
            bootstrap_metadata={
                "environment": "production",
                "bootstrap_mode": "pre_live_source",
            },
        )
    )

    second_state = FakePostgreSQLState()

    (
        second_configuration,
        second_factory,
        second_evidence,
        second_driver,
    ) = build_configuration_and_factory(
        state=second_state
    )

    second = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=second_configuration,
            connection_factory_evidence=second_evidence,
            connection_factory=second_factory,
            bootstrap_started_at=BOOTSTRAP_STARTED_AT,
            bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
            bootstrap_metadata={
                "environment": "production",
                "bootstrap_mode": "pre_live_source",
            },
        )
    )

    assert first == second

    assert first.schema_version == "OLA-014"
    assert first.engine_id == "OLA-014"

    assert first.bootstrap_id.startswith(
        "postgresql_bootstrap."
    )

    assert first.bootstrap_status == "passed"

    assert first.backend_id == (
        "backend.oracle.postgresql.canonical"
    )

    assert first.backend_type == "postgresql"

    assert (
        first.configuration_id
        == configuration.configuration_id
    )

    assert (
        first.configuration_hash
        == configuration.configuration_hash
    )

    assert (
        first.connection_factory_evidence_hash
        == evidence.evidence_hash
    )

    assert first.schema_initialized is True

    assert first.backend_contract_satisfied is True

    assert first.backend_health_status == "healthy"
    assert first.backend_healthy is True

    assert (
        first.expected_genesis_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert (
        first.observed_terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert first.empty_backend_state is True
    assert first.chain_state_compatible is True

    assert first.live_write_ready is True

    assert first.acquisition_performed is False
    assert first.routing_performed is False

    assert (
        "approved_genesis_chain_verified"
        in first.reason_codes
    )

    assert (
        "production_bootstrap_gate_passed"
        in first.reason_codes
    )

    assert "create_observations" in state.schema_markers

    assert "create_source_index" in state.schema_markers

    assert "create_observed_index" in state.schema_markers

    assert "create_state" in state.schema_markers

    assert "create_checkpoints" in state.schema_markers

    canonical = first.to_canonical_dict()

    assert SECRET_VALUE not in str(
        canonical
    )

    assert first.bootstrap_hash == second.bootstrap_hash

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
        first.live_write_ready = False

        raise AssertionError(
            "bootstrap record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return first


def run_existing_chain_bootstrap_test():
    existing_chain_hash = (
        "chain."
        "85f75a71a9e5bcfe177b333f746355a7"
        "129901e54dbb992d91ff7e6437eb1580"
    )

    state = FakePostgreSQLState(
        terminal_chain_hash=existing_chain_hash
    )

    state.sequence_number = 250

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    result = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=configuration,
            connection_factory_evidence=evidence,
            connection_factory=factory,
            bootstrap_started_at=BOOTSTRAP_STARTED_AT,
            bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
            bootstrap_metadata={
                "environment": "production",
                "bootstrap_mode": "restart_validation",
            },
        )
    )

    assert result.bootstrap_status == "passed"

    assert result.empty_backend_state is False

    assert result.observed_terminal_chain_hash == (
        existing_chain_hash
    )

    assert result.chain_state_compatible is True

    assert result.live_write_ready is True

    assert (
        "existing_terminal_chain_preserved"
        in result.reason_codes
    )

    assert (
        "existing_backend_state_accepted"
        in result.reason_codes
    )

    return result


def run_configuration_identity_mismatch_test():
    state = FakePostgreSQLState()

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    second_state = FakePostgreSQLState()

    (
        second_configuration,
        second_factory,
        second_evidence,
        second_driver,
    ) = build_configuration_and_factory(
        state=second_state
    )

    bad_evidence = type(evidence)(
        schema_version=evidence.schema_version,
        engine_id=evidence.engine_id,
        configuration_id="postgresql_config.foreign",
        configuration_hash=evidence.configuration_hash,
        driver_module=evidence.driver_module,
        driver_connect_attribute=(
            evidence.driver_connect_attribute
        ),
        password_environment_variable=(
            evidence.password_environment_variable
        ),
        created_at=evidence.created_at,
        factory_status=evidence.factory_status,
        reason_codes=evidence.reason_codes,
        secret_value_read=evidence.secret_value_read,
        secret_value_canonicalized=(
            evidence.secret_value_canonicalized
        ),
        secret_value_returned=(
            evidence.secret_value_returned
        ),
        raw_dsn_created=evidence.raw_dsn_created,
        evidence_hash=evidence.evidence_hash,
        read_only=evidence.read_only,
        execution_allowed=evidence.execution_allowed,
        execution_adapter_resolved=(
            evidence.execution_adapter_resolved
        ),
        execution_adapter_invoked=(
            evidence.execution_adapter_invoked
        ),
        trade_authorization_allowed=(
            evidence.trade_authorization_allowed
        ),
        order_placement_allowed=(
            evidence.order_placement_allowed
        ),
        funds_moved=evidence.funds_moved,
        portfolio_mutated=evidence.portfolio_mutated,
    )

    try:
        (
            OraclePostgreSQLProductionBootstrapMigrationGate()
            .bootstrap(
                configuration=configuration,
                connection_factory_evidence=bad_evidence,
                connection_factory=factory,
                bootstrap_started_at=BOOTSTRAP_STARTED_AT,
                bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
                bootstrap_metadata={},
            )
        )

        raise AssertionError(
            "configuration identity mismatch must fail closed"
        )

    except PostgreSQLBootstrapCompatibilityError:
        pass


def run_unhealthy_backend_fail_closed_test():
    state = FakePostgreSQLState(
        healthy=False
    )

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    try:
        (
            OraclePostgreSQLProductionBootstrapMigrationGate()
            .bootstrap(
                configuration=configuration,
                connection_factory_evidence=evidence,
                connection_factory=factory,
                bootstrap_started_at=BOOTSTRAP_STARTED_AT,
                bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
                bootstrap_metadata={},
            )
        )

        raise AssertionError(
            "unhealthy PostgreSQL backend must fail closed"
        )

    except PostgreSQLBootstrapCompatibilityError:
        pass


def run_forbidden_metadata_fail_closed_test():
    state = FakePostgreSQLState()

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    try:
        (
            OraclePostgreSQLProductionBootstrapMigrationGate()
            .bootstrap(
                configuration=configuration,
                connection_factory_evidence=evidence,
                connection_factory=factory,
                bootstrap_started_at=BOOTSTRAP_STARTED_AT,
                bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
                bootstrap_metadata={
                    "password": SECRET_VALUE,
                },
            )
        )

        raise AssertionError(
            "secret-bearing bootstrap metadata must fail closed"
        )

    except PostgreSQLBootstrapContractError:
        pass


def run_timestamp_fail_closed_test():
    state = FakePostgreSQLState()

    (
        configuration,
        factory,
        evidence,
        driver,
    ) = build_configuration_and_factory(
        state=state
    )

    try:
        (
            OraclePostgreSQLProductionBootstrapMigrationGate()
            .bootstrap(
                configuration=configuration,
                connection_factory_evidence=evidence,
                connection_factory=factory,
                bootstrap_started_at=datetime(
                    2026,
                    7,
                    12,
                    5,
                    0,
                    2,
                ),
                bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
                bootstrap_metadata={},
            )
        )

        raise AssertionError(
            "naive bootstrap_started_at must fail closed"
        )

    except PostgreSQLBootstrapContractError:
        pass

    try:
        (
            OraclePostgreSQLProductionBootstrapMigrationGate()
            .bootstrap(
                configuration=configuration,
                connection_factory_evidence=evidence,
                connection_factory=factory,
                bootstrap_started_at=BOOTSTRAP_STARTED_AT,
                bootstrap_completed_at=datetime(
                    2026,
                    7,
                    12,
                    5,
                    0,
                    1,
                    tzinfo=timezone.utc,
                ),
                bootstrap_metadata={},
            )
        )

        raise AssertionError(
            "bootstrap completion before start must fail closed"
        )

    except PostgreSQLBootstrapContractError:
        pass


def main():
    empty_backend = run_empty_backend_bootstrap_test()

    existing_backend = (
        run_existing_chain_bootstrap_test()
    )

    run_configuration_identity_mismatch_test()
    run_unhealthy_backend_fail_closed_test()
    run_forbidden_metadata_fail_closed_test()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": empty_backend.schema_version,
        "engine_id": empty_backend.engine_id,
        "status": "passed",
        "bootstrap_status": (
            empty_backend.bootstrap_status
        ),
        "backend_id": empty_backend.backend_id,
        "backend_type": empty_backend.backend_type,
        "schema_initialized": (
            empty_backend.schema_initialized
        ),
        "ola_011_contract_satisfied": (
            empty_backend.backend_contract_satisfied
        ),
        "backend_health_status": (
            empty_backend.backend_health_status
        ),
        "approved_genesis_chain_verified": (
            empty_backend.empty_backend_state
            and empty_backend.observed_terminal_chain_hash
            == empty_backend.expected_genesis_chain_hash
        ),
        "existing_chain_state_accepted": (
            existing_backend.empty_backend_state
            is False
            and existing_backend.chain_state_compatible
        ),
        "live_write_ready": (
            empty_backend.live_write_ready
        ),
        "acquisition_performed": (
            empty_backend.acquisition_performed
        ),
        "routing_performed": (
            empty_backend.routing_performed
        ),
        "configuration_identity_mismatch_blocked": True,
        "unhealthy_backend_blocked": True,
        "secret_metadata_blocked": True,
        "deterministic_bootstrap_hashing": True,
        "read_only": empty_backend.read_only,
        "execution_allowed": (
            empty_backend.execution_allowed
        ),
        "execution_adapter_resolved": (
            empty_backend.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            empty_backend.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            empty_backend.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            empty_backend.order_placement_allowed
        ),
        "funds_moved": empty_backend.funds_moved,
        "portfolio_mutated": (
            empty_backend.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-014 Oracle PostgreSQL Production "
        "Bootstrap and Migration Gate"
    )

    print(result)


if __name__ == "__main__":
    main()
