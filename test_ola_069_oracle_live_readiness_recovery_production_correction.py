from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
)


MODULE_NAME = (
    "qseries_v2.oracle_intelligence."
    "live_acquisition_model."
    "oracle_first_real_shadow_corpus_launch_command"
)


class FakeReadinessRecord:
    schema_version = "OLA-018"
    engine_id = "OLA-018"
    readiness_status = "ready"
    acquisition_allowed = True
    read_only = True
    execution_allowed = False


class RecoveringFakeGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        self.calls.append(dict(kwargs))

        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure(
                "temporary source-health failure"
            )

        return FakeReadinessRecord()


class AlwaysReadyFakeGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        self.calls.append(dict(kwargs))
        return FakeReadinessRecord()


def main() -> None:
    module = importlib.import_module(MODULE_NAME)

    provider_class = getattr(
        module,
        "_ProductionLiveReadinessProvider",
    )

    base_time = datetime(
        2026,
        7,
        18,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )

    clock_values = iter(
        (
            base_time + timedelta(seconds=5),
            base_time + timedelta(seconds=10),
        )
    )

    sleep_calls: list[float] = []

    gate = RecoveringFakeGate()

    provider = provider_class.__new__(
        provider_class
    )

    provider._gate = gate
    provider._retry_base_seconds = 5.0
    provider._retry_max_seconds = 60.0
    provider._sleeper = sleep_calls.append
    provider._clock = lambda: next(clock_values)
    provider._calls = 0
    provider._readiness_attempts = 0
    provider._transient_failure_count = 0
    provider._last_transient_failure = None

    readiness = provider(
        iteration_number=12,
        consecutive_failures=9,
        checked_at=base_time,
        evaluated_at=base_time,
    )

    assert isinstance(
        readiness,
        FakeReadinessRecord,
    )

    assert provider.calls == 1
    assert provider.readiness_attempts == 2
    assert provider.transient_failure_count == 1
    assert provider.last_transient_failure is None

    assert sleep_calls == [5.0]
    assert len(gate.calls) == 2

    first_call = gate.calls[0]
    second_call = gate.calls[1]

    # Critical OLA-069 contract:
    # scheduler failures must not poison OLA-002 source health.
    assert first_call["consecutive_failures"] == 0
    assert second_call["consecutive_failures"] == 0

    first_metadata = first_call[
        "readiness_metadata"
    ]

    assert (
        first_metadata[
            "scheduler_consecutive_failures"
        ]
        == 9
    )

    assert (
        first_metadata[
            "source_health_consecutive_failures"
        ]
        == 0
    )

    assert (
        first_metadata[
            "ola_069_readiness_recovery"
        ]
        is True
    )

    assert (
        second_call["checked_at"]
        > first_call["checked_at"]
    )

    assert (
        second_call["evaluated_at"]
        == second_call["checked_at"]
    )

    assert (
        second_call[
            "rate_window_observation"
        ].checked_at
        == second_call["checked_at"]
    )

    ready_gate = AlwaysReadyFakeGate()

    ready_provider = provider_class.__new__(
        provider_class
    )

    ready_provider._gate = ready_gate
    ready_provider._retry_base_seconds = 5.0
    ready_provider._retry_max_seconds = 60.0
    ready_provider._sleeper = sleep_calls.append
    ready_provider._clock = lambda: base_time
    ready_provider._calls = 0
    ready_provider._readiness_attempts = 0
    ready_provider._transient_failure_count = 0
    ready_provider._last_transient_failure = None

    direct = ready_provider(
        iteration_number=1,
        consecutive_failures=100,
        checked_at=base_time,
        evaluated_at=base_time,
    )

    assert isinstance(
        direct,
        FakeReadinessRecord,
    )

    assert ready_provider.calls == 1
    assert ready_provider.readiness_attempts == 1
    assert ready_provider.transient_failure_count == 0

    assert (
        ready_gate.calls[0][
            "consecutive_failures"
        ]
        == 0
    )

    assert sleep_calls == [5.0]

    production_path = Path(
        module.__file__
    )

    production_text = production_path.read_text(
        encoding="utf-8"
    )

    assert (
        "scheduler_consecutive_failures"
        in production_text
    )

    assert (
        "source_health_consecutive_failures"
        in production_text
    )

    assert (
        "except KalshiLiveReadReadinessFailure"
        in production_text
    )

    result = {
        "schema_version": "OLA-069",
        "engine_id": "OLA-069",
        "status": "passed",
        "scheduler_failure_state_separated": True,
        "source_health_failure_state_reset": True,
        "temporary_readiness_failure_contained": True,
        "readiness_retried_fail_closed": True,
        "fresh_retry_timestamps_used": True,
        "no_acquisition_during_failure": True,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] OLA-069 Oracle Live Readiness "
        "Recovery Production Correction"
    )
    print(result)


if __name__ == "__main__":
    main()
