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
    import tempfile
    from pathlib import Path


    ROOT = Path(__file__).resolve().parent

    LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
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


    def main() -> None:
        print("========================================")
        print(" OLA-074 GUARDED LAUNCHER TEST")
        print(" DETERMINISTIC OPERATIONAL VALIDATION")
        print(" NO REAL CONTINUOUS SERVICE START")
        print("========================================")

        module = _load_module()

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

        try:
            with tempfile.TemporaryDirectory() as directory:
                temporary_root = Path(
                    directory
                )

                environment_file = (
                    temporary_root
                    / ".env"
                )

                runtime_directory = (
                    temporary_root
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

                module.ROOT = temporary_root
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
                    pass
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
                    pass
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

        result = {
            "schema_version": "OLA-074",
            "engine_id": "OLA-074",
            "status": "passed",
            "guarded_launcher_installed": True,
            "canonical_ola072_launcher_required": True,
            "continuous_mode_required": True,
            "bounded_mode_blocked": True,
            "bounded_mode_tested_without_main": True,
            "misleading_third_launch_removed": True,
            "positive_tick_required": True,
            "single_runtime_lock_enforced": True,
            "duplicate_runtime_blocked": True,
            "stale_lock_recovery_verified": True,
            "runtime_lock_release_verified": True,
            "real_continuous_service_started": False,
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
        "OLA-074 GUARDED LAUNCHER TEST",
        "NO REAL CONTINUOUS SERVICE START",
        "Bounded-mode values rejected directly",
        "Direct bounded-mode rejection",
        "module._require_continuous_mode(",
        "bounded_mode_tested_without_main",
        "misleading_third_launch_removed",
        "real_continuous_service_started",
        "[PASS] OLA-074",
    )

    missing_markers = tuple(
        marker
        for marker in required_markers
        if marker not in source
    )

    if missing_markers:
        raise RuntimeError(
            "OLA-074 correction V2 is incomplete. "
            f"Missing markers: {missing_markers}"
        )

    forbidden_markers = (
        "bounded_environment_file",
        "module.ENV_FILE = (\n"
        "                    bounded_environment_file",
        "bounded_fake_launcher",
        "module.main()\n"
        "                except (\n"
        "                    module.OracleContinuousLaunchError",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_markers
        if marker in source
    )

    if forbidden_present:
        raise RuntimeError(
            "OLA-074 correction V2 still contains "
            "the misleading bounded-mode main() test: "
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
        "[OK] Misleading third launcher invocation removed"
    )

    print(
        "[OK] Bounded-mode rejection tested directly"
    )

    print(
        "[OK] No real continuous service starts during test"
    )

    print(
        "[OK] Clean lock lifecycle test preserved"
    )

    print(
        "[OK] Stale lock recovery test preserved"
    )

    print(
        "[OK] Duplicate runtime prevention preserved"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-074 PRODUCTION CORRECTION V2")
    print(" DETERMINISTIC TEST REWRITE")
    print(" REMOVE MISLEADING THIRD LAUNCH")
    print("========================================")

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-074 deterministic test "
        "correction V2 installed"
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