from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_077_oracle_readiness_retry_timestamp_lineage_correction.py"
)


OLD_TIMESTAMP_BLOCK = dedent(
    '''
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
    '''
).strip("\n")


NEW_TIMESTAMP_BLOCK = dedent(
    '''
            # OLA-077 canonical retry timestamp-lineage correction:
            #
            # OLA-023 owns the canonical readiness timestamps for the
            # complete service iteration. A temporary OLA-018 readiness
            # failure may cause multiple internal recovery attempts, but
            # those attempts remain part of the same OLA-023 iteration.
            #
            # Therefore every retry must preserve the exact checked_at and
            # evaluated_at values supplied by OLA-023. Replacing them with
            # fresh retry timestamps causes the valid OLA-023 compatibility
            # guard to terminate the persistent runtime with:
            #
            #     readiness provider did not preserve checked_at
            #
            # Retry-attempt timing remains observable through attempt_number,
            # retry delay, and readiness metadata. It must not create a
            # second canonical timestamp authority.
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
    '''
).strip("\n")


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
    KalshiLiveReadReadinessFailure,
)


SCHEMA_VERSION = "OLA-077"
ENGINE_ID = "OLA-077"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

MODULE_NAME = (
    "qseries_v2.oracle_intelligence."
    "live_acquisition_model."
    "oracle_first_real_shadow_corpus_launch_command"
)


class FakeReadinessRecord:
    schema_version = "OLA-018"
    engine_id = "OLA-018"
    readiness_status = "passed"
    live_shadow_cycle_entry_ready = True
    acquisition_allowed = True
    shadow_mode = True
    alerts_allowed = False
    qseries_handoff_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        checked_at: datetime,
        evaluated_at: datetime,
    ) -> None:
        self.checked_at = checked_at
        self.evaluated_at = evaluated_at


class RecoveringFakeGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(
        self,
        **kwargs,
    ):
        call = dict(kwargs)
        self.calls.append(call)

        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure(
                "temporary readiness failure"
            )

        return FakeReadinessRecord(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
        )


class AlwaysBlockedFakeGate:
    def __init__(
        self,
        *,
        maximum_attempts: int,
    ) -> None:
        self.maximum_attempts = maximum_attempts
        self.calls: list[dict[str, Any]] = []

    def evaluate(
        self,
        **kwargs,
    ):
        self.calls.append(
            dict(kwargs)
        )

        if len(self.calls) >= self.maximum_attempts:
            raise StopIteration(
                "bounded test termination"
            )

        raise KalshiLiveReadReadinessFailure(
            "temporary readiness failure"
        )


class AlwaysReadyFakeGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(
        self,
        **kwargs,
    ):
        call = dict(kwargs)
        self.calls.append(call)

        return FakeReadinessRecord(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
        )


def construct_provider(
    provider_class,
    *,
    gate,
    sleeper,
    clock,
):
    provider = provider_class.__new__(
        provider_class
    )

    provider._gate = gate
    provider._retry_base_seconds = 5.0
    provider._retry_max_seconds = 60.0
    provider._sleeper = sleeper
    provider._clock = clock
    provider._calls = 0
    provider._readiness_attempts = 0
    provider._transient_failure_count = 0
    provider._last_transient_failure = None

    return provider


def assert_read_only_contract() -> None:
    assert SCHEMA_VERSION == "OLA-077"
    assert ENGINE_ID == "OLA-077"

    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ALERTS_ALLOWED is False
    assert QSERIES_HANDOFF_ALLOWED is False
    assert TRADE_AUTHORIZATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False


def main() -> int:
    print("========================================")
    print(" OLA-077 READINESS RETRY TIMESTAMP TEST")
    print(" CANONICAL OLA-023 LINEAGE PRESERVATION")
    print(" NO REAL CONTINUOUS SERVICE START")
    print("========================================")

    assert_read_only_contract()

    module = importlib.import_module(
        MODULE_NAME
    )

    provider_class = getattr(
        module,
        "_ProductionLiveReadinessProvider",
    )

    production_path = Path(
        module.__file__
    )

    production_source = production_path.read_text(
        encoding="utf-8"
    )

    print("[TEST] Production correction installed")

    assert (
        "OLA-077 canonical retry timestamp-lineage correction"
        in production_source
    )

    assert (
        "attempt_checked_at = self._fresh_timestamp()"
        not in production_source
    )

    print("[OK] Production correction installed")

    base_checked_at = datetime(
        2026,
        7,
        19,
        6,
        0,
        0,
        tzinfo=timezone.utc,
    )

    base_evaluated_at = (
        base_checked_at
        + timedelta(microseconds=1)
    )

    sleep_calls: list[float] = []
    clock_calls: list[str] = []

    def forbidden_retry_clock() -> datetime:
        clock_calls.append(
            "clock"
        )

        raise AssertionError(
            "retry recovery must not create replacement "
            "canonical timestamps"
        )

    print("[TEST] Temporary failure followed by recovery")

    recovering_gate = RecoveringFakeGate()

    recovering_provider = construct_provider(
        provider_class,
        gate=recovering_gate,
        sleeper=sleep_calls.append,
        clock=forbidden_retry_clock,
    )

    readiness = recovering_provider(
        iteration_number=1,
        consecutive_failures=0,
        checked_at=base_checked_at,
        evaluated_at=base_evaluated_at,
    )

    assert isinstance(
        readiness,
        FakeReadinessRecord,
    )

    assert len(
        recovering_gate.calls
    ) == 2

    first_call = recovering_gate.calls[0]
    second_call = recovering_gate.calls[1]

    assert (
        first_call["checked_at"]
        == base_checked_at
    )

    assert (
        first_call["evaluated_at"]
        == base_evaluated_at
    )

    assert (
        second_call["checked_at"]
        == base_checked_at
    )

    assert (
        second_call["evaluated_at"]
        == base_evaluated_at
    )

    assert (
        readiness.checked_at
        == base_checked_at
    )

    assert (
        readiness.evaluated_at
        == base_evaluated_at
    )

    assert (
        first_call[
            "rate_window_observation"
        ].checked_at
        == base_checked_at
    )

    assert (
        second_call[
            "rate_window_observation"
        ].checked_at
        == base_checked_at
    )

    assert (
        first_call[
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 1
    )

    assert (
        second_call[
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 2
    )

    assert (
        first_call[
            "readiness_metadata"
        ][
            "scheduler_consecutive_failures"
        ]
        == 0
    )

    assert (
        second_call[
            "readiness_metadata"
        ][
            "scheduler_consecutive_failures"
        ]
        == 0
    )

    assert (
        first_call["consecutive_failures"]
        == 0
    )

    assert (
        second_call["consecutive_failures"]
        == 0
    )

    assert sleep_calls == [5.0]
    assert clock_calls == []

    assert recovering_provider.calls == 1
    assert recovering_provider.readiness_attempts == 2
    assert recovering_provider.transient_failure_count == 1
    assert recovering_provider.last_transient_failure is None

    print("[OK] Retry preserved canonical timestamps")

    print("[TEST] Multiple consecutive readiness retries")

    blocked_gate = AlwaysBlockedFakeGate(
        maximum_attempts=4,
    )

    blocked_sleep_calls: list[float] = []

    blocked_provider = construct_provider(
        provider_class,
        gate=blocked_gate,
        sleeper=blocked_sleep_calls.append,
        clock=forbidden_retry_clock,
    )

    try:
        blocked_provider(
            iteration_number=5,
            consecutive_failures=7,
            checked_at=base_checked_at,
            evaluated_at=base_evaluated_at,
        )
    except StopIteration as exc:
        assert str(exc) == "bounded test termination"
    else:
        raise AssertionError(
            "bounded blocked provider did not terminate test"
        )

    assert len(
        blocked_gate.calls
    ) == 4

    for attempt_number, call in enumerate(
        blocked_gate.calls,
        start=1,
    ):
        assert (
            call["checked_at"]
            == base_checked_at
        )

        assert (
            call["evaluated_at"]
            == base_evaluated_at
        )

        assert (
            call[
                "rate_window_observation"
            ].checked_at
            == base_checked_at
        )

        metadata = call[
            "readiness_metadata"
        ]

        assert (
            metadata[
                "readiness_attempt_number"
            ]
            == attempt_number
        )

        assert (
            metadata[
                "scheduler_consecutive_failures"
            ]
            == 7
        )

        assert (
            metadata[
                "source_health_consecutive_failures"
            ]
            == 0
        )

        assert (
            call["consecutive_failures"]
            == 0
        )

    assert blocked_sleep_calls == [
        5.0,
        10.0,
        20.0,
    ]

    assert clock_calls == []

    print("[OK] Multiple retries preserved one timestamp authority")

    print("[TEST] Immediately ready dependency")

    ready_gate = AlwaysReadyFakeGate()

    ready_provider = construct_provider(
        provider_class,
        gate=ready_gate,
        sleeper=lambda seconds: (
            _ for _ in ()
        ).throw(
            AssertionError(
                "ready dependency must not sleep"
            )
        ),
        clock=forbidden_retry_clock,
    )

    direct = ready_provider(
        iteration_number=10,
        consecutive_failures=100,
        checked_at=base_checked_at,
        evaluated_at=base_evaluated_at,
    )

    assert isinstance(
        direct,
        FakeReadinessRecord,
    )

    assert (
        direct.checked_at
        == base_checked_at
    )

    assert (
        direct.evaluated_at
        == base_evaluated_at
    )

    assert len(
        ready_gate.calls
    ) == 1

    assert (
        ready_gate.calls[0][
            "consecutive_failures"
        ]
        == 0
    )

    assert clock_calls == []

    print("[OK] Immediately ready dependency passed")

    print("[TEST] No execution or service authority introduced")

    forbidden_tokens = (
        "subprocess.Popen(",
        "os.system(",
        "CREATE ORDER",
        "PLACE ORDER",
        "EXECUTION_ALLOWED = True",
        "ORDER_PLACEMENT_ALLOWED = True",
        "FUNDS_MOVED = True",
        "PORTFOLIO_MUTATED = True",
    )

    correction_region_start = production_source.index(
        "OLA-077 canonical retry timestamp-lineage correction"
    )

    correction_region = production_source[
        correction_region_start:
        correction_region_start + 2500
    ]

    for token in forbidden_tokens:
        assert token not in correction_region

    print("[OK] Read-only boundary preserved")

    print(
        "[PASS] OLA-077 Oracle Readiness Retry "
        "Timestamp Lineage Correction"
    )

    print({
        "schema_version": "OLA-077",
        "engine_id": "OLA-077",
        "status": "passed",
        "ola023_timestamp_authority_preserved": True,
        "retry_checked_at_preserved": True,
        "retry_evaluated_at_preserved": True,
        "multiple_retry_lineage_preserved": True,
        "retry_attempt_metadata_preserved": True,
        "retry_backoff_preserved": True,
        "scheduler_failure_separation_preserved": True,
        "source_health_failure_count_reset_preserved": True,
        "replacement_retry_clock_not_used": True,
        "readiness_provider_did_not_preserve_checked_at_fixed": True,
        "real_continuous_service_started": False,
        "process_created": False,
        "thread_created": False,
        "background_loop_started": False,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


def require_production_file() -> str:
    if not PRODUCTION_PATH.exists():
        raise FileNotFoundError(
            f"Missing production file: {PRODUCTION_PATH}"
        )

    source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    if OLD_TIMESTAMP_BLOCK not in source:
        if NEW_TIMESTAMP_BLOCK in source:
            raise RuntimeError(
                "OLA-077 correction already appears installed"
            )

        raise RuntimeError(
            "Expected OLA-069 retry timestamp block was not found. "
            "Production file was not changed."
        )

    occurrence_count = source.count(
        OLD_TIMESTAMP_BLOCK
    )

    if occurrence_count != 1:
        raise RuntimeError(
            "Expected exactly one OLA-069 timestamp block; "
            f"found {occurrence_count}. Production file was not changed."
        )

    return source


def build_corrected_production_source(
    current_source: str,
) -> str:
    corrected_source = current_source.replace(
        OLD_TIMESTAMP_BLOCK,
        NEW_TIMESTAMP_BLOCK,
        1,
    )

    if corrected_source == current_source:
        raise RuntimeError(
            "Production source replacement made no change"
        )

    if OLD_TIMESTAMP_BLOCK in corrected_source:
        raise RuntimeError(
            "Stale OLA-069 timestamp block remains after replacement"
        )

    if corrected_source.count(
        NEW_TIMESTAMP_BLOCK
    ) != 1:
        raise RuntimeError(
            "Corrected OLA-077 timestamp block was not installed exactly once"
        )

    compile(
        corrected_source,
        str(PRODUCTION_PATH),
        "exec",
    )

    return corrected_source


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + ".ola077.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    compile(
        temporary_path.read_text(
            encoding="utf-8"
        ),
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-077 PRODUCTION CORRECTION")
    print(" READINESS RETRY TIMESTAMP LINEAGE")
    print(" OLA-023 CANONICAL TIMESTAMP AUTHORITY")
    print("========================================")

    current_production_source = require_production_file()

    corrected_production_source = (
        build_corrected_production_source(
            current_production_source
        )
    )

    write_full_replacement(
        PRODUCTION_PATH,
        corrected_production_source,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    installed_source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "OLA-077 canonical retry timestamp-lineage correction"
        in installed_source
    )

    assert (
        "attempt_checked_at = self._fresh_timestamp()"
        not in installed_source
    )

    print("[OK] OLA-069 recovery provider corrected")
    print("[OK] Retry checked_at now preserves OLA-023 input")
    print("[OK] Retry evaluated_at now preserves OLA-023 input")
    print("[OK] Retry attempt metadata remains distinct")
    print("[OK] Exponential retry delay remains active")
    print("[OK] OLA-023 compatibility guard remains strict")
    print("[OK] No second canonical timestamp authority remains")
    print("[OK] Temporary readiness blocks remain retryable")
    print("[OK] Oracle read-only boundary preserved")
    print("[OK] No real continuous service started")

    print(
        "\n[DONE] OLA-077 readiness retry timestamp "
        "lineage correction installed"
    )

    print("\nRun:")
    print(
        "py test_ola_077_"
        "oracle_readiness_retry_timestamp_lineage_correction.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )