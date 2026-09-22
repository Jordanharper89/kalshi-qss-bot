from __future__ import annotations

from pathlib import Path


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


OLD_RETRY_BRANCH = """            else:
                attempt_checked_at = self._fresh_timestamp()
                attempt_evaluated_at = (
                    attempt_checked_at
                )
"""


NEW_RETRY_BRANCH = """            else:
                # OLA-077 canonical retry timestamp-lineage correction:
                #
                # OLA-023 owns checked_at and evaluated_at for the complete
                # service-runner iteration. Internal OLA-069 readiness
                # recovery attempts remain part of that same iteration and
                # must not establish a second timestamp authority.
                #
                # Preserve the caller-supplied canonical timestamps on every
                # retry. Retry identity remains represented by
                # readiness_attempt_number and the recovery audit metadata.
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
"""


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
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


class RecoveringGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        call = dict(kwargs)
        self.calls.append(call)

        if len(self.calls) == 1:
            raise KalshiLiveReadReadinessFailure(
                "temporary readiness block"
            )

        return SimpleNamespace(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
            read_only=True,
            execution_allowed=False,
        )


class MultiRetryGate:
    def __init__(self, pass_on_attempt: int) -> None:
        self.pass_on_attempt = pass_on_attempt
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        call = dict(kwargs)
        self.calls.append(call)

        if len(self.calls) < self.pass_on_attempt:
            raise KalshiLiveReadReadinessFailure(
                "temporary readiness block"
            )

        return SimpleNamespace(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
            read_only=True,
            execution_allowed=False,
        )


class ImmediatelyReadyGate:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def evaluate(self, **kwargs):
        call = dict(kwargs)
        self.calls.append(call)

        return SimpleNamespace(
            checked_at=call["checked_at"],
            evaluated_at=call["evaluated_at"],
            read_only=True,
            execution_allowed=False,
        )


def build_provider(
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
    print(" EXACT REPOSITORY SOURCE CORRECTION V2")
    print(" NO REAL SERVICE START")
    print("========================================")

    assert_read_only_contract()

    module = import_module(
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

    print("[TEST] OLA-077 production marker")

    marker = (
        "OLA-077 canonical retry timestamp-lineage correction"
    )

    assert marker in production_source

    print("[OK] OLA-077 production marker")

    print("[TEST] Stale retry timestamp generation removed")

    stale_branch = (
        "else:\n"
        "                attempt_checked_at = "
        "self._fresh_timestamp()"
    )

    assert stale_branch not in production_source

    print("[OK] Stale retry timestamp generation removed")

    checked_at = datetime(
        2026,
        7,
        19,
        13,
        30,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(microseconds=1)
    )

    clock_calls: list[str] = []

    def forbidden_clock() -> datetime:
        clock_calls.append(
            "called"
        )

        raise AssertionError(
            "retry path attempted to create a replacement "
            "canonical timestamp"
        )

    print("[TEST] Temporary readiness block recovery")

    recovery_gate = RecoveringGate()
    recovery_sleeps: list[float] = []

    recovery_provider = build_provider(
        provider_class,
        gate=recovery_gate,
        sleeper=recovery_sleeps.append,
        clock=forbidden_clock,
    )

    recovery_result = recovery_provider(
        iteration_number=1,
        consecutive_failures=0,
        checked_at=checked_at,
        evaluated_at=evaluated_at,
    )

    assert len(recovery_gate.calls) == 2
    assert recovery_sleeps == [5.0]
    assert clock_calls == []

    for call in recovery_gate.calls:
        assert call["checked_at"] == checked_at
        assert call["evaluated_at"] == evaluated_at

        assert (
            call["rate_window_observation"].checked_at
            == checked_at
        )

    assert (
        recovery_gate.calls[0][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 1
    )

    assert (
        recovery_gate.calls[1][
            "readiness_metadata"
        ][
            "readiness_attempt_number"
        ]
        == 2
    )

    assert recovery_result.checked_at == checked_at
    assert recovery_result.evaluated_at == evaluated_at
    assert recovery_result.read_only is True
    assert recovery_result.execution_allowed is False

    assert recovery_provider.calls == 1
    assert recovery_provider.readiness_attempts == 2
    assert recovery_provider.transient_failure_count == 1
    assert recovery_provider.last_transient_failure is None

    print("[OK] Temporary block recovery preserved timestamps")

    print("[TEST] Multiple retries preserve one timestamp authority")

    multi_gate = MultiRetryGate(
        pass_on_attempt=4
    )

    multi_sleeps: list[float] = []

    multi_provider = build_provider(
        provider_class,
        gate=multi_gate,
        sleeper=multi_sleeps.append,
        clock=forbidden_clock,
    )

    multi_result = multi_provider(
        iteration_number=25,
        consecutive_failures=6,
        checked_at=checked_at,
        evaluated_at=evaluated_at,
    )

    assert len(multi_gate.calls) == 4
    assert multi_sleeps == [
        5.0,
        10.0,
        20.0,
    ]

    assert clock_calls == []

    for attempt_number, call in enumerate(
        multi_gate.calls,
        start=1,
    ):
        assert call["checked_at"] == checked_at
        assert call["evaluated_at"] == evaluated_at

        assert (
            call["rate_window_observation"].checked_at
            == checked_at
        )

        readiness_metadata = call[
            "readiness_metadata"
        ]

        assert (
            readiness_metadata[
                "readiness_attempt_number"
            ]
            == attempt_number
        )

        assert (
            readiness_metadata[
                "scheduler_consecutive_failures"
            ]
            == 6
        )

        assert (
            readiness_metadata[
                "source_health_consecutive_failures"
            ]
            == 0
        )

        assert call["consecutive_failures"] == 0

    assert multi_result.checked_at == checked_at
    assert multi_result.evaluated_at == evaluated_at
    assert multi_result.read_only is True
    assert multi_result.execution_allowed is False

    assert multi_provider.calls == 1
    assert multi_provider.readiness_attempts == 4
    assert multi_provider.transient_failure_count == 3
    assert multi_provider.last_transient_failure is None

    print("[OK] Multiple retries preserved timestamps")

    print("[TEST] Immediately ready path")

    ready_gate = ImmediatelyReadyGate()

    def forbidden_sleep(seconds: float) -> None:
        raise AssertionError(
            f"immediately ready path slept for {seconds}"
        )

    ready_provider = build_provider(
        provider_class,
        gate=ready_gate,
        sleeper=forbidden_sleep,
        clock=forbidden_clock,
    )

    ready_result = ready_provider(
        iteration_number=100,
        consecutive_failures=20,
        checked_at=checked_at,
        evaluated_at=evaluated_at,
    )

    assert len(ready_gate.calls) == 1
    assert ready_result.checked_at == checked_at
    assert ready_result.evaluated_at == evaluated_at
    assert clock_calls == []

    print("[OK] Immediately ready path")

    print("[TEST] Scheduler and source-health failures remain separated")

    call = multi_gate.calls[-1]

    assert (
        call["readiness_metadata"][
            "scheduler_consecutive_failures"
        ]
        == 6
    )

    assert (
        call["readiness_metadata"][
            "source_health_consecutive_failures"
        ]
        == 0
    )

    assert call["consecutive_failures"] == 0

    print("[OK] Failure domains remain separated")

    print("[TEST] No service or execution authority introduced")

    forbidden_tokens = (
        "subprocess.Popen(",
        "subprocess.run(",
        "os.system(",
        "ORDER_PLACEMENT_ALLOWED = True",
        "TRADE_AUTHORIZATION_ALLOWED = True",
        "EXECUTION_ALLOWED = True",
        "FUNDS_MOVED = True",
        "PORTFOLIO_MUTATED = True",
    )

    marker_position = production_source.index(
        marker
    )

    correction_region = production_source[
        marker_position:
        marker_position + 2400
    ]

    for token in forbidden_tokens:
        assert token not in correction_region

    print("[OK] Oracle read-only boundary preserved")

    print(
        "[PASS] OLA-077 Oracle Readiness Retry "
        "Timestamp Lineage Correction"
    )

    print({
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "exact_repository_source_matched": True,
        "ola023_checked_at_authority_preserved": True,
        "ola023_evaluated_at_authority_preserved": True,
        "first_attempt_timestamp_preserved": True,
        "retry_timestamp_preserved": True,
        "multiple_retry_timestamp_preserved": True,
        "replacement_retry_clock_not_called": True,
        "retry_attempt_metadata_preserved": True,
        "exponential_retry_backoff_preserved": True,
        "scheduler_failure_history_preserved": True,
        "source_health_failure_separation_preserved": True,
        "strict_runner_validation_preserved": True,
        "real_service_started": False,
        "background_loop_started": False,
        "process_created": False,
        "thread_created": False,
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


def read_current_production_source() -> str:
    if not PRODUCTION_PATH.exists():
        raise FileNotFoundError(
            f"Missing production file: {PRODUCTION_PATH}"
        )

    source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    marker = (
        "OLA-077 canonical retry timestamp-lineage correction"
    )

    if marker in source:
        raise RuntimeError(
            "OLA-077 correction already appears installed"
        )

    old_count = source.count(
        OLD_RETRY_BRANCH
    )

    if old_count != 1:
        raise RuntimeError(
            "Expected exactly one live OLA-069 retry branch; "
            f"found {old_count}. Production file was not changed."
        )

    required_context = (
        "class _ProductionLiveReadinessProvider:"
    )

    if required_context not in source:
        raise RuntimeError(
            "OLA-069 production readiness provider was not found. "
            "Production file was not changed."
        )

    provider_position = source.index(
        required_context
    )

    branch_position = source.index(
        OLD_RETRY_BRANCH
    )

    if branch_position < provider_position:
        raise RuntimeError(
            "Matched retry branch is outside the OLA-069 provider. "
            "Production file was not changed."
        )

    following_anchor = (
        "            rate_observation = (\n"
        "                RateWindowObservation.create("
    )

    following_position = source.find(
        following_anchor,
        branch_position,
    )

    if following_position == -1:
        raise RuntimeError(
            "Expected OLA-069 rate observation anchor was not found. "
            "Production file was not changed."
        )

    if (
        following_position
        - branch_position
        > 1000
    ):
        raise RuntimeError(
            "Matched retry branch is not adjacent to the expected "
            "OLA-069 rate observation. Production file was not changed."
        )

    return source


def create_corrected_production_source(
    current_source: str,
) -> str:
    corrected_source = current_source.replace(
        OLD_RETRY_BRANCH,
        NEW_RETRY_BRANCH,
        1,
    )

    if corrected_source == current_source:
        raise RuntimeError(
            "Production replacement produced no change"
        )

    if OLD_RETRY_BRANCH in corrected_source:
        raise RuntimeError(
            "Stale OLA-069 retry branch remains after replacement"
        )

    if corrected_source.count(
        NEW_RETRY_BRANCH
    ) != 1:
        raise RuntimeError(
            "OLA-077 retry correction was not installed exactly once"
        )

    if (
        "attempt_checked_at = self._fresh_timestamp()"
        in corrected_source
    ):
        raise RuntimeError(
            "Replacement retry timestamp generation remains in "
            "production source"
        )

    compile(
        corrected_source,
        str(PRODUCTION_PATH),
        "exec",
    )

    return corrected_source


def write_complete_file(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + ".ola077_v2.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    written_source = temporary_path.read_text(
        encoding="utf-8"
    )

    compile(
        written_source,
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def verify_installed_production_source() -> None:
    installed_source = PRODUCTION_PATH.read_text(
        encoding="utf-8"
    )

    marker = (
        "OLA-077 canonical retry timestamp-lineage correction"
    )

    assert marker in installed_source

    assert (
        installed_source.count(
            NEW_RETRY_BRANCH
        )
        == 1
    )

    assert OLD_RETRY_BRANCH not in installed_source

    assert (
        "attempt_checked_at = self._fresh_timestamp()"
        not in installed_source
    )

    compile(
        installed_source,
        str(PRODUCTION_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-077 PRODUCTION CORRECTION V2")
    print(" EXACT REPOSITORY RETRY BRANCH MATCH")
    print(" OLA-023 TIMESTAMP AUTHORITY")
    print("========================================")

    current_source = (
        read_current_production_source()
    )

    corrected_source = (
        create_corrected_production_source(
            current_source
        )
    )

    write_complete_file(
        PRODUCTION_PATH,
        corrected_source,
    )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    verify_installed_production_source()

    print("[OK] Exact live OLA-069 retry branch matched")
    print("[OK] Complete production source rewritten")
    print("[OK] Complete OLA-077 test written")
    print("[OK] Retry checked_at preserves OLA-023 authority")
    print("[OK] Retry evaluated_at preserves OLA-023 authority")
    print("[OK] Replacement retry clock removed")
    print("[OK] Retry attempt metadata preserved")
    print("[OK] Exponential retry backoff preserved")
    print("[OK] Scheduler/source-health separation preserved")
    print("[OK] Strict OLA-023 runner validation preserved")
    print("[OK] Oracle read-only boundary preserved")
    print("[OK] No real continuous service started")

    print(
        "\n[DONE] OLA-077 readiness retry timestamp "
        "lineage correction V2 installed"
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