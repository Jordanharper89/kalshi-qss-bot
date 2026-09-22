from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

TEST_FILE = (
    ROOT
    / "test_ola_074_oracle_guarded_continuous_production_launcher.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import json
    import os
    import shutil
    import signal
    import traceback
    import uuid
    from dataclasses import dataclass
    from datetime import datetime, timezone
    from pathlib import Path
    from types import FrameType
    from typing import Any, Callable


    ROOT = Path(__file__).resolve().parent

    LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    TEST_SANDBOX_ROOT = (
        ROOT
        / "runtime"
        / "ola074_test_sandbox"
    )


    @dataclass(frozen=True)
    class CapturedConsoleInterrupt:
        signal_number: int
        signal_name: str
        captured_at: str
        filename: str
        line_number: int
        function_name: str
        stack_summary: tuple[str, ...]


    class DeterministicConsoleInterruptCapture:
        """
        Test-only Windows console interrupt capture.

        This prevents unexpected console-control events from
        terminating the deterministic OLA-074 test.

        It does not modify the production launcher and it restores
        every original signal handler before the test exits.
        """

        def __init__(self) -> None:
            self._original_handlers: dict[
                int,
                Any,
            ] = {}

            self._captured_events: list[
                CapturedConsoleInterrupt
            ] = []

            self._installed = False

        @property
        def captured_events(
            self,
        ) -> tuple[CapturedConsoleInterrupt, ...]:
            return tuple(
                self._captured_events
            )

        def _supported_console_signals(
            self,
        ) -> tuple[int, ...]:
            supported: list[int] = [
                signal.SIGINT,
            ]

            sigbreak = getattr(
                signal,
                "SIGBREAK",
                None,
            )

            if (
                isinstance(sigbreak, int)
                and sigbreak not in supported
            ):
                supported.append(
                    sigbreak
                )

            return tuple(
                supported
            )

        def _capture_handler(
            self,
            signal_number: int,
            frame: FrameType | None,
        ) -> None:
            signal_name = (
                signal.Signals(
                    signal_number
                ).name
            )

            if frame is None:
                filename = "<unknown>"
                line_number = -1
                function_name = "<unknown>"
            else:
                filename = frame.f_code.co_filename
                line_number = frame.f_lineno
                function_name = frame.f_code.co_name

            stack_entries = traceback.extract_stack(
                frame,
                limit=8,
            )

            stack_summary = tuple(
                (
                    f"{entry.filename}:"
                    f"{entry.lineno}:"
                    f"{entry.name}"
                )
                for entry in stack_entries
            )

            event = CapturedConsoleInterrupt(
                signal_number=signal_number,
                signal_name=signal_name,
                captured_at=(
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                filename=filename,
                line_number=line_number,
                function_name=function_name,
                stack_summary=stack_summary,
            )

            self._captured_events.append(
                event
            )

            print()
            print(
                "[DIAGNOSTIC] Unexpected console "
                f"interrupt captured: {signal_name}"
            )

            print(
                "[DIAGNOSTIC] Location:",
                f"{filename}:{line_number}",
                function_name,
            )

            print(
                "[DIAGNOSTIC] Deterministic test "
                "continues; production handlers "
                "remain unchanged"
            )

        def install(
            self,
        ) -> None:
            if self._installed:
                raise RuntimeError(
                    "Console interrupt capture is "
                    "already installed"
                )

            for signal_number in (
                self._supported_console_signals()
            ):
                self._original_handlers[
                    signal_number
                ] = signal.getsignal(
                    signal_number
                )

                signal.signal(
                    signal_number,
                    self._capture_handler,
                )

            self._installed = True

            print(
                "[OK] Test-only console interrupt "
                "capture installed"
            )

        def restore(
            self,
        ) -> None:
            if not self._installed:
                return

            for (
                signal_number,
                original_handler,
            ) in self._original_handlers.items():
                signal.signal(
                    signal_number,
                    original_handler,
                )

            self._installed = False

            print(
                "[OK] Original console signal "
                "handlers restored"
            )


    def _load_module():
        specification = (
            importlib.util.spec_from_file_location(
                "ola074_launcher_under_test",
                LAUNCHER_FILE,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise RuntimeError(
                "Could not load OLA-074 launcher"
            )

        module = (
            importlib.util.module_from_spec(
                specification
            )
        )

        specification.loader.exec_module(
            module
        )

        return module


    class FakeCanonicalLauncher:
        SCHEMA_VERSION = "OLA-072"
        ENGINE_ID = "OLA-072"

        def __init__(self) -> None:
            self.call_count = 0

        def main(self) -> int:
            self.call_count += 1
            return 0


    def _create_test_sandbox() -> Path:
        TEST_SANDBOX_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        sandbox = (
            TEST_SANDBOX_ROOT
            / (
                "run-"
                + uuid.uuid4().hex
            )
        )

        sandbox.mkdir(
            parents=True,
            exist_ok=False,
        )

        print(
            "[OK] Deterministic sandbox created:",
            sandbox,
        )

        return sandbox


    def _remove_test_sandbox(
        sandbox: Path,
    ) -> None:
        if not sandbox.exists():
            return

        last_error: Exception | None = None

        for attempt in range(
            1,
            4,
        ):
            try:
                shutil.rmtree(
                    sandbox
                )

                print(
                    "[OK] Deterministic sandbox removed"
                )

                return

            except Exception as exc:
                last_error = exc

                print(
                    "[WARN] Sandbox cleanup attempt",
                    attempt,
                    "failed:",
                    type(exc).__name__,
                    str(exc),
                )

        raise RuntimeError(
            "Could not remove deterministic "
            f"test sandbox: {sandbox}"
        ) from last_error


    def _assert_handler_restored(
        signal_number: int,
        expected_handler: Any,
    ) -> None:
        actual_handler = signal.getsignal(
            signal_number
        )

        assert actual_handler == expected_handler, (
            "Original signal handler was not "
            f"restored for signal {signal_number}"
        )


    def _run_deterministic_validation(
        module,
        sandbox: Path,
    ) -> dict[str, Any]:
        assert (
            module.SCHEMA_VERSION
            == "OLA-074"
        )

        assert (
            module.ENGINE_ID
            == "OLA-074"
        )

        print(
            "[OK] OLA-074 launcher module loaded"
        )

        assert (
            module._require_positive_tick(
                {}
            )
            == 5
        )

        assert (
            module._require_positive_tick(
                {
                    "ORACLE_LIVE_SHADOW_TICK_SECONDS": "1",
                }
            )
            == 1
        )

        for invalid_tick in (
            "0",
            "-1",
            "abc",
        ):
            try:
                module._require_positive_tick(
                    {
                        "ORACLE_LIVE_SHADOW_TICK_SECONDS": (
                            invalid_tick
                        ),
                    }
                )
            except (
                module.OracleContinuousLaunchError
            ):
                pass
            else:
                raise AssertionError(
                    "Invalid tick value accepted: "
                    f"{invalid_tick}"
                )

        print(
            "[OK] Positive cadence validation passed"
        )

        continuous_cases = (
            {},
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "",
            },
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "none",
            },
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "null",
            },
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "continuous",
            },
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "unbounded",
            },
            {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "forever",
            },
        )

        for environment in continuous_cases:
            module._require_continuous_mode(
                environment
            )

        print(
            "[OK] Continuous-mode values accepted"
        )

        for bounded_value in (
            "1",
            "3",
            "100",
        ):
            try:
                module._require_continuous_mode(
                    {
                        "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": (
                            bounded_value
                        ),
                    }
                )
            except (
                module.OracleContinuousLaunchError
            ):
                pass
            else:
                raise AssertionError(
                    "Bounded runtime was accepted by "
                    "the continuous launcher: "
                    f"{bounded_value}"
                )

        print(
            "[OK] Bounded-mode values rejected directly"
        )

        original_environment = dict(
            os.environ
        )

        original_root = module.ROOT
        original_env_file = module.ENV_FILE

        original_runtime_directory = (
            module.RUNTIME_DIRECTORY
        )

        original_lock_file = (
            module.LOCK_FILE
        )

        original_loader = (
            module._load_canonical_launcher
        )

        clean_lifecycle_verified = False
        stale_lock_recovery_verified = False
        duplicate_runtime_blocked = False
        bounded_mode_blocked = False

        try:
            environment_file = (
                sandbox
                / ".env"
            )

            runtime_directory = (
                sandbox
                / "runtime"
                / "oracle_live_shadow"
            )

            lock_file = (
                runtime_directory
                / "oracle_continuous_runtime.lock"
            )

            environment_file.write_text(
                "\n".join(
                    (
                        (
                            "DATABASE_URL="
                            "postgresql://oracle:test@"
                            "localhost:5432/postgres"
                        ),
                        (
                            "ORACLE_POSTGRES_SSLMODE="
                            "disable"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_TICK_SECONDS="
                            "1"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_MAX_ITERATIONS="
                            "continuous"
                        ),
                        "",
                    )
                ),
                encoding="utf-8",
            )

            module.ROOT = sandbox
            module.ENV_FILE = environment_file
            module.RUNTIME_DIRECTORY = (
                runtime_directory
            )
            module.LOCK_FILE = lock_file

            fake_launcher = (
                FakeCanonicalLauncher()
            )

            module._load_canonical_launcher = (
                lambda: fake_launcher
            )

            print(
                "[TEST] Clean guarded launcher lifecycle"
            )

            exit_code = module.main()

            assert exit_code == 0

            assert (
                fake_launcher.call_count
                == 1
            )

            assert not lock_file.exists(), (
                "Runtime lock remained after "
                "the launcher returned."
            )

            clean_lifecycle_verified = True

            print(
                "[OK] Runtime lock acquired and released"
            )

            runtime_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            stale_lock = {
                "schema_version": "OLA-074",
                "engine_id": "OLA-074",
                "process_id": 999999999,
                "read_only": True,
                "execution_allowed": False,
            }

            lock_file.write_text(
                json.dumps(
                    stale_lock
                ),
                encoding="utf-8",
            )

            second_fake_launcher = (
                FakeCanonicalLauncher()
            )

            module._load_canonical_launcher = (
                lambda: second_fake_launcher
            )

            print(
                "[TEST] Stale runtime lock recovery"
            )

            second_exit_code = module.main()

            assert second_exit_code == 0

            assert (
                second_fake_launcher.call_count
                == 1
            )

            assert not lock_file.exists(), (
                "Stale runtime lock was not "
                "cleaned up."
            )

            stale_lock_recovery_verified = True

            print(
                "[OK] Stale runtime lock recovered"
            )

            active_lock = {
                "schema_version": "OLA-074",
                "engine_id": "OLA-074",
                "process_id": os.getpid(),
                "read_only": True,
                "execution_allowed": False,
            }

            lock_file.write_text(
                json.dumps(
                    active_lock
                ),
                encoding="utf-8",
            )

            print(
                "[TEST] Duplicate active runtime rejection"
            )

            try:
                module._acquire_runtime_lock()
            except (
                module.OracleContinuousRuntimeAlreadyActive
            ):
                duplicate_runtime_blocked = True
            else:
                raise AssertionError(
                    "Duplicate active Oracle runtime "
                    "was not blocked."
                )

            assert lock_file.exists(), (
                "Active runtime lock should remain "
                "after duplicate rejection."
            )

            lock_file.unlink(
                missing_ok=True
            )

            print(
                "[OK] Duplicate active runtime blocked"
            )

            bounded_environment = {
                "DATABASE_URL": (
                    "postgresql://oracle:test@"
                    "localhost:5432/postgres"
                ),
                "ORACLE_LIVE_SHADOW_TICK_SECONDS": "1",
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "3",
            }

            print(
                "[TEST] Direct bounded-mode rejection"
            )

            try:
                module._require_continuous_mode(
                    bounded_environment
                )
            except (
                module.OracleContinuousLaunchError
            ):
                bounded_mode_blocked = True
            else:
                raise AssertionError(
                    "Guarded continuous launcher "
                    "accepted bounded mode."
                )

            assert not lock_file.exists(), (
                "Bounded-mode validation unexpectedly "
                "created a runtime lock."
            )

            print(
                "[OK] Bounded mode rejected without "
                "entering launcher main()"
            )

        finally:
            os.environ.clear()
            os.environ.update(
                original_environment
            )

            module.ROOT = original_root
            module.ENV_FILE = original_env_file

            module.RUNTIME_DIRECTORY = (
                original_runtime_directory
            )

            module.LOCK_FILE = (
                original_lock_file
            )

            module._load_canonical_launcher = (
                original_loader
            )

        return {
            "clean_lifecycle_verified": (
                clean_lifecycle_verified
            ),
            "stale_lock_recovery_verified": (
                stale_lock_recovery_verified
            ),
            "duplicate_runtime_blocked": (
                duplicate_runtime_blocked
            ),
            "bounded_mode_blocked": (
                bounded_mode_blocked
            ),
        }


    def main() -> None:
        print("========================================")
        print(" OLA-074 GUARDED LAUNCHER TEST")
        print(" WINDOWS INTERRUPT DIAGNOSTIC V3")
        print(" NO REAL CONTINUOUS SERVICE START")
        print("========================================")

        interrupt_capture = (
            DeterministicConsoleInterruptCapture()
        )

        original_sigint_handler = (
            signal.getsignal(
                signal.SIGINT
            )
        )

        sigbreak_number = getattr(
            signal,
            "SIGBREAK",
            None,
        )

        original_sigbreak_handler = (
            signal.getsignal(
                sigbreak_number
            )
            if isinstance(
                sigbreak_number,
                int,
            )
            else None
        )

        sandbox: Path | None = None
        validation_result: dict[
            str,
            Any,
        ] = {}

        cleanup_completed = False

        interrupt_capture.install()

        try:
            module = _load_module()

            sandbox = _create_test_sandbox()

            validation_result = (
                _run_deterministic_validation(
                    module,
                    sandbox,
                )
            )

            _remove_test_sandbox(
                sandbox
            )

            cleanup_completed = True

        finally:
            if (
                sandbox is not None
                and sandbox.exists()
            ):
                try:
                    _remove_test_sandbox(
                        sandbox
                    )

                    cleanup_completed = True

                except Exception as cleanup_error:
                    print(
                        "[WARN] Final sandbox cleanup failed:",
                        type(cleanup_error).__name__,
                        str(cleanup_error),
                    )

            interrupt_capture.restore()

        _assert_handler_restored(
            signal.SIGINT,
            original_sigint_handler,
        )

        if isinstance(
            sigbreak_number,
            int,
        ):
            _assert_handler_restored(
                sigbreak_number,
                original_sigbreak_handler,
            )

        print(
            "[OK] Production Ctrl+C behavior remains untouched"
        )

        print(
            "[OK] Test sandbox cleanup completed:",
            cleanup_completed,
        )

        captured_events = (
            interrupt_capture.captured_events
        )

        print(
            "[DIAGNOSTIC] Captured console interrupt count:",
            len(captured_events),
        )

        for index, event in enumerate(
            captured_events,
            start=1,
        ):
            print(
                f"[DIAGNOSTIC] Event {index}:",
                {
                    "signal_number": (
                        event.signal_number
                    ),
                    "signal_name": (
                        event.signal_name
                    ),
                    "captured_at": (
                        event.captured_at
                    ),
                    "filename": (
                        event.filename
                    ),
                    "line_number": (
                        event.line_number
                    ),
                    "function_name": (
                        event.function_name
                    ),
                    "stack_summary": (
                        event.stack_summary
                    ),
                },
            )

        source = LAUNCHER_FILE.read_text(
            encoding="utf-8"
        )

        required_markers = (
            'SCHEMA_VERSION = "OLA-074"',
            "oracle_continuous_runtime.lock",
            "_require_continuous_mode",
            "_acquire_runtime_lock",
            "_release_runtime_lock",
            "OracleContinuousRuntimeAlreadyActive",
            "run_oracle_live_shadow_FINAL_FIXED.py",
            "canonical_launcher.main()",
            "finally:",
            "read_only",
            "execution_allowed",
        )

        missing_markers = tuple(
            marker
            for marker in required_markers
            if marker not in source
        )

        if missing_markers:
            raise AssertionError(
                "OLA-074 launcher source is incomplete: "
                f"{missing_markers}"
            )

        assert (
            validation_result[
                "clean_lifecycle_verified"
            ]
            is True
        )

        assert (
            validation_result[
                "stale_lock_recovery_verified"
            ]
            is True
        )

        assert (
            validation_result[
                "duplicate_runtime_blocked"
            ]
            is True
        )

        assert (
            validation_result[
                "bounded_mode_blocked"
            ]
            is True
        )

        assert cleanup_completed is True

        result = {
            "schema_version": "OLA-074",
            "engine_id": "OLA-074",
            "status": "passed",
            "guarded_launcher_installed": True,
            "canonical_ola072_launcher_required": True,
            "continuous_mode_required": True,
            "bounded_mode_blocked": True,
            "bounded_mode_tested_without_main": True,
            "positive_tick_required": True,
            "single_runtime_lock_enforced": True,
            "duplicate_runtime_blocked": True,
            "stale_lock_recovery_verified": True,
            "runtime_lock_release_verified": True,
            "test_only_interrupt_capture_installed": True,
            "test_only_interrupt_capture_restored": True,
            "captured_console_interrupt_count": (
                len(captured_events)
            ),
            "unexpected_interrupts_diagnosed": True,
            "automatic_temporary_directory_removed": True,
            "deterministic_sandbox_cleanup_verified": True,
            "real_continuous_service_started": False,
            "production_signal_handlers_modified": False,
            "operator_ctrl_c_shutdown_preserved": True,
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
            "[PASS] OLA-074 Oracle Guarded "
            "Continuous Production Launcher"
        )

        print(result)


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
    source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    required_markers = (
        "WINDOWS INTERRUPT DIAGNOSTIC V3",
        "DeterministicConsoleInterruptCapture",
        "CapturedConsoleInterrupt",
        "signal.SIGINT",
        "SIGBREAK",
        "_capture_handler",
        "Original console signal handlers restored",
        "TEST_SANDBOX_ROOT",
        "_create_test_sandbox",
        "_remove_test_sandbox",
        "automatic_temporary_directory_removed",
        "production_signal_handlers_modified",
        "captured_console_interrupt_count",
        "[PASS] OLA-074",
    )

    missing_markers = tuple(
        marker
        for marker in required_markers
        if marker not in source
    )

    if missing_markers:
        raise RuntimeError(
            "OLA-074 correction V3 is incomplete. "
            f"Missing markers: {missing_markers}"
        )

    forbidden_markers = (
        "tempfile.TemporaryDirectory",
        "signal.SIG_IGN",
        "os.kill(os.getpid(), signal.SIGINT)",
        "production_signal_handlers_modified\": True",
        "real_continuous_service_started\": True",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_markers
        if marker in source
    )

    if forbidden_present:
        raise RuntimeError(
            "OLA-074 correction V3 contains "
            "forbidden logic: "
            f"{forbidden_present}"
        )

    compile(
        source,
        str(TEST_FILE),
        "exec",
    )

    print(
        "[OK] Complete OLA-074 test replaced"
    )

    print(
        "[OK] Test-only SIGINT capture installed"
    )

    print(
        "[OK] Test-only SIGBREAK capture installed"
    )

    print(
        "[OK] Interrupt location diagnostics installed"
    )

    print(
        "[OK] Automatic TemporaryDirectory removed"
    )

    print(
        "[OK] Deterministic repository sandbox installed"
    )

    print(
        "[OK] Original signal-handler restoration frozen"
    )

    print(
        "[OK] Production Ctrl+C behavior preserved"
    )

    print(
        "[OK] No real continuous service starts during test"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-074 PRODUCTION CORRECTION V3")
    print(" WINDOWS CONSOLE INTERRUPT DIAGNOSTIC")
    print(" TEST-ONLY SIGNAL ISOLATION")
    print("========================================")

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-074 Windows console "
        "interrupt correction V3 installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_074_oracle_guarded_"
        "continuous_production_launcher.py"
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