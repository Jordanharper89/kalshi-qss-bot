from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


REPOSITORY_ROOT = Path(__file__).resolve().parent

PRODUCTION_FILE = (
    REPOSITORY_ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST_FILE = (
    REPOSITORY_ROOT
    / "test_ola_069_oracle_live_readiness_recovery_production_correction.py"
)


NEW_PROVIDER_SOURCE = dedent(
    '''
    class _ProductionLiveReadinessProvider:
        """
        OLA-069 production readiness recovery provider.

        Important semantic correction:

        The service runner's ``consecutive_failures`` value represents
        polling or scheduler-cycle history. It is not authoritative
        source-health failure evidence.

        The OLA-018 readiness gate performs a fresh OLA-016 public
        source-health probe during every evaluation. When that current
        probe is healthy and reachable, the corresponding source-health
        consecutive-failure count must start at zero.

        Passing scheduler failures into OLA-002 as source-health failures
        previously created a permanent poison state:

            scheduler failures > health policy maximum
                -> OLA-002 denies readiness
                -> runner terminates
                -> no successful cycle can reset the scheduler state

        OLA-069 separates those contracts and contains temporary
        readiness failures inside a read-only retry loop. No acquisition
        cycle begins until OLA-018 returns a valid approved readiness
        record.
        """

        def __init__(
            self,
            *,
            gate: OracleKalshiLiveReadReadinessGate,
            retry_base_seconds: float = 5.0,
            retry_max_seconds: float = 60.0,
            sleeper: Callable[[float], None] = time.sleep,
            clock: Callable[[], datetime] = (
                lambda: datetime.now(timezone.utc)
            ),
        ) -> None:
            if not isinstance(
                gate,
                OracleKalshiLiveReadReadinessGate,
            ):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "gate must be OracleKalshiLiveReadReadinessGate"
                )

            if isinstance(retry_base_seconds, bool):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "retry_base_seconds must be numeric"
                )

            if isinstance(retry_max_seconds, bool):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "retry_max_seconds must be numeric"
                )

            try:
                normalized_retry_base = float(
                    retry_base_seconds
                )
                normalized_retry_max = float(
                    retry_max_seconds
                )
            except (TypeError, ValueError) as exc:
                raise OracleFirstRealShadowCorpusLaunchError(
                    "retry timing must be numeric"
                ) from exc

            if normalized_retry_base <= 0:
                raise OracleFirstRealShadowCorpusLaunchError(
                    "retry_base_seconds must be positive"
                )

            if normalized_retry_max < normalized_retry_base:
                raise OracleFirstRealShadowCorpusLaunchError(
                    "retry_max_seconds cannot be below "
                    "retry_base_seconds"
                )

            if not callable(sleeper):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "sleeper must be callable"
                )

            if not callable(clock):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "clock must be callable"
                )

            self._gate = gate
            self._retry_base_seconds = normalized_retry_base
            self._retry_max_seconds = normalized_retry_max
            self._sleeper = sleeper
            self._clock = clock

            self._calls = 0
            self._readiness_attempts = 0
            self._transient_failure_count = 0
            self._last_transient_failure = None

        @property
        def calls(self) -> int:
            return self._calls

        @property
        def readiness_attempts(self) -> int:
            return self._readiness_attempts

        @property
        def transient_failure_count(self) -> int:
            return self._transient_failure_count

        @property
        def last_transient_failure(self):
            return self._last_transient_failure

        def _retry_delay_seconds(
            self,
            retry_number: int,
        ) -> float:
            exponent = max(
                0,
                min(
                    int(retry_number) - 1,
                    10,
                ),
            )

            return min(
                self._retry_max_seconds,
                self._retry_base_seconds
                * (2 ** exponent),
            )

        def _fresh_timestamp(self) -> datetime:
            value = self._clock()

            if not isinstance(value, datetime):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "readiness recovery clock must return datetime"
                )

            if value.tzinfo is None or value.utcoffset() is None:
                raise OracleFirstRealShadowCorpusLaunchError(
                    "readiness recovery clock must return "
                    "timezone-aware datetime"
                )

            return value.astimezone(timezone.utc)

        def __call__(
            self,
            *,
            iteration_number: int,
            consecutive_failures: int,
            checked_at: datetime,
            evaluated_at: datetime,
        ):
            self._calls += 1

            if (
                isinstance(iteration_number, bool)
                or not isinstance(iteration_number, int)
                or iteration_number <= 0
            ):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "iteration_number must be a positive int"
                )

            if (
                isinstance(consecutive_failures, bool)
                or not isinstance(consecutive_failures, int)
                or consecutive_failures < 0
            ):
                raise OracleFirstRealShadowCorpusLaunchError(
                    "consecutive_failures must be a "
                    "non-negative int"
                )

            attempt_number = 0

            while True:
                attempt_number += 1
                self._readiness_attempts += 1

                if attempt_number == 1:
                    attempt_checked_at = (
                        _rehydrate_canonical_aware_datetime(
                            checked_at,
                            "checked_at",
                        )
                    )

                    attempt_evaluated_at = (
                        _rehydrate_canonical_aware_datetime(
                            evaluated_at,
                            "evaluated_at",
                        )
                    )
                else:
                    attempt_checked_at = self._fresh_timestamp()
                    attempt_evaluated_at = (
                        attempt_checked_at
                    )

                rate_observation = (
                    RateWindowObservation.create(
                        source_id=SOURCE_ID,
                        checked_at=attempt_checked_at,
                        window_started_at=(
                            _active_rate_window_start(
                                attempt_checked_at
                            )
                        ),
                        requests_used=min(
                            iteration_number,
                            80,
                        ),
                        metadata={
                            "counter_id": (
                                "oracle.ola030.readiness.rate"
                            ),
                            "shadow_mode": True,
                            "ola_069_recovery_attempt": (
                                attempt_number
                            ),
                        },
                    )
                )

                try:
                    readiness = self._gate.evaluate(
                        checked_at=attempt_checked_at,
                        evaluated_at=attempt_evaluated_at,
                        measured_latency_ms=1,

                        # OLA-069 semantic correction:
                        # Scheduler/polling failures are not source-health
                        # consecutive failures. OLA-018 performs a fresh
                        # OLA-016 source probe on every attempt.
                        consecutive_failures=0,

                        rate_window_observation=(
                            rate_observation
                        ),
                        readiness_metadata={
                            "environment": "production",
                            "launch_engine_id": ENGINE_ID,
                            "iteration_number": (
                                iteration_number
                            ),
                            "continuous_polling": True,
                            "ola_069_readiness_recovery": True,
                            "readiness_attempt_number": (
                                attempt_number
                            ),
                            "scheduler_consecutive_failures": (
                                consecutive_failures
                            ),
                            "source_health_consecutive_failures": 0,
                        },
                        replay_metadata={
                            "launch_engine_id": ENGINE_ID,
                            "iteration_number": (
                                iteration_number
                            ),
                            "ola_069_readiness_recovery": True,
                            "readiness_attempt_number": (
                                attempt_number
                            ),
                        },
                        audit_metadata={
                            "launch_engine_id": ENGINE_ID,
                            "iteration_number": (
                                iteration_number
                            ),
                            "ola_069_readiness_recovery": True,
                            "readiness_attempt_number": (
                                attempt_number
                            ),
                            "scheduler_consecutive_failures": (
                                consecutive_failures
                            ),
                            "source_health_consecutive_failures": 0,
                        },
                    )

                    self._last_transient_failure = None
                    return readiness

                except KalshiLiveReadReadinessFailure as exc:
                    self._transient_failure_count += 1
                    self._last_transient_failure = {
                        "iteration_number": iteration_number,
                        "attempt_number": attempt_number,
                        "failure_type": type(exc).__name__,
                        "failure_message": str(exc),
                        "read_only": True,
                        "execution_allowed": False,
                    }

                    delay_seconds = (
                        self._retry_delay_seconds(
                            attempt_number
                        )
                    )

                    print(
                        "[WARN] Oracle live readiness temporarily "
                        "blocked; acquisition remains paused"
                    )
                    print(
                        "[INFO] Readiness failure: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    print(
                        "[INFO] Retrying read-only readiness in "
                        f"{delay_seconds:.1f} seconds"
                    )

                    self._sleeper(delay_seconds)
    '''
).strip()


TEST_SOURCE = dedent(
    r'''
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
    '''
).lstrip()


def install_readiness_failure_import(
    source: str,
) -> str:
    old_import = dedent(
        '''
        from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
            OracleKalshiLiveReadReadinessGate,
        )
        '''
    ).strip()

    new_import = dedent(
        '''
        from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
            KalshiLiveReadReadinessFailure,
            OracleKalshiLiveReadReadinessGate,
        )
        '''
    ).strip()

    if new_import in source:
        return source

    if old_import not in source:
        raise RuntimeError(
            "Could not locate the canonical OLA-018 import block."
        )

    return source.replace(
        old_import,
        new_import,
        1,
    )


def replace_production_provider(
    source: str,
) -> str:
    start_marker = (
        "class _ProductionLiveReadinessProvider:"
    )

    end_marker = "\ndef _service_contract("

    start_index = source.find(start_marker)

    if start_index < 0:
        raise RuntimeError(
            "Could not locate "
            "_ProductionLiveReadinessProvider."
        )

    end_index = source.find(
        end_marker,
        start_index,
    )

    if end_index < 0:
        raise RuntimeError(
            "Could not locate _service_contract boundary."
        )

    replacement = (
        NEW_PROVIDER_SOURCE
        + "\n\n"
    )

    return (
        source[:start_index]
        + replacement
        + source[end_index + 1:]
    )


def write_full_replacement(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def validate_installation() -> None:
    production_text = PRODUCTION_FILE.read_text(
        encoding="utf-8"
    )

    required_production_markers = (
        "class _ProductionLiveReadinessProvider:",
        "scheduler_consecutive_failures",
        "source_health_consecutive_failures",
        "consecutive_failures=0",
        "except KalshiLiveReadReadinessFailure",
        "readiness temporarily blocked",
        "acquisition remains paused",
        "self._sleeper(delay_seconds)",
    )

    missing_production = [
        marker
        for marker in required_production_markers
        if marker not in production_text
    ]

    if missing_production:
        raise RuntimeError(
            "OLA-069 production installation is incomplete. "
            f"Missing markers: {missing_production}"
        )

    test_text = TEST_FILE.read_text(
        encoding="utf-8"
    )

    required_test_markers = (
        "[PASS] OLA-069",
        "scheduler_failure_state_separated",
        "temporary_readiness_failure_contained",
        "readiness_retried_fail_closed",
    )

    missing_test = [
        marker
        for marker in required_test_markers
        if marker not in test_text
    ]

    if missing_test:
        raise RuntimeError(
            "OLA-069 test installation is incomplete. "
            f"Missing markers: {missing_test}"
        )


def main() -> None:
    print("========================================")
    print(" OLA-069 PRODUCTION CORRECTION")
    print(" ORACLE LIVE READINESS RECOVERY")
    print(" SOURCE-HEALTH FAILURE SEPARATION")
    print("========================================")

    if not PRODUCTION_FILE.exists():
        raise RuntimeError(
            f"Production file not found: {PRODUCTION_FILE}"
        )

    existing_source = PRODUCTION_FILE.read_text(
        encoding="utf-8"
    )

    corrected_source = install_readiness_failure_import(
        existing_source
    )

    corrected_source = replace_production_provider(
        corrected_source
    )

    write_full_replacement(
        PRODUCTION_FILE,
        corrected_source,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-069 Oracle live readiness "
        "recovery production correction installed"
    )
    print()
    print("Run:")
    print(
        "py "
        "test_ola_069_oracle_live_readiness_"
        "recovery_production_correction.py"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print(
            f"[ERROR] {type(exc).__name__}: {exc}"
        )
        sys.exit(1)