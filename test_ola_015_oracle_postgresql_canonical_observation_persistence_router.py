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
