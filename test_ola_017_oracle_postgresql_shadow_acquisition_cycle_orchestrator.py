from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
from urllib.parse import parse_qs, urlparse


from qseries_v2.oracle_intelligence.live_acquisition import (
    OracleAcquisitionDeduplicationLedger,
    OracleAcquisitionSourceControlEngine,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlPolicy,
    RateWindowObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
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
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_public_market_shadow_source_adapter import (
    OracleKalshiPublicMarketShadowSourceAdapter,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (
    OraclePostgreSQLShadowAcquisitionCycleOrchestrator,
)


CONFIGURED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    0,
    tzinfo=timezone.utc,
)

FACTORY_CREATED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    1,
    tzinfo=timezone.utc,
)

BOOTSTRAP_STARTED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    2,
    tzinfo=timezone.utc,
)

BOOTSTRAP_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    3,
    tzinfo=timezone.utc,
)

CONTROL_CHECKED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    50,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    0,
    tzinfo=timezone.utc,
)

CONTROL_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    9,
    0,
    55,
    tzinfo=timezone.utc,
)

CYCLE_STARTED_AT = datetime(
    2026,
    7,
    12,
    9,
    1,
    0,
    tzinfo=timezone.utc,
)

CYCLE_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    9,
    1,
    3,
    tzinfo=timezone.utc,
)


SECRET_VALUE = "OLA_017_POSTGRES_SECRET"


FIRST_MARKET = {
    "ticker": "KXBTC-26JUL12-116000",
    "event_ticker": "KXBTC-26JUL12",
    "title": "Bitcoin below 116000 by 5 PM",
    "subtitle": "OLA-017 shadow cycle",
    "yes_sub_title": "Yes",
    "no_sub_title": "No",
    "created_time": "2026-07-12T08:50:00Z",
    "updated_time": "2026-07-12T09:00:58Z",
    "open_time": "2026-07-12T08:55:00Z",
    "close_time": "2026-07-12T22:00:00Z",
    "latest_expiration_time": "2026-07-12T22:05:00Z",
    "expected_expiration_time": "2026-07-12T22:00:00Z",
    "expiration_time": "2026-07-12T22:00:00Z",
    "occurrence_datetime": "2026-07-12T21:00:00Z",
    "yes_bid_dollars": "0.3000",
    "yes_bid_size_fp": "25.00",
    "yes_ask_dollars": "0.3200",
    "yes_ask_size_fp": "30.00",
    "no_bid_dollars": "0.6800",
    "no_ask_dollars": "0.7000",
    "last_price_dollars": "0.3100",
    "previous_yes_bid_dollars": "0.2900",
    "previous_yes_ask_dollars": "0.3200",
    "previous_price_dollars": "0.3000",
    "volume_fp": "1250.00",
    "volume_24h_fp": "1250.00",
    "open_interest_fp": "420.00",
    "liquidity_dollars": "5400.00",
    "notional_value_dollars": "1.0000",
    "can_close_early": False,
    "early_close_condition": "",
    "settlement_timer_seconds": 60,
    "rules_primary": "Test rules",
    "rules_secondary": "",
    "price_level_structure": "linear_cent",
    "floor_strike": 116000,
    "cap_strike": None,
    "functional_strike": "116000",
    "is_provisional": False,
    "exchange_index": 1,
}


SECOND_MARKET = {
    **FIRST_MARKET,
    "ticker": "KXBTC-26JUL12-117000",
    "title": "Bitcoin below 117000 by 5 PM",
    "updated_time": "2026-07-12T09:00:59Z",
    "yes_bid_dollars": "0.4300",
    "yes_ask_dollars": "0.4500",
    "last_price_dollars": "0.4400",
    "volume_fp": "1800.00",
    "volume_24h_fp": "1800.00",
    "liquidity_dollars": "7100.00",
    "floor_strike": 117000,
    "functional_strike": "117000",
}


class DeterministicKalshiFetcher:
    def __init__(
        self,
    ):
        self.calls = []

    def __call__(
        self,
        *,
        url,
        timeout_seconds,
    ):
        self.calls.append(
            {
                "url": url,
                "timeout_seconds": timeout_seconds,
            }
        )

        query = parse_qs(
            urlparse(url).query
        )

        cursor = query.get(
            "cursor",
            [None],
        )[0]

        if cursor is None:
            return (
                200,
                json.dumps(
                    {
                        "markets": [
                            FIRST_MARKET,
                            FIRST_MARKET,
                        ],
                        "cursor": "page.two",
                    }
                ),
            )

        if cursor == "page.two":
            return (
                200,
                json.dumps(
                    {
                        "markets": [
                            SECOND_MARKET,
                        ],
                        "cursor": "",
                    }
                ),
            )

        raise AssertionError(
            "unexpected Kalshi cursor"
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


class FakeDriver:
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


def build_postgresql_path():
    state = FakePostgreSQLState()

    driver = FakeDriver(
        state
    )

    secure_engine = (
        OraclePostgreSQLSecureConfigurationConnectionFactory()
    )

    secret_contract = (
        PostgreSQLSecretEnvironmentContract.create(
            password_environment_variable=(
                "ORACLE_POSTGRES_PASSWORD"
            ),
            driver_module="psycopg",
            driver_connect_attribute="connect",
        )
    )

    configuration = (
        secure_engine.create_sanitized_configuration(
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
                "shadow_mode": True,
            },
        )
    )

    connection_factory, factory_evidence = (
        secure_engine.build_connection_factory(
            configuration=configuration,
            created_at=FACTORY_CREATED_AT,
            environment={
                "ORACLE_POSTGRES_PASSWORD": SECRET_VALUE,
            },
            module_loader=lambda _: driver,
        )
    )

    bootstrap = (
        OraclePostgreSQLProductionBootstrapMigrationGate()
        .bootstrap(
            configuration=configuration,
            connection_factory_evidence=factory_evidence,
            connection_factory=connection_factory,
            bootstrap_started_at=BOOTSTRAP_STARTED_AT,
            bootstrap_completed_at=BOOTSTRAP_COMPLETED_AT,
            bootstrap_metadata={
                "environment": "production",
                "mode": "shadow",
            },
        )
    )

    backend = (
        OraclePostgreSQLCanonicalObservationPersistenceBackend(
            connection_factory=connection_factory,
            auto_initialize_schema=False,
        )
    )

    router = (
        OraclePostgreSQLCanonicalObservationPersistenceRouter(
            persistence_backend=backend,
            route_id=(
                "oracle.postgresql.kalshi.shadow.router.v1"
            ),
            routing_metadata={
                "production_path": True,
                "shadow_mode": True,
            },
            replay_metadata={
                "replay_source": "ola017",
            },
            audit_metadata={
                "request_id": "audit-ola-017-router",
            },
        )
    )

    return {
        "state": state,
        "driver": driver,
        "configuration": configuration,
        "factory_evidence": factory_evidence,
        "bootstrap": bootstrap,
        "backend": backend,
        "router": router,
    }


def build_source_control_decision(
    *,
    healthy,
):
    engine = OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.kalshi.market_data": (
                SourceHealthPolicy.create(
                    policy_id="health.kalshi.ola017.v1",
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=0,
                    max_latency_ms=500,
                ),
                RateControlPolicy.create(
                    policy_id="rate.kalshi.ola017.v1",
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=10,
                ),
            )
        }
    )

    health = SourceHealthObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=CONTROL_CHECKED_AT,
        reachable=healthy,
        consecutive_failures=(
            0
            if healthy
            else 1
        ),
        latency_ms=(
            40
            if healthy
            else None
        ),
        metadata={
            "probe_id": "probe.ola017",
            "shadow_mode": True,
        },
    )

    rate = RateWindowObservation.create(
        source_id="source.kalshi.market_data",
        checked_at=CONTROL_CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=5,
        metadata={
            "counter_id": "rate.ola017",
        },
    )

    return engine.evaluate(
        health_observation=health,
        rate_observation=rate,
        evaluated_at=CONTROL_EVALUATED_AT,
        replay_metadata={
            "test": "ola017",
        },
        audit_metadata={
            "request_id": "audit-ola017-control",
        },
    )


def build_system():
    postgresql = build_postgresql_path()

    fetcher = DeterministicKalshiFetcher()

    adapter = (
        OracleKalshiPublicMarketShadowSourceAdapter(
            market_status="open",
            page_limit=1000,
            max_pages=2,
            timeout_seconds=20,
            http_fetcher=fetcher,
        )
    )

    deduplication = (
        OracleAcquisitionDeduplicationLedger(
            policy_id="oracle.dedup.content_hash.v1",
            entry_metadata={
                "shadow_mode": True,
                "source": "kalshi",
            },
        )
    )

    runtime = OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(
            adapter,
        ),
        deduplication_hook=deduplication,
        canonical_observation_router=(
            postgresql["router"]
        ),
    )

    orchestrator = (
        OraclePostgreSQLShadowAcquisitionCycleOrchestrator(
            acquisition_runtime=runtime,
            postgresql_router=postgresql["router"],
            shadow_adapter=adapter,
            bootstrap_record=postgresql["bootstrap"],
        )
    )

    return {
        **postgresql,
        "fetcher": fetcher,
        "adapter": adapter,
        "deduplication": deduplication,
        "runtime": runtime,
        "orchestrator": orchestrator,
    }


def run_successful_shadow_cycle_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    assert decision.acquisition_allowed is True

    cycle = system["orchestrator"].run_cycle(
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "mode": "shadow",
            "source": "kalshi",
        },
        audit_metadata={
            "request_id": "audit-ola017-cycle",
        },
    )

    assert cycle.schema_version == "OLA-017"
    assert cycle.engine_id == "OLA-017"

    assert cycle.cycle_id.startswith(
        "postgresql_shadow_cycle."
    )

    assert cycle.cycle_status == "completed"

    assert cycle.adapter_id == (
        "adapter.oracle.kalshi.public_markets.shadow"
    )

    assert cycle.source_id == (
        "source.kalshi.market_data"
    )

    assert cycle.backend_id == (
        "backend.oracle.postgresql.canonical"
    )

    assert cycle.bootstrap_live_write_ready is True

    assert cycle.source_control_acquisition_allowed is True

    assert cycle.shadow_mode is True
    assert cycle.alerts_allowed is False
    assert cycle.qseries_intake_allowed is False

    assert cycle.acquisition_invoked is True

    assert cycle.acquisition_batch_id is not None
    assert cycle.acquisition_batch_hash is not None

    assert cycle.observation_count == 2
    assert cycle.canonical_count == 2
    assert cycle.duplicate_count == 0
    assert cycle.routed_count == 2

    assert cycle.postgresql_routing_record_delta == 2

    assert cycle.first_persistence_sequence_number == 1
    assert cycle.last_persistence_sequence_number == 2

    assert (
        cycle.prior_terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )

    assert cycle.terminal_chain_advanced is True

    assert cycle.persistence_reconciled is True

    assert len(system["state"].observations) == 2

    assert system["state"].sequence_number == 2

    assert system["router"].routing_record_count == 2

    assert system["deduplication"].entry_count == 2

    assert (
        system["backend"].terminal_chain_hash()
        == cycle.terminal_chain_hash
    )

    first_row = system["state"].observations[0]

    second_row = system["state"].observations[1]

    assert (
        first_row["previous_chain_hash"]
        == GENESIS_CHAIN_HASH
    )

    assert (
        second_row["previous_chain_hash"]
        == first_row["chain_hash"]
    )

    assert (
        second_row["chain_hash"]
        == cycle.terminal_chain_hash
    )

    acquisition_evidence = (
        system["adapter"].last_acquisition_evidence
    )

    assert acquisition_evidence is not None

    assert (
        acquisition_evidence.canonical_replay_hash_created
        is False
    )

    assert len(
        acquisition_evidence.raw_observation_hashes
    ) == 2

    for row in system["state"].observations:
        assert row["observation_replay_hash"]

    assert cycle.immutable is True
    assert cycle.replayable is True
    assert cycle.auditable is True
    assert cycle.explainable is True

    assert cycle.read_only is True
    assert cycle.execution_allowed is False
    assert cycle.execution_adapter_resolved is False
    assert cycle.execution_adapter_invoked is False
    assert cycle.trade_authorization_allowed is False
    assert cycle.order_placement_allowed is False
    assert cycle.funds_moved is False
    assert cycle.portfolio_mutated is False

    try:
        cycle.shadow_mode = False

        raise AssertionError(
            "shadow cycle record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return system, cycle


def run_blocked_cycle_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=False
    )

    assert decision.acquisition_allowed is False

    cycle = system["orchestrator"].run_cycle(
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "mode": "shadow",
            "source": "kalshi",
            "blocked_test": True,
        },
        audit_metadata={
            "request_id": "audit-ola017-blocked",
        },
    )

    assert cycle.cycle_status == "blocked"

    assert cycle.acquisition_invoked is False

    assert cycle.observation_count == 0
    assert cycle.canonical_count == 0
    assert cycle.duplicate_count == 0
    assert cycle.routed_count == 0

    assert cycle.postgresql_routing_record_delta == 0

    assert cycle.first_persistence_sequence_number is None

    assert cycle.last_persistence_sequence_number is None

    assert cycle.terminal_chain_advanced is False

    assert cycle.persistence_reconciled is True

    assert len(system["fetcher"].calls) == 0

    assert len(system["state"].observations) == 0

    assert system["router"].routing_record_count == 0

    assert system["deduplication"].entry_count == 0

    assert (
        system["backend"].terminal_chain_hash()
        == GENESIS_CHAIN_HASH
    )

    return system, cycle


def run_deterministic_replay_test():
    first_system = build_system()

    second_system = build_system()

    first_decision = build_source_control_decision(
        healthy=True
    )

    second_decision = build_source_control_decision(
        healthy=True
    )

    first = first_system["orchestrator"].run_cycle(
        source_control_decision=first_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "mode": "shadow",
            "source": "kalshi",
            "deterministic": True,
        },
        audit_metadata={
            "request_id": "audit-ola017-replay",
        },
    )

    second = second_system["orchestrator"].run_cycle(
        source_control_decision=second_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "mode": "shadow",
            "source": "kalshi",
            "deterministic": True,
        },
        audit_metadata={
            "request_id": "audit-ola017-replay",
        },
    )

    assert first == second

    assert first.cycle_hash == second.cycle_hash

    assert (
        first_system["router"].routing_records
        == second_system["router"].routing_records
    )

    assert (
        first_system["state"].observations
        == second_system["state"].observations
    )

    assert (
        first_system["backend"].terminal_chain_hash()
        == second_system["backend"].terminal_chain_hash()
    )

    return first


def run_timestamp_fail_closed_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    try:
        system["orchestrator"].run_cycle(
            source_control_decision=decision,
            cycle_started_at=datetime(
                2026,
                7,
                12,
                9,
                1,
                0,
            ),
            cycle_completed_at=CYCLE_COMPLETED_AT,
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "naive cycle_started_at must fail closed"
        )

    except ValueError:
        pass

    assert len(system["fetcher"].calls) == 0

    assert len(system["state"].observations) == 0


def run_secret_metadata_fail_closed_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    try:
        system["orchestrator"].run_cycle(
            source_control_decision=decision,
            cycle_started_at=CYCLE_STARTED_AT,
            cycle_completed_at=CYCLE_COMPLETED_AT,
            replay_metadata={
                "password": SECRET_VALUE,
            },
            audit_metadata={},
        )

        raise AssertionError(
            "secret-bearing cycle metadata must fail closed"
        )

    except ValueError:
        pass

    assert len(system["fetcher"].calls) == 0

    assert len(system["state"].observations) == 0


def main():
    successful_system, successful_cycle = (
        run_successful_shadow_cycle_test()
    )

    blocked_system, blocked_cycle = (
        run_blocked_cycle_test()
    )

    replay_cycle = run_deterministic_replay_test()

    run_timestamp_fail_closed_test()

    run_secret_metadata_fail_closed_test()

    result = {
        "schema_version": successful_cycle.schema_version,
        "engine_id": successful_cycle.engine_id,
        "status": "passed",
        "successful_cycle_status": (
            successful_cycle.cycle_status
        ),
        "blocked_cycle_status": (
            blocked_cycle.cycle_status
        ),
        "adapter_id": successful_cycle.adapter_id,
        "source_id": successful_cycle.source_id,
        "backend_id": successful_cycle.backend_id,
        "bootstrap_live_write_ready": (
            successful_cycle.bootstrap_live_write_ready
        ),
        "source_control_allowed_cycle_invoked": (
            successful_cycle.acquisition_invoked
        ),
        "source_control_blocked_cycle_invoked": (
            blocked_cycle.acquisition_invoked
        ),
        "observation_count": (
            successful_cycle.observation_count
        ),
        "canonical_count": (
            successful_cycle.canonical_count
        ),
        "duplicate_count": (
            successful_cycle.duplicate_count
        ),
        "routed_count": (
            successful_cycle.routed_count
        ),
        "postgresql_routing_record_delta": (
            successful_cycle
            .postgresql_routing_record_delta
        ),
        "first_persistence_sequence_number": (
            successful_cycle
            .first_persistence_sequence_number
        ),
        "last_persistence_sequence_number": (
            successful_cycle
            .last_persistence_sequence_number
        ),
        "postgresql_persistence_count": len(
            successful_system["state"].observations
        ),
        "deduplication_reconciled": (
            successful_cycle.canonical_count
            + successful_cycle.duplicate_count
            == successful_cycle.observation_count
        ),
        "routing_reconciled": (
            successful_cycle.routed_count
            == successful_cycle.canonical_count
        ),
        "persistence_reconciled": (
            successful_cycle.persistence_reconciled
        ),
        "postgresql_chain_advanced": (
            successful_cycle.terminal_chain_advanced
        ),
        "canonical_replay_hash_owned_by_ola_001": True,
        "raw_observation_hash_owned_by_ola_016": True,
        "deterministic_replay_valid": (
            replay_cycle.cycle_status == "completed"
        ),
        "shadow_mode": successful_cycle.shadow_mode,
        "alerts_allowed": successful_cycle.alerts_allowed,
        "qseries_intake_allowed": (
            successful_cycle.qseries_intake_allowed
        ),
        "read_only": successful_cycle.read_only,
        "execution_allowed": (
            successful_cycle.execution_allowed
        ),
        "execution_adapter_resolved": (
            successful_cycle.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            successful_cycle.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            successful_cycle.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            successful_cycle.order_placement_allowed
        ),
        "funds_moved": successful_cycle.funds_moved,
        "portfolio_mutated": (
            successful_cycle.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-017 Oracle PostgreSQL Shadow "
        "Acquisition Cycle Orchestrator"
    )

    print(result)


if __name__ == "__main__":
    main()
