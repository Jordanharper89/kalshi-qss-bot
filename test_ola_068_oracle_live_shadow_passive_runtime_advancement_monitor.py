from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_passive_runtime_advancement_monitor import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OraclePassiveRuntimeAdvancementRecord,
    OraclePassiveRuntimeSnapshot,
    PassiveRuntimeConfigurationError,
    PassiveRuntimeInvariantError,
    compare_passive_runtime_snapshots,
    monitor_existing_runtime,
)


PASS_MARKER = (
    "[PASS] OLA-068 Oracle Live Shadow "
    "Passive Runtime Advancement Monitor"
)


def _normalize(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _normalize(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return [
            _normalize(item)
            for item in value
        ]

    if isinstance(
        value,
        datetime,
    ):
        return value.astimezone(
            timezone.utc
        ).isoformat()

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return str(value)


def _canonical_hash(
    payload: Mapping[str, Any],
) -> str:
    normalized = _normalize(
        payload
    )

    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


def _snapshot(
    *,
    captured_at: datetime,
    observation_count: int,
    latest_sequence_number: int,
    persistence_terminal_sequence: int,
    latest_persisted_at: datetime,
    log_path: str,
    log_modified_at: datetime,
    log_sha256: str,
    state_modified_at: datetime,
    state_sha256: str,
) -> OraclePassiveRuntimeSnapshot:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "captured_at": (
            captured_at.isoformat()
        ),
        "observation_count": (
            observation_count
        ),
        "latest_sequence_number": (
            latest_sequence_number
        ),
        "latest_persisted_at": (
            latest_persisted_at.isoformat()
        ),
        "persistence_terminal_sequence": (
            persistence_terminal_sequence
        ),
        "newest_runtime_log_path": (
            log_path
        ),
        "newest_runtime_log_modified_at": (
            log_modified_at.isoformat()
        ),
        "newest_runtime_log_size_bytes": (
            5638
        ),
        "newest_runtime_log_sha256": (
            log_sha256
        ),
        "active_state_path": (
            "runtime/oracle_live_shadow/"
            "state/current.json"
        ),
        "active_state_modified_at": (
            state_modified_at.isoformat()
        ),
        "active_state_size_bytes": (
            1190
        ),
        "active_state_sha256": (
            state_sha256
        ),
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    return OraclePassiveRuntimeSnapshot(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        captured_at=captured_at,
        observation_count=(
            observation_count
        ),
        latest_sequence_number=(
            latest_sequence_number
        ),
        latest_persisted_at=(
            latest_persisted_at
        ),
        persistence_terminal_sequence=(
            persistence_terminal_sequence
        ),
        newest_runtime_log_path=(
            log_path
        ),
        newest_runtime_log_modified_at=(
            log_modified_at
        ),
        newest_runtime_log_size_bytes=(
            5638
        ),
        newest_runtime_log_sha256=(
            log_sha256
        ),
        active_state_path=(
            "runtime/oracle_live_shadow/"
            "state/current.json"
        ),
        active_state_modified_at=(
            state_modified_at
        ),
        active_state_size_bytes=(
            1190
        ),
        active_state_sha256=(
            state_sha256
        ),
        read_only=True,
        execution_allowed=False,
        alerts_allowed=False,
        qseries_handoff_allowed=False,
        trade_authorization_allowed=False,
        order_placement_allowed=False,
        funds_moved=False,
        portfolio_mutated=False,
        snapshot_hash=_canonical_hash(
            payload
        ),
    )


def _assert_safety_contract(
    record: OraclePassiveRuntimeAdvancementRecord,
) -> None:
    assert (
        record.existing_runtime_observed_only
        is True
    )

    assert (
        record.acquisition_cycle_invoked
        is False
    )

    assert (
        record.scheduler_invoked
        is False
    )

    assert (
        record.runner_invoked
        is False
    )

    assert record.read_only is True

    assert (
        record.execution_allowed
        is False
    )

    assert (
        record.alerts_allowed
        is False
    )

    assert (
        record.qseries_handoff_allowed
        is False
    )

    assert (
        record.trade_authorization_allowed
        is False
    )

    assert (
        record.order_placement_allowed
        is False
    )

    assert record.funds_moved is False

    assert (
        record.portfolio_mutated
        is False
    )


def main() -> None:
    print(
        "========================================"
    )
    print(
        " OLA-068 FULL REPLACEMENT TEST"
    )
    print(
        " CURRENT REPOSITORY CONTRACT"
    )
    print(
        " POSTGRESQL CANONICAL ADVANCEMENT"
    )
    print(
        "========================================"
    )

    base_time = datetime(
        2026,
        7,
        19,
        15,
        59,
        21,
        tzinfo=timezone.utc,
    )

    mapping_payload = MappingProxyType(
        {
            "alpha": 1,
            "beta": {
                "gamma": 2,
            },
        }
    )

    regular_payload = {
        "alpha": 1,
        "beta": {
            "gamma": 2,
        },
    }

    assert (
        _canonical_hash(
            mapping_payload
        )
        == _canonical_hash(
            regular_payload
        )
    )

    before = _snapshot(
        captured_at=base_time,
        observation_count=18974,
        latest_sequence_number=18974,
        persistence_terminal_sequence=18974,
        latest_persisted_at=base_time,
        log_path=(
            "runtime/oracle_live_shadow/"
            "logs/historical-log.json"
        ),
        log_modified_at=base_time,
        log_sha256="a" * 64,
        state_modified_at=base_time,
        state_sha256="b" * 64,
    )

    full_after = _snapshot(
        captured_at=(
            base_time
            + timedelta(seconds=30)
        ),
        observation_count=18999,
        latest_sequence_number=18999,
        persistence_terminal_sequence=18999,
        latest_persisted_at=(
            base_time
            + timedelta(seconds=29)
        ),
        log_path=(
            "runtime/oracle_live_shadow/"
            "logs/new-log.json"
        ),
        log_modified_at=(
            base_time
            + timedelta(seconds=30)
        ),
        log_sha256="c" * 64,
        state_modified_at=(
            base_time
            + timedelta(seconds=30)
        ),
        state_sha256="d" * 64,
    )

    full_record = (
        compare_passive_runtime_snapshots(
            before=before,
            after=full_after,
            observation_window_seconds=30.0,
            evaluated_at=(
                base_time
                + timedelta(seconds=31)
            ),
        )
    )

    assert isinstance(
        full_record,
        OraclePassiveRuntimeAdvancementRecord,
    )

    assert full_record.status == "advancing"

    assert (
        full_record.observation_count_delta
        == 25
    )

    assert (
        full_record.latest_sequence_delta
        == 25
    )

    assert (
        full_record
        .persistence_terminal_sequence_delta
        == 25
    )

    assert (
        full_record.latest_persisted_at_advanced
        is True
    )

    assert (
        full_record.runtime_log_advanced
        is True
    )

    assert (
        full_record.active_state_advanced
        is True
    )

    assert (
        full_record.postgresql_persistence_advanced
        is True
    )

    assert (
        full_record.runtime_advancing
        is True
    )

    _assert_safety_contract(
        full_record
    )

    print(
        "[PASS] PostgreSQL and filesystem "
        "advancement accepted"
    )

    database_only_after = _snapshot(
        captured_at=(
            base_time
            + timedelta(seconds=30)
        ),
        observation_count=18999,
        latest_sequence_number=18999,
        persistence_terminal_sequence=18999,
        latest_persisted_at=(
            base_time
            + timedelta(seconds=29)
        ),
        log_path=(
            "runtime/oracle_live_shadow/"
            "logs/historical-log.json"
        ),
        log_modified_at=base_time,
        log_sha256="a" * 64,
        state_modified_at=base_time,
        state_sha256="b" * 64,
    )

    database_only_record = (
        compare_passive_runtime_snapshots(
            before=before,
            after=database_only_after,
            observation_window_seconds=30.0,
            evaluated_at=(
                base_time
                + timedelta(seconds=31)
            ),
        )
    )

    assert (
        database_only_record.status
        == "advancing"
    )

    assert (
        database_only_record
        .observation_count_delta
        == 25
    )

    assert (
        database_only_record
        .latest_sequence_delta
        == 25
    )

    assert (
        database_only_record
        .persistence_terminal_sequence_delta
        == 25
    )

    assert (
        database_only_record
        .latest_persisted_at_advanced
        is True
    )

    assert (
        database_only_record
        .runtime_log_advanced
        is False
    )

    assert (
        database_only_record
        .active_state_advanced
        is False
    )

    assert (
        database_only_record
        .postgresql_persistence_advanced
        is True
    )

    assert (
        database_only_record
        .runtime_advancing
        is True
    )

    _assert_safety_contract(
        database_only_record
    )

    print(
        "[PASS] PostgreSQL-only advancement accepted"
    )
    print(
        "[PASS] Unchanged runtime log accepted"
    )
    print(
        "[PASS] Unchanged active state accepted"
    )

    repeated = (
        compare_passive_runtime_snapshots(
            before=before,
            after=database_only_after,
            observation_window_seconds=30.0,
            evaluated_at=(
                base_time
                + timedelta(seconds=31)
            ),
        )
    )

    assert (
        repeated.evidence_hash
        == database_only_record.evidence_hash
    )

    assert (
        dict(
            repeated.to_payload()
        )
        == dict(
            database_only_record.to_payload()
        )
    )

    print(
        "[PASS] Deterministic evidence preserved"
    )

    unchanged = (
        compare_passive_runtime_snapshots(
            before=before,
            after=before,
            observation_window_seconds=30.0,
            evaluated_at=(
                base_time
                + timedelta(seconds=31)
            ),
        )
    )

    assert (
        unchanged.status
        == "not_advancing"
    )

    assert (
        unchanged.runtime_advancing
        is False
    )

    assert (
        unchanged.postgresql_persistence_advanced
        is False
    )

    _assert_safety_contract(
        unchanged
    )

    print(
        "[PASS] Inactive runtime fails closed"
    )

    sleep_calls: list[float] = []

    snapshots = iter(
        (
            before,
            database_only_after,
        )
    )

    def probe() -> OraclePassiveRuntimeSnapshot:
        return next(
            snapshots
        )

    def sleeper(
        seconds: float,
    ) -> None:
        sleep_calls.append(
            seconds
        )

    monitored = monitor_existing_runtime(
        snapshot_probe=probe,
        observation_window_seconds=30.0,
        sleeper=sleeper,
        evaluated_at_factory=lambda: (
            base_time
            + timedelta(seconds=31)
        ),
    )

    assert (
        monitored.runtime_advancing
        is True
    )

    assert sleep_calls == [
        30.0
    ]

    _assert_safety_contract(
        monitored
    )

    print(
        "[PASS] Passive monitor accepts "
        "PostgreSQL-only advancement"
    )

    try:
        monitor_existing_runtime(
            snapshot_probe=lambda: before,
            observation_window_seconds=-1.0,
            sleeper=sleeper,
        )
    except PassiveRuntimeConfigurationError:
        pass
    else:
        raise AssertionError(
            "Negative observation window "
            "did not fail."
        )

    print(
        "[PASS] Invalid observation window "
        "fails closed"
    )

    try:
        OraclePassiveRuntimeAdvancementRecord(
            schema_version=(
                database_only_record.schema_version
            ),
            engine_id=(
                database_only_record.engine_id
            ),
            status=(
                database_only_record.status
            ),
            evaluated_at=(
                database_only_record.evaluated_at
            ),
            observation_window_seconds=(
                database_only_record
                .observation_window_seconds
            ),
            before_snapshot_hash=(
                database_only_record
                .before_snapshot_hash
            ),
            after_snapshot_hash=(
                database_only_record
                .after_snapshot_hash
            ),
            observation_count_delta=(
                database_only_record
                .observation_count_delta
            ),
            latest_sequence_delta=(
                database_only_record
                .latest_sequence_delta
            ),
            persistence_terminal_sequence_delta=(
                database_only_record
                .persistence_terminal_sequence_delta
            ),
            latest_persisted_at_advanced=(
                database_only_record
                .latest_persisted_at_advanced
            ),
            runtime_log_advanced=(
                database_only_record
                .runtime_log_advanced
            ),
            active_state_advanced=(
                database_only_record
                .active_state_advanced
            ),
            postgresql_persistence_advanced=(
                database_only_record
                .postgresql_persistence_advanced
            ),
            runtime_advancing=(
                database_only_record
                .runtime_advancing
            ),
            existing_runtime_observed_only=(
                database_only_record
                .existing_runtime_observed_only
            ),
            acquisition_cycle_invoked=(
                database_only_record
                .acquisition_cycle_invoked
            ),
            scheduler_invoked=(
                database_only_record
                .scheduler_invoked
            ),
            runner_invoked=(
                database_only_record
                .runner_invoked
            ),
            read_only=(
                database_only_record.read_only
            ),
            execution_allowed=(
                database_only_record
                .execution_allowed
            ),
            alerts_allowed=(
                database_only_record
                .alerts_allowed
            ),
            qseries_handoff_allowed=(
                database_only_record
                .qseries_handoff_allowed
            ),
            trade_authorization_allowed=(
                database_only_record
                .trade_authorization_allowed
            ),
            order_placement_allowed=(
                database_only_record
                .order_placement_allowed
            ),
            funds_moved=(
                database_only_record.funds_moved
            ),
            portfolio_mutated=(
                database_only_record
                .portfolio_mutated
            ),
            evidence_hash="0" * 64,
        )
    except PassiveRuntimeInvariantError:
        pass
    else:
        raise AssertionError(
            "Tampered evidence hash "
            "did not fail."
        )

    print(
        "[PASS] Tampered evidence fails closed"
    )

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "mapping_proxy_hash_canonicalized": True,
        "postgresql_is_canonical_advancement": True,
        "filesystem_evidence_is_supporting_only": True,
        "postgresql_only_advancement_detected": True,
        "runtime_log_advancement_detected": True,
        "active_state_advancement_detected": True,
        "inactive_runtime_fails_closed": True,
        "passive_monitor_verified": True,
        "deterministic_evidence_hash": True,
        "tampering_fails_closed": True,
        "existing_runtime_observed_only": True,
        "no_acquisition_cycle_invoked": True,
        "no_scheduler_invoked": True,
        "no_runner_invoked": True,
        "read_only": True,
        "execution_allowed": False,
    }

    print(
        PASS_MARKER
    )

    print(
        result
    )


if __name__ == "__main__":
    main()
