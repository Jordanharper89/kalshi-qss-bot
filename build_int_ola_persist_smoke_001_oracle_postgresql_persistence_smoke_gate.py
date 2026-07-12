from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_int_ola_persist_smoke_001_"
    "oracle_postgresql_persistence_smoke_gate.py"
)


TEST_CONTENT = r'''
"""
INT-OLA-PERSIST-SMOKE-001
Oracle PostgreSQL Persistence Smoke Integration Gate

Smoke integration checkpoint for OLA-011 through OLA-015.

Validated production persistence architecture:

OLA-011 CANONICAL BACKEND CONTRACT
    |
OLA-013 SECURE CONFIGURATION / SECRET BOUNDARY
    |
OLA-014 PRODUCTION BOOTSTRAP / MIGRATION GATE
    |
OLA-012 POSTGRESQL CANONICAL PERSISTENCE BACKEND
    |
OLA-015 POSTGRESQL PERSISTENCE ROUTER
    |
COMMITTED CANONICAL OBSERVATION HISTORY
    |
QUERY / CHECKPOINT EVIDENCE

This gate proves:

- the physical backend satisfies OLA-011,
- secrets remain outside canonical evidence,
- PostgreSQL schema bootstrap occurs before writes,
- approved chain genesis is verified,
- the backend is declared live-write ready,
- canonical observations route through OLA-015,
- routing acceptance occurs only after committed PostgreSQL append,
- sequence order is preserved,
- chain continuity is preserved,
- duplicate routing fails closed,
- observations can be read by observation identity,
- observations can be read by source identity,
- observations can be read by observed time range,
- an immutable snapshot checkpoint can be written and restored,
- deterministic replay reproduces canonical persistence evidence,
- Oracle remains permanently read-only,
- no execution adapter is resolved,
- no execution adapter is invoked,
- no trade is authorized,
- no order is placed,
- no funds are moved,
- no portfolio is mutated.
"""

from datetime import datetime, timezone
from decimal import Decimal


from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OraclePersistenceBackendContractValidator,
    RawSourceObservation,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_secure_configuration_connection_factory import (
    OraclePostgreSQLSecureConfigurationConnectionFactory,
    PostgreSQLSecretEnvironmentContract,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_production_bootstrap_migration_gate import (
    OraclePostgreSQLProductionBootstrapMigrationGate,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
    PostgreSQLPersistenceRoutingFailure,
)


SCHEMA_VERSION = "INT-OLA-PERSIST-SMOKE-001"
ENGINE_ID = "INT-OLA-PERSIST-SMOKE-001"


CONFIGURED_AT = datetime(
    2026,
    7,
    12,
    7,
    0,
    0,
    tzinfo=timezone.utc,
)

FACTORY_CREATED_AT = datetime(
    2026,
    7,
    12,
    7,
    0,
    1,
    tzinfo=timezone.utc,
)

BOOTSTRAP_STARTED_AT = datetime(
    2026,
    7,
    12,
    7,
    0,
    2,
    tzinfo=timezone.utc,
)

BOOTSTRAP_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    7,
    0,
    3,
    tzinfo=timezone.utc,
)

OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    7,
    1,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    7,
    1,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    7,
    2,
    0,
    tzinfo=timezone.utc,
)

ROUTED_AT_ONE = datetime(
    2026,
    7,
    12,
    7,
    2,
    1,
    tzinfo=timezone.utc,
)

ROUTED_AT_TWO = datetime(
    2026,
    7,
    12,
    7,
    2,
    2,
    tzinfo=timezone.utc,
)

QUERY_REQUESTED_AT = datetime(
    2026,
    7,
    12,
    7,
    3,
    0,
    tzinfo=timezone.utc,
)

CHECKPOINTED_AT = datetime(
    2026,
    7,
    12,
    7,
    4,
    0,
    tzinfo=timezone.utc,
)


SECRET_VALUE = (
    "INT_OLA_PERSIST_SMOKE_SECRET_VALUE"
)


class FakePostgreSQLState:
    def __init__(self):
        self.sequence_number = 0

        self.terminal_chain_hash = (
            GENESIS_CHAIN_HASH
        )

        self.observations = []

        self.checkpoints = {}

        self.schema_markers = set()

        self.connection_count = 0


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

        if "ola012:health" in sql:
            self._one = (1,)
            self._all = [(1,)]

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

        if "ola012:query_by_observation_id" in sql:
            observation_id = params[0]

            matches = [
                row
                for row in self.state.observations
                if (
                    row["observation_id"]
                    == observation_id
                )
            ]

            matches.sort(
                key=lambda row: row["sequence_number"]
            )

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:1]
            ]

            return

        if "ola012:query_by_source_id" in sql:
            source_id = params[0]
            limit = int(params[1])

            matches = [
                row
                for row in self.state.observations
                if row["source_id"] == source_id
            ]

            matches.sort(
                key=lambda row: row["sequence_number"]
            )

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:limit]
            ]

            return

        if "ola012:query_by_time_range" in sql:
            observed_from = params[0]
            observed_to = params[1]
            limit = int(params[2])

            matches = [
                row
                for row in self.state.observations
                if (
                    observed_from
                    <= row["observed_at"]
                    <= observed_to
                )
            ]

            matches.sort(
                key=lambda row: (
                    row["observed_at"],
                    row["sequence_number"],
                )
            )

            self._all = [
                (
                    row["canonical_observation_json"],
                )
                for row in matches[:limit]
            ]

            return

        if "ola012:insert_checkpoint" in sql:
            checkpoint_id = params[0]

            if checkpoint_id in self.state.checkpoints:
                raise RuntimeError(
                    "duplicate checkpoint identity"
                )

            self.state.checkpoints[
                checkpoint_id
            ] = params[8]

            return

        if "ola012:select_checkpoint" in sql:
            checkpoint_id = params[0]

            checkpoint = self.state.checkpoints.get(
                checkpoint_id
            )

            self._one = (
                None
                if checkpoint is None
                else (checkpoint,)
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

        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return FakeCursor(
            self.state
        )

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

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

        self.state.connection_count += 1

        return FakeConnection(
            self.state
        )


def build_secret_contract():
    return PostgreSQLSecretEnvironmentContract.create(
        password_environment_variable=(
            "ORACLE_POSTGRES_PASSWORD"
        ),
        driver_module="psycopg",
        driver_connect_attribute="connect",
    )


def build_sanitized_configuration():
    return (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
        .create_sanitized_configuration(
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
                "environment": "production",
                "integration_gate": ENGINE_ID,
                "persistence_backend": (
                    "backend.oracle.postgresql.canonical"
                ),
            },
        )
    )


def build_production_persistence_system():
    state = FakePostgreSQLState()

    driver = FakeDriverModule(
        state
    )

    configuration = build_sanitized_configuration()

    secure_factory_engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    connection_factory, factory_evidence = (
        secure_factory_engine.build_connection_factory(
            configuration=configuration,
            created_at=FACTORY_CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": (
                    SECRET_VALUE
                ),
            },
            module_loader=lambda _: driver,
        )
    )

    bootstrap = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=configuration,
            connection_factory_evidence=(
                factory_evidence
            ),
            connection_factory=connection_factory,
            bootstrap_started_at=(
                BOOTSTRAP_STARTED_AT
            ),
            bootstrap_completed_at=(
                BOOTSTRAP_COMPLETED_AT
            ),
            bootstrap_metadata={
                "environment": "production",
                "integration_gate": ENGINE_ID,
                "bootstrap_mode": "pre_live_source",
            },
        )
    )

    backend = (
        OraclePostgreSQLCanonicalObservationPersistenceBackend(
            connection_factory=connection_factory,
            auto_initialize_schema=False,
        )
    )

    capability, health = (
        OraclePersistenceBackendContractValidator()
        .validate_backend(
            backend=backend,
            checked_at=BOOTSTRAP_COMPLETED_AT,
        )
    )

    router = (
        OraclePostgreSQLCanonicalObservationPersistenceRouter(
            persistence_backend=backend,
            route_id=(
                "oracle.postgresql.canonical."
                "persistence.router.smoke.v1"
            ),
            routing_metadata={
                "persistence_policy_id": (
                    "oracle.postgresql.canonical.v1"
                ),
                "integration_gate": ENGINE_ID,
                "production_path": True,
            },
            replay_metadata={
                "integration_gate": ENGINE_ID,
                "replay_source": (
                    "postgresql_persistence_smoke_gate"
                ),
                "replay_version": 1,
            },
            audit_metadata={
                "integration_gate": ENGINE_ID,
                "request_id": (
                    "audit-int-ola-persist-smoke-001"
                ),
            },
        )
    )

    return {
        "state": state,
        "driver": driver,
        "configuration": configuration,
        "connection_factory": connection_factory,
        "factory_evidence": factory_evidence,
        "bootstrap": bootstrap,
        "backend": backend,
        "capability": capability,
        "health": health,
        "router": router,
    }


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id=(
            "persistence.smoke.snapshot.001"
        ),
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "source_market_id": (
                "KXBTC-PERSIST-SMOKE-001"
            ),
            "instrument_type": (
                "prediction_contract"
            ),
            "venue_claim": "venue.kalshi",
            "share_side": "yes",
            "share_price": Decimal("0.31"),
            "volume": 1500,
        },
        provenance={
            "source_id": "source.kalshi.market_data",
            "adapter_id": (
                "adapter.oracle.persistence.smoke"
            ),
            "integration_gate": ENGINE_ID,
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id=(
            "batch.int.ola.persist.smoke.001"
        ),
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id=(
            "persistence.smoke.snapshot.002"
        ),
        observed_at=OBSERVED_AT_TWO,
        observation_type="market_snapshot",
        payload={
            "source_market_id": (
                "KXBTC-PERSIST-SMOKE-002"
            ),
            "instrument_type": (
                "prediction_contract"
            ),
            "venue_claim": "venue.kalshi",
            "share_side": "yes",
            "share_price": Decimal("0.44"),
            "volume": 2100,
        },
        provenance={
            "source_id": "source.kalshi.market_data",
            "adapter_id": (
                "adapter.oracle.persistence.smoke"
            ),
            "integration_gate": ENGINE_ID,
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id=(
            "batch.int.ola.persist.smoke.001"
        ),
    )


def run_bootstrap_and_contract_path():
    system = build_production_persistence_system()

    configuration = system["configuration"]
    factory_evidence = system["factory_evidence"]
    bootstrap = system["bootstrap"]
    capability = system["capability"]
    health = system["health"]
    backend = system["backend"]
    state = system["state"]

    assert configuration.schema_version == "OLA-013"
    assert configuration.engine_id == "OLA-013"

    assert configuration.secret_value_present is False

    assert (
        configuration.secret_value_canonicalized
        is False
    )

    assert configuration.raw_dsn_stored is False

    assert SECRET_VALUE not in str(
        configuration.to_canonical_dict()
    )

    assert factory_evidence.factory_status == "ready"

    assert factory_evidence.secret_value_read is True

    assert (
        factory_evidence.secret_value_canonicalized
        is False
    )

    assert (
        factory_evidence.secret_value_returned
        is False
    )

    assert factory_evidence.raw_dsn_created is False

    assert SECRET_VALUE not in str(
        factory_evidence.to_canonical_dict()
    )

    assert bootstrap.schema_version == "OLA-014"
    assert bootstrap.engine_id == "OLA-014"

    assert bootstrap.bootstrap_status == "passed"

    assert bootstrap.schema_initialized is True

    assert (
        bootstrap.backend_contract_satisfied
        is True
    )

    assert bootstrap.backend_health_status == "healthy"

    assert bootstrap.backend_healthy is True

    assert bootstrap.empty_backend_state is True

    assert bootstrap.chain_state_compatible is True

    assert bootstrap.live_write_ready is True

    assert bootstrap.acquisition_performed is False

    assert bootstrap.routing_performed is False

    assert (
        bootstrap.observed_terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert SECRET_VALUE not in str(
        bootstrap.to_canonical_dict()
    )

    assert capability.schema_version == "OLA-011"

    assert capability.contract_satisfied is True

    assert (
        capability.missing_required_capabilities
        == ()
    )

    assert health.health_status == "healthy"

    assert health.healthy is True

    assert backend.terminal_chain_hash() == (
        GENESIS_CHAIN_HASH
    )

    assert "create_observations" in state.schema_markers

    assert "create_source_index" in state.schema_markers

    assert "create_observed_index" in state.schema_markers

    assert "create_state" in state.schema_markers

    assert "create_checkpoints" in state.schema_markers

    return system


def run_committed_routing_path():
    system = run_bootstrap_and_contract_path()

    router = system["router"]
    backend = system["backend"]
    state = system["state"]

    observation_one = build_observation_one()

    observation_two = build_observation_two()

    first_evidence = router(
        observation_one,
        ROUTED_AT_ONE,
    )

    first_record = router.get_routing_record(
        observation_id=observation_one.observation_id
    )

    assert first_record is not None

    first_terminal_hash = (
        backend.terminal_chain_hash()
    )

    second_evidence = router(
        observation_two,
        ROUTED_AT_TWO,
    )

    second_record = router.get_routing_record(
        observation_id=observation_two.observation_id
    )

    assert second_record is not None

    second_terminal_hash = (
        backend.terminal_chain_hash()
    )

    assert first_evidence.accepted is True

    assert second_evidence.accepted is True

    assert first_record.persistence_committed is True

    assert first_record.persistence_atomic is True

    assert first_record.persistence_verified is True

    assert first_record.routing_accepted is True

    assert second_record.persistence_committed is True

    assert second_record.persistence_atomic is True

    assert second_record.persistence_verified is True

    assert second_record.routing_accepted is True

    assert first_record.persistence_sequence_number == 1

    assert second_record.persistence_sequence_number == 2

    assert (
        first_record.prior_terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert (
        second_record.prior_terminal_chain_hash
        == first_record.terminal_chain_hash
    )

    assert (
        first_terminal_hash
        == first_record.terminal_chain_hash
    )

    assert (
        second_terminal_hash
        == second_record.terminal_chain_hash
    )

    assert first_terminal_hash != GENESIS_CHAIN_HASH

    assert second_terminal_hash != first_terminal_hash

    assert len(state.observations) == 2

    assert state.sequence_number == 2

    assert (
        state.observations[0]["observation_id"]
        == observation_one.observation_id
    )

    assert (
        state.observations[1]["observation_id"]
        == observation_two.observation_id
    )

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

    return {
        "system": system,
        "observation_one": observation_one,
        "observation_two": observation_two,
        "first_evidence": first_evidence,
        "second_evidence": second_evidence,
        "first_record": first_record,
        "second_record": second_record,
    }


def run_query_and_checkpoint_path():
    result = run_committed_routing_path()

    system = result["system"]

    backend = system["backend"]

    state = system["state"]

    observation_one = result["observation_one"]

    observation_two = result["observation_two"]

    by_id_request = (
        CanonicalPersistenceQueryRequest
        .by_observation_id(
            query_id=(
                "query.persist.smoke.by_observation_id"
            ),
            backend_id=backend.backend_id,
            observation_id=(
                observation_one.observation_id
            ),
            requested_at=QUERY_REQUESTED_AT,
            query_metadata={
                "integration_gate": ENGINE_ID,
            },
        )
    )

    by_id_results = backend.query(
        request=by_id_request
    )

    assert by_id_results == (
        observation_one,
    )

    by_source_request = (
        CanonicalPersistenceQueryRequest
        .by_source_id(
            query_id="query.persist.smoke.by_source",
            backend_id=backend.backend_id,
            source_id="source.kalshi.market_data",
            limit=10,
            requested_at=QUERY_REQUESTED_AT,
            query_metadata={
                "integration_gate": ENGINE_ID,
            },
        )
    )

    by_source_results = backend.query(
        request=by_source_request
    )

    assert by_source_results == (
        observation_one,
        observation_two,
    )

    by_time_request = (
        CanonicalPersistenceQueryRequest
        .by_observed_time_range(
            query_id="query.persist.smoke.by_time",
            backend_id=backend.backend_id,
            observed_from=OBSERVED_AT_ONE,
            observed_to=OBSERVED_AT_TWO,
            limit=10,
            requested_at=QUERY_REQUESTED_AT,
            query_metadata={
                "integration_gate": ENGINE_ID,
            },
        )
    )

    by_time_results = backend.query(
        request=by_time_request
    )

    assert by_time_results == (
        observation_one,
        observation_two,
    )

    checkpoint = (
        CanonicalPersistenceSnapshotCheckpoint.create(
            checkpoint_id=(
                "checkpoint.int.ola.persist.smoke.001"
            ),
            backend_id=backend.backend_id,
            snapshot_schema_version="OLA-008",
            snapshot_engine_id="OLA-008",
            snapshot_hash=(
                "snapshot.int.ola.persist.smoke.001"
            ),
            entry_count=2,
            terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
            checkpointed_at=CHECKPOINTED_AT,
            checkpoint_metadata={
                "integration_gate": ENGINE_ID,
                "archive_required": True,
                "checkpoint_type": (
                    "postgresql_persistence_smoke"
                ),
            },
        )
    )

    stored_checkpoint = (
        backend.write_snapshot_checkpoint(
            checkpoint=checkpoint
        )
    )

    restored_checkpoint = (
        backend.read_snapshot_checkpoint(
            checkpoint_id=checkpoint.checkpoint_id
        )
    )

    assert stored_checkpoint == checkpoint

    assert restored_checkpoint == checkpoint

    assert checkpoint.checkpoint_id in state.checkpoints

    assert checkpoint.immutable is True

    assert checkpoint.read_only is True

    assert checkpoint.execution_allowed is False

    return {
        **result,
        "by_id_results": by_id_results,
        "by_source_results": by_source_results,
        "by_time_results": by_time_results,
        "checkpoint": checkpoint,
        "restored_checkpoint": restored_checkpoint,
    }


def run_duplicate_fail_closed_path():
    system = build_production_persistence_system()

    router = system["router"]

    backend = system["backend"]

    state = system["state"]

    observation = build_observation_one()

    router(
        observation,
        ROUTED_AT_ONE,
    )

    terminal_hash_before_duplicate = (
        backend.terminal_chain_hash()
    )

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "duplicate routing must fail closed"
        )

    except PostgreSQLPersistenceRoutingFailure:
        pass

    assert len(state.observations) == 1

    assert state.sequence_number == 1

    assert (
        backend.terminal_chain_hash()
        == terminal_hash_before_duplicate
    )

    assert router.routing_record_count == 1


def assert_permanent_no_execution_invariants(
    result,
):
    system = result["system"]

    configuration = system["configuration"]

    factory_evidence = system["factory_evidence"]

    bootstrap = system["bootstrap"]

    capability = system["capability"]

    health = system["health"]

    backend = system["backend"]

    router = system["router"]

    first_record = result["first_record"]

    second_record = result["second_record"]

    assert configuration.read_only is True
    assert configuration.execution_allowed is False

    assert (
        configuration.execution_adapter_resolved
        is False
    )

    assert (
        configuration.execution_adapter_invoked
        is False
    )

    assert (
        configuration.trade_authorization_allowed
        is False
    )

    assert (
        configuration.order_placement_allowed
        is False
    )

    assert configuration.funds_moved is False
    assert configuration.portfolio_mutated is False

    assert factory_evidence.read_only is True
    assert factory_evidence.execution_allowed is False

    assert (
        factory_evidence.execution_adapter_resolved
        is False
    )

    assert (
        factory_evidence.execution_adapter_invoked
        is False
    )

    assert (
        factory_evidence.trade_authorization_allowed
        is False
    )

    assert (
        factory_evidence.order_placement_allowed
        is False
    )

    assert factory_evidence.funds_moved is False
    assert factory_evidence.portfolio_mutated is False

    assert bootstrap.read_only is True
    assert bootstrap.execution_allowed is False

    assert bootstrap.execution_adapter_resolved is False
    assert bootstrap.execution_adapter_invoked is False

    assert (
        bootstrap.trade_authorization_allowed
        is False
    )

    assert bootstrap.order_placement_allowed is False
    assert bootstrap.funds_moved is False
    assert bootstrap.portfolio_mutated is False

    assert capability.read_only is True
    assert capability.execution_allowed is False

    assert health.read_only is True
    assert health.execution_allowed is False

    assert backend.read_only is True
    assert backend.execution_allowed is False

    assert backend.execution_adapter_resolved is False
    assert backend.execution_adapter_invoked is False

    assert backend.trade_authorization_allowed is False
    assert backend.order_placement_allowed is False
    assert backend.funds_moved is False
    assert backend.portfolio_mutated is False

    assert router.read_only is True
    assert router.execution_allowed is False

    assert router.execution_adapter_resolved is False
    assert router.execution_adapter_invoked is False

    assert router.trade_authorization_allowed is False
    assert router.order_placement_allowed is False
    assert router.funds_moved is False
    assert router.portfolio_mutated is False

    for record in (
        first_record,
        second_record,
    ):
        assert record.read_only is True

        assert record.execution_allowed is False

        assert record.execution_adapter_resolved is False

        assert record.execution_adapter_invoked is False

        assert (
            record.trade_authorization_allowed
            is False
        )

        assert record.order_placement_allowed is False

        assert record.funds_moved is False

        assert record.portfolio_mutated is False


def run_deterministic_replay_gate():
    first = run_query_and_checkpoint_path()

    second = run_query_and_checkpoint_path()

    first_system = first["system"]

    second_system = second["system"]

    assert (
        first_system["configuration"].configuration_hash
        == second_system["configuration"].configuration_hash
    )

    assert (
        first_system["factory_evidence"].evidence_hash
        == second_system["factory_evidence"].evidence_hash
    )

    assert (
        first_system["bootstrap"].bootstrap_hash
        == second_system["bootstrap"].bootstrap_hash
    )

    assert (
        first["first_evidence"]
        == second["first_evidence"]
    )

    assert (
        first["second_evidence"]
        == second["second_evidence"]
    )

    assert (
        first["first_record"]
        == second["first_record"]
    )

    assert (
        first["second_record"]
        == second["second_record"]
    )

    assert (
        first_system["backend"].terminal_chain_hash()
        == second_system["backend"].terminal_chain_hash()
    )

    assert (
        first_system["state"].observations
        == second_system["state"].observations
    )

    assert (
        first["checkpoint"]
        == second["checkpoint"]
    )

    assert (
        first["restored_checkpoint"]
        == second["restored_checkpoint"]
    )

    assert_permanent_no_execution_invariants(
        first
    )

    return first


def main():
    result = run_deterministic_replay_gate()

    run_duplicate_fail_closed_path()

    system = result["system"]

    configuration = system["configuration"]

    factory_evidence = system["factory_evidence"]

    bootstrap = system["bootstrap"]

    capability = system["capability"]

    health = system["health"]

    backend = system["backend"]

    router = system["router"]

    state = system["state"]

    first_record = result["first_record"]

    second_record = result["second_record"]

    checkpoint = result["checkpoint"]

    output = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola_011_backend_contract_passed": (
            capability.contract_satisfied
        ),
        "ola_012_postgresql_backend_passed": True,
        "ola_013_secure_configuration_passed": (
            configuration.secret_value_canonicalized
            is False
        ),
        "ola_014_bootstrap_gate_passed": (
            bootstrap.live_write_ready
        ),
        "ola_015_postgresql_router_passed": (
            first_record.persistence_verified
        ),
        "backend_id": backend.backend_id,
        "backend_type": backend.backend_type,
        "backend_health_status": health.health_status,
        "approved_genesis_chain_verified": (
            bootstrap.empty_backend_state
            and bootstrap.observed_terminal_chain_hash
            == GENESIS_CHAIN_HASH
        ),
        "live_write_ready": bootstrap.live_write_ready,
        "secret_value_canonicalized": (
            configuration.secret_value_canonicalized
        ),
        "secret_value_returned": (
            factory_evidence.secret_value_returned
        ),
        "raw_dsn_stored": configuration.raw_dsn_stored,
        "routing_record_count": (
            router.routing_record_count
        ),
        "postgresql_persistence_count": (
            len(state.observations)
        ),
        "first_sequence_number": (
            first_record.persistence_sequence_number
        ),
        "second_sequence_number": (
            second_record.persistence_sequence_number
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
        "chain_continuity_preserved": (
            second_record.prior_terminal_chain_hash
            == first_record.terminal_chain_hash
        ),
        "terminal_chain_hash_verified": (
            backend.terminal_chain_hash()
            == second_record.terminal_chain_hash
        ),
        "duplicate_route_blocked": True,
        "read_by_observation_id_passed": (
            len(result["by_id_results"]) == 1
        ),
        "read_by_source_id_passed": (
            len(result["by_source_results"]) == 2
        ),
        "read_by_observed_time_range_passed": (
            len(result["by_time_results"]) == 2
        ),
        "snapshot_checkpoint_write_passed": True,
        "snapshot_checkpoint_read_passed": (
            result["restored_checkpoint"]
            == checkpoint
        ),
        "checkpoint_id": checkpoint.checkpoint_id,
        "deterministic_replay_passed": True,
        "read_only": True,
        "execution_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-OLA-PERSIST-SMOKE-001 Oracle "
        "PostgreSQL Persistence Smoke Integration Gate"
    )

    print(output)


if __name__ == "__main__":
    main()
'''


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


def main() -> None:
    print("========================================")
    print(" INT-OLA-PERSIST-SMOKE-001 INSTALLER")
    print(" Oracle PostgreSQL Persistence")
    print(" OLA-011 Through OLA-015")
    print(" Smoke Integration Gate")
    print("========================================")

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print(
        "[DONE] INT-OLA-PERSIST-SMOKE-001 installed"
    )
    print()
    print("Run:")
    print(
        "py test_int_ola_persist_smoke_001_"
        "oracle_postgresql_persistence_smoke_gate.py"
    )


if __name__ == "__main__":
    main()