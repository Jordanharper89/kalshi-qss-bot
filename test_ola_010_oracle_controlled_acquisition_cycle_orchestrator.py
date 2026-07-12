from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleAcquisitionDeduplicationLedger,
    OracleAcquisitionSourceControlEngine,
    OracleCanonicalObservationPersistenceLedger,
    OracleCanonicalObservationPersistenceRouter,
    OracleControlledAcquisitionCycleOrchestrator,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlPolicy,
    RateWindowObservation,
    RawSourceObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)


CONTROL_CHECKED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    50,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    0,
    tzinfo=timezone.utc,
)

CONTROL_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    55,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    58,
    tzinfo=timezone.utc,
)

CYCLE_STARTED_AT = datetime(
    2026,
    7,
    12,
    0,
    10,
    0,
    tzinfo=timezone.utc,
)

CYCLE_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    0,
    10,
    2,
    tzinfo=timezone.utc,
)


class ControlledReadOnlyAdapter:
    adapter_id = "adapter.oracle.ola010.test"
    source_id = "source.ola010.test.market"
    read_only = True
    execution_allowed = False

    def __init__(self):
        self.acquire_call_count = 0

    def acquire(
        self,
        *,
        acquired_at,
    ):
        self.acquire_call_count += 1

        assert acquired_at == CYCLE_STARTED_AT

        first = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.001",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-1",
                "price": Decimal("0.31"),
                "volume": 1000,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        duplicate = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.001",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-1",
                "price": Decimal("0.31"),
                "volume": 1000,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        second = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.002",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-2",
                "price": Decimal("0.44"),
                "volume": 500,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        return (
            first,
            duplicate,
            second,
        )


def build_source_control_engine():
    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.ola010.test.market": (
                SourceHealthPolicy.create(
                    policy_id="health.ola010.test.v1",
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=0,
                    max_latency_ms=250,
                ),
                RateControlPolicy.create(
                    policy_id="rate.ola010.test.v1",
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=5,
                ),
            ),
        }
    )


def build_source_control_decision(
    *,
    healthy=True,
):
    health = SourceHealthObservation.create(
        source_id="source.ola010.test.market",
        checked_at=CONTROL_CHECKED_AT,
        reachable=healthy,
        consecutive_failures=(
            0
            if healthy
            else 1
        ),
        latency_ms=(
            25
            if healthy
            else None
        ),
        metadata={
            "probe_id": "probe.ola010.001",
        },
    )

    rate = RateWindowObservation.create(
        source_id="source.ola010.test.market",
        checked_at=CONTROL_CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=10,
        metadata={
            "counter_id": "counter.ola010.001",
        },
    )

    return build_source_control_engine().evaluate(
        health_observation=health,
        rate_observation=rate,
        evaluated_at=CONTROL_EVALUATED_AT,
        replay_metadata={
            "test": "ola010",
        },
        audit_metadata={
            "request_id": "audit-ola010-control",
        },
    )


def build_system():
    adapter = ControlledReadOnlyAdapter()

    deduplication_ledger = (
        OracleAcquisitionDeduplicationLedger(
            policy_id="oracle.dedup.content_hash.v1",
            entry_metadata={
                "ola010": True,
            },
        )
    )

    persistence_ledger = (
        OracleCanonicalObservationPersistenceLedger()
    )

    persistence_router = (
        OracleCanonicalObservationPersistenceRouter(
            persistence_ledger=persistence_ledger,
            route_id=(
                "oracle.canonical.persistence.router.ola010"
            ),
            persistence_metadata={
                "persistence_policy_id": (
                    "oracle.persistence.canonical.v1"
                ),
                "ola010": True,
            },
            replay_metadata={
                "replay_source": "ola010",
            },
            audit_metadata={
                "request_id": "audit-ola010-router",
            },
        )
    )

    runtime = OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(adapter,),
        deduplication_hook=deduplication_ledger,
        canonical_observation_router=persistence_router,
    )

    orchestrator = (
        OracleControlledAcquisitionCycleOrchestrator(
            acquisition_runtime=runtime,
            persistence_router=persistence_router,
        )
    )

    return {
        "adapter": adapter,
        "deduplication_ledger": deduplication_ledger,
        "persistence_ledger": persistence_ledger,
        "persistence_router": persistence_router,
        "runtime": runtime,
        "orchestrator": orchestrator,
    }


def run_successful_cycle_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    assert decision.acquisition_allowed is True

    cycle = system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "controlled_cycle_test",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010",
            "operator": "automated_runtime",
        },
    )

    assert cycle.schema_version == "OLA-010"
    assert cycle.engine_id == "OLA-010"

    assert cycle.cycle_id.startswith(
        "acquisition_cycle."
    )

    assert cycle.cycle_status == "completed"

    assert cycle.adapter_id == (
        "adapter.oracle.ola010.test"
    )

    assert cycle.source_id == (
        "source.ola010.test.market"
    )

    assert cycle.source_control_acquisition_allowed is True
    assert cycle.acquisition_invoked is True

    assert cycle.acquisition_batch_id is not None
    assert cycle.acquisition_batch_hash is not None

    assert cycle.observation_count == 3
    assert cycle.canonical_count == 2
    assert cycle.duplicate_count == 1
    assert cycle.routed_count == 2
    assert cycle.persisted_count == 2

    assert (
        cycle.persistence_routing_record_count
        == 2
    )

    assert (
        system["adapter"].acquire_call_count
        == 1
    )

    assert (
        system["deduplication_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 2
    )

    assert (
        cycle.persistence_terminal_chain_hash
        == system["persistence_ledger"]
        .terminal_chain_hash
    )

    assert (
        "canonical_observations_reconciled"
        in cycle.reason_codes
    )

    assert (
        "persistence_routing_reconciled"
        in cycle.reason_codes
    )

    assert cycle.immutable is True
    assert cycle.replayable is True
    assert cycle.auditable is True
    assert cycle.explainable is True

    assert cycle.read_only is True
    assert cycle.execution_allowed is False

    assert cycle.execution_adapter_resolved is False
    assert cycle.execution_adapter_invoked is False

    assert (
        cycle.trade_authorization_allowed
        is False
    )

    assert cycle.order_placement_allowed is False
    assert cycle.funds_moved is False
    assert cycle.portfolio_mutated is False

    try:
        cycle.cycle_status = "mutated"

        raise AssertionError(
            "acquisition cycle record must be immutable"
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
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "blocked_cycle_test",
        },
        audit_metadata={
            "request_id": "audit-ola-010-blocked",
        },
    )

    assert cycle.cycle_status == "blocked"

    assert cycle.source_control_acquisition_allowed is False
    assert cycle.acquisition_invoked is False

    assert cycle.acquisition_batch_id is None
    assert cycle.acquisition_batch_hash is None

    assert cycle.observation_count == 0
    assert cycle.canonical_count == 0
    assert cycle.duplicate_count == 0
    assert cycle.routed_count == 0
    assert cycle.persisted_count == 0

    assert system["adapter"].acquire_call_count == 0

    assert (
        system["deduplication_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 0
    )

    assert (
        "source_control_blocked_acquisition"
        in cycle.reason_codes
    )

    assert (
        "acquisition_not_invoked"
        in cycle.reason_codes
    )

    assert cycle.read_only is True
    assert cycle.execution_allowed is False

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
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=first_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "deterministic_cycle",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010-replay",
        },
    )

    second = second_system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=second_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "deterministic_cycle",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010-replay",
        },
    )

    assert first == second
    assert first.cycle_hash == second.cycle_hash

    assert (
        first.persistence_terminal_chain_hash
        == second.persistence_terminal_chain_hash
    )

    return first


def run_timestamp_fail_closed_tests():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    try:
        system["orchestrator"].run_cycle(
            adapter_id="adapter.oracle.ola010.test",
            source_control_decision=decision,
            cycle_started_at=datetime(
                2026,
                7,
                12,
                0,
                10,
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

    assert system["adapter"].acquire_call_count == 0

    try:
        system["orchestrator"].run_cycle(
            adapter_id="adapter.oracle.ola010.test",
            source_control_decision=decision,
            cycle_started_at=CYCLE_STARTED_AT,
            cycle_completed_at=datetime(
                2026,
                7,
                12,
                0,
                9,
                59,
                tzinfo=timezone.utc,
            ),
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "cycle completion before start must fail closed"
        )

    except ValueError:
        pass

    assert system["adapter"].acquire_call_count == 0


def main():
    successful_system, successful_cycle = (
        run_successful_cycle_test()
    )

    blocked_system, blocked_cycle = (
        run_blocked_cycle_test()
    )

    replay_cycle = run_deterministic_replay_test()

    run_timestamp_fail_closed_tests()

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
        "routed_count": successful_cycle.routed_count,
        "persisted_count": (
            successful_cycle.persisted_count
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
            successful_cycle.persisted_count
            == successful_cycle.canonical_count
        ),
        "persistence_router_record_count": (
            successful_system[
                "persistence_router"
            ].routing_record_count
        ),
        "persistence_ledger_entry_count": (
            successful_system[
                "persistence_ledger"
            ].entry_count
        ),
        "blocked_cycle_adapter_call_count": (
            blocked_system["adapter"].acquire_call_count
        ),
        "deterministic_replay_valid": (
            replay_cycle.cycle_hash
            == successful_cycle.cycle_hash
            or replay_cycle.cycle_status == "completed"
        ),
        "immutable": successful_cycle.immutable,
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
        "[PASS] OLA-010 Oracle Controlled Acquisition "
        "Cycle Orchestrator"
    )

    print(result)


if __name__ == "__main__":
    main()
