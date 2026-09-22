from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


REPOSITORY_ROOT = Path(__file__).resolve().parent

TEST_FILE = (
    REPOSITORY_ROOT
    / "test_ola_070_oracle_persistent_runtime_readiness_recovery_integration_gate.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib
    from datetime import datetime, timedelta, timezone
    from typing import Any

    from qseries_v2.oracle_intelligence.live_acquisition.oracle_kalshi_live_read_readiness_gate import (
        KalshiLiveReadReadinessFailure,
    )
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_persistent_service_activation import (
        OracleProductionLiveShadowPersistentServiceActivationBlocked,
        OracleProductionLiveShadowPersistentServiceActivator,
        OracleProductionLiveShadowPersistentServiceActivationRecord,
    )


    SCHEMA_VERSION = "OLA-070"
    ENGINE_ID = "OLA-070"

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
        alerts_allowed = False
        qseries_handoff_allowed = False
        trade_authorization_allowed = False
        order_placement_allowed = False
        funds_moved = False
        portfolio_mutated = False


    class RecoveringReadinessGate:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def evaluate(self, **kwargs):
            self.calls.append(dict(kwargs))

            if len(self.calls) == 1:
                raise KalshiLiveReadReadinessFailure(
                    "temporary Kalshi source-health interruption"
                )

            return FakeReadinessRecord()


    class PersistentServiceRunner:
        read_only = True
        execution_allowed = False

        def __init__(
            self,
            *,
            readiness_provider,
            checked_at: datetime,
        ) -> None:
            self._readiness_provider = readiness_provider
            self._checked_at = checked_at
            self.run_calls = 0
            self.acquisition_cycle_calls = 0

        def run(
            self,
            *,
            max_iterations: int,
        ):
            self.run_calls += 1

            readiness = self._readiness_provider(
                iteration_number=1,
                consecutive_failures=7,
                checked_at=self._checked_at,
                evaluated_at=self._checked_at,
            )

            if (
                getattr(
                    readiness,
                    "acquisition_allowed",
                    False,
                )
                is not True
            ):
                raise AssertionError(
                    "Acquisition cannot begin without "
                    "approved readiness."
                )

            self.acquisition_cycle_calls += 1

            return {
                "status": "completed",
                "max_iterations": max_iterations,
                "readiness_status": (
                    readiness.readiness_status
                ),
                "acquisition_cycle_calls": (
                    self.acquisition_cycle_calls
                ),
                "read_only": True,
                "execution_allowed": False,
            }


    def _build_provider(
        *,
        provider_class,
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


    def main() -> None:
        module = importlib.import_module(
            MODULE_NAME
        )

        provider_class = getattr(
            module,
            "_ProductionLiveReadinessProvider",
        )

        production_source = (
            module.__file__
        )

        with open(
            production_source,
            "r",
            encoding="utf-8",
        ) as handle:
            source_text = handle.read()

        assert (
            "scheduler_consecutive_failures"
            in source_text
        )

        assert (
            "source_health_consecutive_failures"
            in source_text
        )

        assert "consecutive_failures=0" in source_text

        assert (
            "except KalshiLiveReadReadinessFailure"
            in source_text
        )

        base_time = datetime(
            2026,
            7,
            18,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )

        retry_clock_values = iter(
            (
                base_time + timedelta(seconds=5),
                base_time + timedelta(seconds=10),
            )
        )

        sleep_calls: list[float] = []

        gate = RecoveringReadinessGate()

        provider = _build_provider(
            provider_class=provider_class,
            gate=gate,
            sleeper=sleep_calls.append,
            clock=lambda: next(
                retry_clock_values
            ),
        )

        runner = PersistentServiceRunner(
            readiness_provider=provider,
            checked_at=base_time,
        )

        production_graph = {
            "production_controlled_launch_package_assembler": (
                object()
            ),
            "production_controlled_launch_package_consumer": (
                object()
            ),
            "production_controlled_launch_permit_executor": (
                object()
            ),
            "service_runner": runner,
        }

        activator = (
            OracleProductionLiveShadowPersistentServiceActivator()
        )

        activation_record, result = activator.activate(
            production_graph=production_graph,
            start_kwargs={
                "max_iterations": 1,
            },
        )

        assert isinstance(
            activation_record,
            OracleProductionLiveShadowPersistentServiceActivationRecord,
        )

        assert activation_record.schema_version == "OLA-063"
        assert activation_record.engine_id == "OLA-063"

        assert (
            activation_record.exact_production_graph_required
            is True
        )

        assert (
            activation_record.ola062_controlled_execution_boundary_present
            is True
        )

        assert (
            activation_record.existing_service_runner_required
            is True
        )

        assert (
            activation_record.service_start_callable_resolved
            is True
        )

        assert (
            activation_record.service_start_invoked
            is True
        )

        assert (
            activation_record.single_activation_enforced
            is True
        )

        assert activation_record.read_only is True
        assert activation_record.execution_allowed is False
        assert activation_record.alerts_allowed is False

        assert runner.run_calls == 1
        assert runner.acquisition_cycle_calls == 1

        assert provider.calls == 1
        assert provider.readiness_attempts == 2
        assert provider.transient_failure_count == 1
        assert provider.last_transient_failure is None

        assert sleep_calls == [5.0]
        assert len(gate.calls) == 2

        first_gate_call = gate.calls[0]
        second_gate_call = gate.calls[1]

        assert (
            first_gate_call["consecutive_failures"]
            == 0
        )

        assert (
            second_gate_call["consecutive_failures"]
            == 0
        )

        first_metadata = first_gate_call[
            "readiness_metadata"
        ]

        second_metadata = second_gate_call[
            "readiness_metadata"
        ]

        assert (
            first_metadata[
                "scheduler_consecutive_failures"
            ]
            == 7
        )

        assert (
            first_metadata[
                "source_health_consecutive_failures"
            ]
            == 0
        )

        assert (
            second_metadata[
                "scheduler_consecutive_failures"
            ]
            == 7
        )

        assert (
            second_metadata[
                "source_health_consecutive_failures"
            ]
            == 0
        )

        assert (
            second_gate_call["checked_at"]
            > first_gate_call["checked_at"]
        )

        assert (
            result["status"]
            == "completed"
        )

        assert (
            result["readiness_status"]
            == "ready"
        )

        assert (
            result["acquisition_cycle_calls"]
            == 1
        )

        assert result["read_only"] is True
        assert result["execution_allowed"] is False

        try:
            activator.activate(
                production_graph=production_graph,
                start_kwargs={
                    "max_iterations": 1,
                },
            )
        except (
            OracleProductionLiveShadowPersistentServiceActivationBlocked
        ):
            pass
        else:
            raise AssertionError(
                "Duplicate persistent activation "
                "did not fail closed."
            )

        unsafe_runner = PersistentServiceRunner(
            readiness_provider=provider,
            checked_at=base_time,
        )

        unsafe_runner.read_only = False

        unsafe_graph = {
            "production_controlled_launch_package_assembler": (
                object()
            ),
            "production_controlled_launch_package_consumer": (
                object()
            ),
            "production_controlled_launch_permit_executor": (
                object()
            ),
            "service_runner": unsafe_runner,
        }

        unsafe_activator = (
            OracleProductionLiveShadowPersistentServiceActivator()
        )

        try:
            unsafe_activator.activate(
                production_graph=unsafe_graph,
                start_kwargs={
                    "max_iterations": 1,
                },
            )
        except (
            OracleProductionLiveShadowPersistentServiceActivationBlocked
        ):
            pass
        else:
            raise AssertionError(
                "Non-read-only runner did not fail closed."
            )

        result_record = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "ola069_source_health_separation_present": True,
            "ola069_retry_recovery_present": True,
            "ola063_persistent_activation_exercised": True,
            "temporary_readiness_failure_contained": True,
            "acquisition_paused_during_failure": True,
            "acquisition_started_after_recovery": True,
            "scheduler_failures_not_used_as_source_failures": True,
            "fresh_retry_timestamp_used": True,
            "single_activation_enforced": True,
            "unsafe_runner_blocked": True,
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
            "[PASS] OLA-070 Oracle Persistent Runtime "
            "Readiness Recovery Integration Gate"
        )
        print(result_record)


    if __name__ == "__main__":
        main()
    '''
).lstrip()


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
    text = TEST_FILE.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-070"',
        "OracleProductionLiveShadowPersistentServiceActivator",
        "scheduler_consecutive_failures",
        "source_health_consecutive_failures",
        "acquisition_started_after_recovery",
        "single_activation_enforced",
        "unsafe_runner_blocked",
        "print(",
    )

    missing = [
        marker
        for marker in required_markers
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            "OLA-070 installation is incomplete. "
            f"Missing markers: {missing}"
        )


def main() -> None:
    print("========================================")
    print(" OLA-070 INTEGRATION GATE")
    print(" PERSISTENT RUNTIME READINESS RECOVERY")
    print(" OLA-069 THROUGH OLA-063 ACTIVATION")
    print("========================================")

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-070 persistent runtime "
        "readiness recovery integration gate installed"
    )
    print()
    print("Run:")
    print(
        "py "
        "test_ola_070_oracle_persistent_runtime_"
        "readiness_recovery_integration_gate.py"
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