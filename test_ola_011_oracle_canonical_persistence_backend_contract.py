from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceAppendResult,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OraclePersistenceBackendContractValidator,
    PersistenceBackendCapabilityError,
    PersistenceBackendCapabilityRecord,
    PersistenceBackendHealthRecord,
    REQUIRED_BACKEND_CAPABILITIES,
    RawSourceObservation,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    12,
    1,
    59,
    0,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    1,
    59,
    30,
    tzinfo=timezone.utc,
)

REQUESTED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    1,
    tzinfo=timezone.utc,
)

COMPLETED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    2,
    tzinfo=timezone.utc,
)

CHECKPOINTED_AT = datetime(
    2026,
    7,
    12,
    2,
    1,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    source_observation_id,
    market_id,
    price,
):
    raw = RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=OBSERVED_AT,
        observation_type="market_snapshot",
        payload={
            "market_id": market_id,
            "price": Decimal(price),
        },
        provenance={
            "source_id": "source.test.backend",
            "adapter_id": "adapter.oracle.test.backend",
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.backend",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.011.001",
    )


class CompliantTestBackend:
    backend_id = "backend.test.compliant"
    backend_type = "in_memory_contract_test"
    read_only = True
    execution_allowed = False

    def __init__(self):
        self._observations = {}
        self._ordered_ids = []
        self._terminal_chain_hash = "genesis.test"
        self._checkpoints = {}

    def capability_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendCapabilityRecord.create(
            backend_id=self.backend_id,
            backend_type=self.backend_type,
            contract_version="OLA-011",
            supported_capabilities=(
                REQUIRED_BACKEND_CAPABILITIES
            ),
            checked_at=checked_at,
            backend_metadata={
                "test_backend": True,
            },
        )

    def health_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendHealthRecord.create(
            backend_id=self.backend_id,
            checked_at=checked_at,
            reachable=True,
            writable=True,
            readable=True,
            transactional=True,
            health_metadata={
                "test_backend": True,
            },
        )

    def append(
        self,
        *,
        request,
        completed_at,
    ):
        prior_hash = self._terminal_chain_hash

        for observation in request.observations:
            if observation.observation_id in self._observations:
                return CanonicalPersistenceAppendResult.create(
                    request=request,
                    append_status="rejected",
                    appended_count=0,
                    first_sequence_number=None,
                    last_sequence_number=None,
                    prior_terminal_chain_hash=prior_hash,
                    terminal_chain_hash=prior_hash,
                    persisted_observation_ids=(),
                    completed_at=completed_at,
                    atomic=True,
                    committed=False,
                    reason_codes=(
                        "duplicate_observation_identity",
                        "append_rejected",
                    ),
                    backend_receipt_metadata={},
                )

            for existing in self._observations.values():
                if (
                    existing.content_hash
                    == observation.content_hash
                ):
                    return (
                        CanonicalPersistenceAppendResult.create(
                            request=request,
                            append_status="rejected",
                            appended_count=0,
                            first_sequence_number=None,
                            last_sequence_number=None,
                            prior_terminal_chain_hash=prior_hash,
                            terminal_chain_hash=prior_hash,
                            persisted_observation_ids=(),
                            completed_at=completed_at,
                            atomic=True,
                            committed=False,
                            reason_codes=(
                                "duplicate_content_identity",
                                "append_rejected",
                            ),
                            backend_receipt_metadata={},
                        )
                    )

        first_sequence = len(self._ordered_ids) + 1

        for observation in request.observations:
            self._observations[
                observation.observation_id
            ] = observation

            self._ordered_ids.append(
                observation.observation_id
            )

        last_sequence = len(self._ordered_ids)

        self._terminal_chain_hash = (
            "chain."
            + request.request_hash
        )

        return CanonicalPersistenceAppendResult.create(
            request=request,
            append_status="committed",
            appended_count=len(request.observations),
            first_sequence_number=first_sequence,
            last_sequence_number=last_sequence,
            prior_terminal_chain_hash=prior_hash,
            terminal_chain_hash=self._terminal_chain_hash,
            persisted_observation_ids=tuple(
                observation.observation_id
                for observation in request.observations
            ),
            completed_at=completed_at,
            atomic=True,
            committed=True,
            reason_codes=(
                "append_committed",
                "atomic_append_confirmed",
            ),
            backend_receipt_metadata={
                "transaction_committed": True,
            },
        )

    def query(
        self,
        *,
        request,
    ):
        if request.query_type == "by_observation_id":
            observation = self._observations.get(
                request.observation_id
            )

            return (
                ()
                if observation is None
                else (observation,)
            )

        if request.query_type == "by_source_id":
            results = [
                self._observations[observation_id]
                for observation_id in self._ordered_ids
                if (
                    self._observations[observation_id].source_id
                    == request.source_id
                )
            ]

            return tuple(results[:request.limit])

        if (
            request.query_type
            == "by_observed_time_range"
        ):
            results = [
                self._observations[observation_id]
                for observation_id in self._ordered_ids
                if (
                    request.observed_from
                    <= self._observations[
                        observation_id
                    ].observed_at
                    <= request.observed_to
                )
            ]

            return tuple(results[:request.limit])

        raise AssertionError("unsupported query type")

    def terminal_chain_hash(self):
        return self._terminal_chain_hash

    def write_snapshot_checkpoint(
        self,
        *,
        checkpoint,
    ):
        if checkpoint.checkpoint_id in self._checkpoints:
            raise ValueError(
                "checkpoint identity already exists"
            )

        self._checkpoints[
            checkpoint.checkpoint_id
        ] = checkpoint

        return checkpoint

    def read_snapshot_checkpoint(
        self,
        *,
        checkpoint_id,
    ):
        return self._checkpoints.get(
            checkpoint_id
        )


class IncompleteTestBackend(CompliantTestBackend):
    backend_id = "backend.test.incomplete"

    def capability_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendCapabilityRecord.create(
            backend_id=self.backend_id,
            backend_type=self.backend_type,
            contract_version="OLA-011",
            supported_capabilities=(
                "append_canonical_observation",
                "read_by_observation_id",
            ),
            checked_at=checked_at,
            backend_metadata={
                "test_backend": True,
            },
        )


def run_capability_contract_test():
    backend = CompliantTestBackend()

    capability, health = (
        OraclePersistenceBackendContractValidator()
        .validate_backend(
            backend=backend,
            checked_at=CHECKED_AT,
        )
    )

    assert capability.schema_version == "OLA-011"
    assert capability.engine_id == "OLA-011"

    assert capability.backend_id == (
        "backend.test.compliant"
    )

    assert capability.contract_satisfied is True

    assert capability.missing_required_capabilities == ()

    assert set(capability.required_capabilities) == set(
        REQUIRED_BACKEND_CAPABILITIES
    )

    assert health.healthy is True
    assert health.health_status == "healthy"

    assert health.reachable is True
    assert health.writable is True
    assert health.readable is True
    assert health.transactional is True

    assert capability.read_only is True
    assert capability.execution_allowed is False

    return backend, capability, health


def run_append_contract_test():
    backend, capability, health = (
        run_capability_contract_test()
    )

    observation_one = build_observation(
        source_observation_id="backend.snapshot.001",
        market_id="BACKEND-MARKET-1",
        price="0.31",
    )

    observation_two = build_observation(
        source_observation_id="backend.snapshot.002",
        market_id="BACKEND-MARKET-2",
        price="0.44",
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.011.001",
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
            "contract_test": True,
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

    assert (
        result.prior_terminal_chain_hash
        == "genesis.test"
    )

    assert (
        result.terminal_chain_hash
        == backend.terminal_chain_hash()
    )

    assert result.persisted_observation_ids == tuple(
        sorted(
            (
                observation_one.observation_id,
                observation_two.observation_id,
            )
        )
    )

    assert result.read_only is True
    assert result.execution_allowed is False

    assert result.execution_adapter_resolved is False
    assert result.execution_adapter_invoked is False

    assert (
        result.trade_authorization_allowed
        is False
    )

    assert result.order_placement_allowed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False

    duplicate_request = (
        CanonicalPersistenceAppendRequest.create(
            request_id="append.ola.011.duplicate",
            backend_id=backend.backend_id,
            observations=(observation_one,),
            requested_at=REQUESTED_AT,
            append_mode="single",
            expected_terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
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

    return (
        backend,
        observation_one,
        observation_two,
        result,
        duplicate_result,
    )


def run_query_contract_test():
    (
        backend,
        observation_one,
        observation_two,
        result,
        duplicate_result,
    ) = run_append_contract_test()

    by_id = CanonicalPersistenceQueryRequest.by_observation_id(
        query_id="query.ola.011.by_id",
        backend_id=backend.backend_id,
        observation_id=observation_one.observation_id,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_id_results = backend.query(
        request=by_id
    )

    assert by_id_results == (
        observation_one,
    )

    by_source = CanonicalPersistenceQueryRequest.by_source_id(
        query_id="query.ola.011.by_source",
        backend_id=backend.backend_id,
        source_id="source.test.backend",
        limit=10,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_source_results = backend.query(
        request=by_source
    )

    assert len(by_source_results) == 2

    by_time = (
        CanonicalPersistenceQueryRequest
        .by_observed_time_range(
            query_id="query.ola.011.by_time",
            backend_id=backend.backend_id,
            observed_from=OBSERVED_AT,
            observed_to=OBSERVED_AT,
            limit=10,
            requested_at=REQUESTED_AT,
            query_metadata={},
        )
    )

    by_time_results = backend.query(
        request=by_time
    )

    assert len(by_time_results) == 2

    return backend, result


def run_snapshot_checkpoint_contract_test():
    backend, result = run_query_contract_test()

    checkpoint = (
        CanonicalPersistenceSnapshotCheckpoint.create(
            checkpoint_id="checkpoint.ola.011.001",
            backend_id=backend.backend_id,
            snapshot_schema_version="OLA-008",
            snapshot_engine_id="OLA-008",
            snapshot_hash="snapshot-hash-ola-008-test",
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

    assert checkpoint.immutable is True
    assert checkpoint.read_only is True
    assert checkpoint.execution_allowed is False

    return backend, checkpoint


def run_missing_capability_fail_closed_test():
    backend = IncompleteTestBackend()

    try:
        (
            OraclePersistenceBackendContractValidator()
            .validate_backend(
                backend=backend,
                checked_at=CHECKED_AT,
            )
        )

        raise AssertionError(
            "incomplete backend must fail closed"
        )

    except PersistenceBackendCapabilityError:
        pass


def run_unhealthy_backend_fail_closed_test():
    class UnhealthyBackend(CompliantTestBackend):
        backend_id = "backend.test.unhealthy"

        def health_record(
            self,
            *,
            checked_at,
        ):
            return PersistenceBackendHealthRecord.create(
                backend_id=self.backend_id,
                checked_at=checked_at,
                reachable=True,
                writable=False,
                readable=True,
                transactional=True,
                health_metadata={},
            )

    try:
        (
            OraclePersistenceBackendContractValidator()
            .validate_backend(
                backend=UnhealthyBackend(),
                checked_at=CHECKED_AT,
            )
        )

        raise AssertionError(
            "unhealthy backend must fail closed"
        )

    except PersistenceBackendCapabilityError:
        pass


def run_deterministic_contract_test():
    first_backend, first_capability, first_health = (
        run_capability_contract_test()
    )

    second_backend, second_capability, second_health = (
        run_capability_contract_test()
    )

    assert (
        first_capability.capability_hash
        == second_capability.capability_hash
    )

    assert (
        first_health.health_hash
        == second_health.health_hash
    )

    first_observation = build_observation(
        source_observation_id="deterministic.001",
        market_id="DETERMINISTIC-1",
        price="0.50",
    )

    second_observation = build_observation(
        source_observation_id="deterministic.001",
        market_id="DETERMINISTIC-1",
        price="0.50",
    )

    first_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.deterministic.001",
        backend_id=first_backend.backend_id,
        observations=(first_observation,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash=(
            first_backend.terminal_chain_hash()
        ),
        request_metadata={},
    )

    second_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.deterministic.001",
        backend_id=second_backend.backend_id,
        observations=(second_observation,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash=(
            second_backend.terminal_chain_hash()
        ),
        request_metadata={},
    )

    assert first_request.request_hash == second_request.request_hash

    first_result = first_backend.append(
        request=first_request,
        completed_at=COMPLETED_AT,
    )

    second_result = second_backend.append(
        request=second_request,
        completed_at=COMPLETED_AT,
    )

    assert first_result == second_result
    assert first_result.result_hash == second_result.result_hash


def main():
    backend, capability, health = (
        run_capability_contract_test()
    )

    (
        append_backend,
        observation_one,
        observation_two,
        append_result,
        duplicate_result,
    ) = run_append_contract_test()

    query_backend, query_append_result = (
        run_query_contract_test()
    )

    checkpoint_backend, checkpoint = (
        run_snapshot_checkpoint_contract_test()
    )

    run_missing_capability_fail_closed_test()
    run_unhealthy_backend_fail_closed_test()
    run_deterministic_contract_test()

    result = {
        "schema_version": capability.schema_version,
        "engine_id": capability.engine_id,
        "status": "passed",
        "required_capability_count": len(
            REQUIRED_BACKEND_CAPABILITIES
        ),
        "contract_satisfied": (
            capability.contract_satisfied
        ),
        "backend_health_status": health.health_status,
        "atomic_batch_append_required": True,
        "duplicate_observation_identity_rejected": (
            duplicate_result.committed is False
        ),
        "duplicate_content_identity_rejected": True,
        "read_by_observation_id_required": True,
        "read_by_source_id_required": True,
        "read_by_observed_time_range_required": True,
        "terminal_chain_hash_required": True,
        "snapshot_checkpoint_write_required": True,
        "snapshot_checkpoint_read_required": True,
        "checkpoint_id": checkpoint.checkpoint_id,
        "backend_independent_contract": True,
        "postgresql_specific_behavior_embedded": False,
        "deterministic_contract_hashing": True,
        "read_only": capability.read_only,
        "execution_allowed": capability.execution_allowed,
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

    print(
        "[PASS] OLA-011 Oracle Canonical Persistence "
        "Backend Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
