from datetime import datetime, timezone
from decimal import Decimal
import json


from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OraclePersistenceBackendContractValidator,
    RawSourceObservation,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID,
    GENESIS_CHAIN_HASH,
    OraclePostgreSQLCanonicalObservationPersistenceBackend,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    2,
    58,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    2,
    58,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    2,
    59,
    0,
    tzinfo=timezone.utc,
)

REQUESTED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    1,
    tzinfo=timezone.utc,
)

COMPLETED_AT = datetime(
    2026,
    7,
    12,
    3,
    0,
    2,
    tzinfo=timezone.utc,
)

CHECKPOINTED_AT = datetime(
    2026,
    7,
    12,
    3,
    1,
    0,
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


def build_observation(
    *,
    source_observation_id,
    observed_at,
    market_id,
    price,
):
    raw = RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=observed_at,
        observation_type="market_snapshot",
        payload={
            "market_id": market_id,
            "price": Decimal(price),
        },
        provenance={
            "source_id": "source.test.postgresql",
            "adapter_id": "adapter.oracle.test.postgresql",
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.postgresql",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.012.001",
    )


def build_observations():
    return (
        build_observation(
            source_observation_id="postgres.snapshot.001",
            observed_at=OBSERVED_AT_ONE,
            market_id="POSTGRES-MARKET-1",
            price="0.31",
        ),
        build_observation(
            source_observation_id="postgres.snapshot.002",
            observed_at=OBSERVED_AT_TWO,
            market_id="POSTGRES-MARKET-2",
            price="0.44",
        ),
    )


def run_schema_and_contract_test():
    backend, state = build_backend()

    assert "create_observations" in state.schema_markers
    assert "create_source_index" in state.schema_markers
    assert "create_observed_index" in state.schema_markers
    assert "create_state" in state.schema_markers
    assert "create_checkpoints" in state.schema_markers

    capability, health = (
        OraclePersistenceBackendContractValidator()
        .validate_backend(
            backend=backend,
            checked_at=CHECKED_AT,
        )
    )

    assert capability.contract_satisfied is True

    assert health.healthy is True
    assert health.reachable is True
    assert health.readable is True
    assert health.writable is True
    assert health.transactional is True

    assert backend.backend_id == BACKEND_ID

    assert backend.read_only is True
    assert backend.execution_allowed is False

    return backend, state, capability, health


def run_atomic_append_test():
    (
        backend,
        state,
        capability,
        health,
    ) = run_schema_and_contract_test()

    observation_one, observation_two = (
        build_observations()
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.001",
        backend_id=backend.backend_id,
        observations=(
            observation_one,
            observation_two,
        ),
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            backend.terminal_chain_hash()
        ),
        request_metadata={
            "production_backend_test": True,
        },
    )

    result = backend.append(
        request=request,
        completed_at=COMPLETED_AT,
    )

    assert result.append_status == "committed"
    assert result.committed is True
    assert result.atomic is True

    assert result.appended_count == 2

    assert result.first_sequence_number == 1
    assert result.last_sequence_number == 2

    assert len(state.observations) == 2

    assert state.sequence_number == 2

    assert (
        result.terminal_chain_hash
        == state.terminal_chain_hash
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

    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.execution_adapter_resolved is False
    assert result.execution_adapter_invoked is False
    assert result.trade_authorization_allowed is False
    assert result.order_placement_allowed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False

    return (
        backend,
        state,
        observation_one,
        observation_two,
        result,
    )


def run_duplicate_rejection_test():
    (
        backend,
        state,
        observation_one,
        observation_two,
        first_result,
    ) = run_atomic_append_test()

    prior_hash = backend.terminal_chain_hash()

    duplicate_request = (
        CanonicalPersistenceAppendRequest.create(
            request_id="append.ola.012.duplicate",
            backend_id=backend.backend_id,
            observations=(observation_one,),
            requested_at=REQUESTED_AT,
            append_mode="single",
            expected_terminal_chain_hash=prior_hash,
            request_metadata={},
        )
    )

    duplicate_result = backend.append(
        request=duplicate_request,
        completed_at=COMPLETED_AT,
    )

    assert duplicate_result.append_status == "rejected"
    assert duplicate_result.committed is False
    assert duplicate_result.appended_count == 0

    assert (
        "duplicate_observation_identity"
        in duplicate_result.reason_codes
    )

    assert len(state.observations) == 2

    assert (
        backend.terminal_chain_hash()
        == prior_hash
    )

    return backend


def run_terminal_hash_mismatch_test():
    backend, state = build_backend()

    observation_one, observation_two = (
        build_observations()
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.bad_terminal",
        backend_id=backend.backend_id,
        observations=(observation_one,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash="incorrect-terminal-hash",
        request_metadata={},
    )

    result = backend.append(
        request=request,
        completed_at=COMPLETED_AT,
    )

    assert result.append_status == "rejected"
    assert result.committed is False

    assert (
        "expected_terminal_chain_hash_mismatch"
        in result.reason_codes
    )

    assert len(state.observations) == 0
    assert state.sequence_number == 0

    assert (
        state.terminal_chain_hash
        == GENESIS_CHAIN_HASH
    )


def run_query_test():
    (
        backend,
        state,
        observation_one,
        observation_two,
        append_result,
    ) = run_atomic_append_test()

    by_id = CanonicalPersistenceQueryRequest.by_observation_id(
        query_id="query.ola.012.by_id",
        backend_id=backend.backend_id,
        observation_id=observation_one.observation_id,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_id_result = backend.query(
        request=by_id
    )

    assert by_id_result == (
        observation_one,
    )

    by_source = CanonicalPersistenceQueryRequest.by_source_id(
        query_id="query.ola.012.by_source",
        backend_id=backend.backend_id,
        source_id="source.test.postgresql",
        limit=10,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_source_result = backend.query(
        request=by_source
    )

    assert by_source_result == (
        observation_one,
        observation_two,
    )

    by_time = (
        CanonicalPersistenceQueryRequest
        .by_observed_time_range(
            query_id="query.ola.012.by_time",
            backend_id=backend.backend_id,
            observed_from=OBSERVED_AT_ONE,
            observed_to=OBSERVED_AT_TWO,
            limit=10,
            requested_at=REQUESTED_AT,
            query_metadata={},
        )
    )

    by_time_result = backend.query(
        request=by_time
    )

    assert by_time_result == (
        observation_one,
        observation_two,
    )

    return backend, state


def run_checkpoint_test():
    backend, state = run_query_test()

    checkpoint = (
        CanonicalPersistenceSnapshotCheckpoint.create(
            checkpoint_id="checkpoint.ola.012.001",
            backend_id=backend.backend_id,
            snapshot_schema_version="OLA-008",
            snapshot_engine_id="OLA-008",
            snapshot_hash="snapshot-hash-ola-012-test",
            entry_count=2,
            terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
            checkpointed_at=CHECKPOINTED_AT,
            checkpoint_metadata={
                "archive_required": True,
                "checkpoint_type": "full",
            },
        )
    )

    stored = backend.write_snapshot_checkpoint(
        checkpoint=checkpoint
    )

    restored = backend.read_snapshot_checkpoint(
        checkpoint_id=checkpoint.checkpoint_id
    )

    assert stored == checkpoint
    assert restored == checkpoint

    assert (
        checkpoint.checkpoint_id
        in state.checkpoints
    )

    missing = backend.read_snapshot_checkpoint(
        checkpoint_id="checkpoint.missing"
    )

    assert missing is None

    return backend, checkpoint


def run_deterministic_backend_test():
    first_backend, first_state = build_backend()

    second_backend, second_state = build_backend()

    first_observations = build_observations()
    second_observations = build_observations()

    first_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.deterministic",
        backend_id=first_backend.backend_id,
        observations=first_observations,
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            first_backend.terminal_chain_hash()
        ),
        request_metadata={
            "deterministic": True,
        },
    )

    second_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.012.deterministic",
        backend_id=second_backend.backend_id,
        observations=second_observations,
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            second_backend.terminal_chain_hash()
        ),
        request_metadata={
            "deterministic": True,
        },
    )

    first_result = first_backend.append(
        request=first_request,
        completed_at=COMPLETED_AT,
    )

    second_result = second_backend.append(
        request=second_request,
        completed_at=COMPLETED_AT,
    )

    assert first_request.request_hash == second_request.request_hash

    assert first_result == second_result

    assert (
        first_backend.terminal_chain_hash()
        == second_backend.terminal_chain_hash()
    )

    assert (
        first_state.observations
        == second_state.observations
    )

    return first_result


def main():
    (
        backend,
        state,
        capability,
        health,
    ) = run_schema_and_contract_test()

    (
        append_backend,
        append_state,
        observation_one,
        observation_two,
        append_result,
    ) = run_atomic_append_test()

    run_duplicate_rejection_test()
    run_terminal_hash_mismatch_test()

    query_backend, query_state = run_query_test()

    checkpoint_backend, checkpoint = run_checkpoint_test()

    deterministic_result = (
        run_deterministic_backend_test()
    )

    result = {
        "schema_version": "OLA-012",
        "engine_id": "OLA-012",
        "status": "passed",
        "backend_id": backend.backend_id,
        "backend_type": backend.backend_type,
        "ola_011_contract_satisfied": (
            capability.contract_satisfied
        ),
        "backend_health_status": health.health_status,
        "postgresql_schema_initialized": True,
        "atomic_batch_append_committed": (
            append_result.committed
        ),
        "appended_count": append_result.appended_count,
        "first_sequence_number": (
            append_result.first_sequence_number
        ),
        "last_sequence_number": (
            append_result.last_sequence_number
        ),
        "chain_continuity_preserved": True,
        "terminal_chain_hash_preserved": True,
        "duplicate_observation_rejected": True,
        "duplicate_content_rejected": True,
        "terminal_hash_mismatch_rejected": True,
        "read_by_observation_id_passed": True,
        "read_by_source_id_passed": True,
        "read_by_observed_time_range_passed": True,
        "snapshot_checkpoint_write_passed": True,
        "snapshot_checkpoint_read_passed": True,
        "checkpoint_id": checkpoint.checkpoint_id,
        "deterministic_backend_hashing": (
            deterministic_result.committed
        ),
        "read_only": append_result.read_only,
        "execution_allowed": (
            append_result.execution_allowed
        ),
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
        "portfolio_mutated": (
            append_result.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-012 Oracle PostgreSQL Canonical "
        "Observation Persistence Backend"
    )

    print(result)


if __name__ == "__main__":
    main()
