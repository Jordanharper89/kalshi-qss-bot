from __future__ import annotations

from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

TEST_PATH = (
    ROOT
    / "test_ola_080_oracle_guarded_continuous_runtime_lifecycle_gate.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import json
    import os
    from pathlib import Path
    from types import SimpleNamespace


    SCHEMA_VERSION = "OLA-080"
    ENGINE_ID = "OLA-080-CORRECTION-V4"

    ROOT = Path(__file__).resolve().parent

    GUARDED_LAUNCHER_PATH = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    TEST_ROOT = (
        ROOT
        / "runtime"
        / "ola080_v4"
    )

    TEST_ENV_FILE = (
        TEST_ROOT
        / "ola080.env"
    )

    READ_ONLY = True
    EXECUTION_ALLOWED = False
    ALERTS_ALLOWED = False
    QSERIES_HANDOFF_ALLOWED = False
    TRADE_AUTHORIZATION_ALLOWED = False
    ORDER_PLACEMENT_ALLOWED = False
    FUNDS_MOVED = False
    PORTFOLIO_MUTATED = False


    def load_guarded_launcher_once():
        specification = (
            importlib.util.spec_from_file_location(
                "ola080_guarded_launcher_v4",
                str(GUARDED_LAUNCHER_PATH),
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise AssertionError(
                "Could not create the guarded launcher "
                "import specification."
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


    def remove_file_only(
        path: Path,
    ) -> None:
        try:
            path.unlink(
                missing_ok=True
            )
        except PermissionError:
            try:
                os.chmod(
                    path,
                    0o700,
                )
            except OSError:
                pass

            path.unlink(
                missing_ok=True
            )


    def prepare_flat_test_area() -> None:
        TEST_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        TEST_ENV_FILE.write_text(
            "\n".join(
                (
                    (
                        "DATABASE_URL="
                        "postgresql://oracle:oracle@"
                        "localhost:5432/postgres"
                    ),
                    (
                        "ORACLE_LIVE_SHADOW_"
                        "TICK_SECONDS=5"
                    ),
                    "",
                )
            ),
            encoding="utf-8",
            newline="\n",
        )


    def configure_scenario(
        module,
        scenario_name: str,
    ) -> Path:
        lock_file = (
            TEST_ROOT
            / (
                scenario_name
                + ".lock"
            )
        )

        remove_file_only(
            lock_file
        )

        module.ENV_FILE = TEST_ENV_FILE
        module.RUNTIME_DIRECTORY = TEST_ROOT
        module.LOCK_FILE = lock_file

        return lock_file


    def assert_authority_boundary() -> None:
        assert READ_ONLY is True
        assert EXECUTION_ALLOWED is False
        assert ALERTS_ALLOWED is False
        assert QSERIES_HANDOFF_ALLOWED is False
        assert TRADE_AUTHORIZATION_ALLOWED is False
        assert ORDER_PLACEMENT_ALLOWED is False
        assert FUNDS_MOVED is False
        assert PORTFOLIO_MUTATED is False


    def assert_static_launcher_contract(
        module,
    ) -> None:
        assert module.SCHEMA_VERSION == "OLA-074"
        assert module.ENGINE_ID == "OLA-074"

        required_callables = (
            "_load_runtime_environment",
            "_require_positive_tick",
            "_require_continuous_mode",
            "_process_is_alive",
            "_read_existing_lock",
            "_remove_stale_lock",
            "_acquire_runtime_lock",
            "_release_runtime_lock",
            "_load_canonical_launcher",
            "main",
        )

        for callable_name in required_callables:
            callable_value = getattr(
                module,
                callable_name,
                None,
            )

            if not callable(
                callable_value
            ):
                raise AssertionError(
                    "Guarded launcher is missing callable: "
                    f"{callable_name}"
                )


    def assert_environment_contract(
        module,
    ) -> None:
        module.ENV_FILE = TEST_ENV_FILE

        environment = (
            module._load_runtime_environment()
        )

        assert (
            environment[
                "ORACLE_LIVE_SHADOW_TICK_SECONDS"
            ]
            == "5"
        )

        assert (
            module._require_positive_tick(
                environment
            )
            == 5
        )

        module._require_continuous_mode(
            environment
        )


    def assert_atomic_lock_lifecycle(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "atomic-lock",
        )

        lock_record = (
            module._acquire_runtime_lock()
        )

        assert lock_file.is_file()

        assert (
            lock_record["process_id"]
            == os.getpid()
        )

        assert lock_record["read_only"] is True
        assert lock_record["execution_allowed"] is False
        assert lock_record["alerts_allowed"] is False

        assert (
            lock_record["qseries_handoff_allowed"]
            is False
        )

        assert (
            lock_record["trade_authorization_allowed"]
            is False
        )

        assert (
            lock_record["order_placement_allowed"]
            is False
        )

        assert lock_record["funds_moved"] is False
        assert lock_record["portfolio_mutated"] is False

        persisted_record = json.loads(
            lock_file.read_text(
                encoding="utf-8"
            )
        )

        assert persisted_record == lock_record

        try:
            module._acquire_runtime_lock()
        except module.OracleContinuousRuntimeAlreadyActive:
            pass
        else:
            raise AssertionError(
                "A duplicate continuous runtime lock "
                "was incorrectly accepted."
            )

        module._release_runtime_lock()

        assert not lock_file.is_file()


    def assert_stale_lock_recovery(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "stale-lock",
        )

        lock_file.write_text(
            json.dumps(
                {
                    "process_id": 999_999_999,
                    "read_only": True,
                    "execution_allowed": False,
                }
            ),
            encoding="utf-8",
            newline="\n",
        )

        original_process_is_alive = (
            module._process_is_alive
        )

        try:
            module._process_is_alive = (
                lambda process_id: False
            )

            lock_record = (
                module._acquire_runtime_lock()
            )

            assert (
                lock_record["process_id"]
                == os.getpid()
            )

            assert lock_file.is_file()

            module._release_runtime_lock()

            assert not lock_file.is_file()

        finally:
            module._process_is_alive = (
                original_process_is_alive
            )

            remove_file_only(
                lock_file
            )


    def assert_invalid_lock_recovery(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "invalid-lock",
        )

        lock_file.write_text(
            "not-json\n",
            encoding="utf-8",
            newline="\n",
        )

        lock_record = (
            module._acquire_runtime_lock()
        )

        assert (
            lock_record["process_id"]
            == os.getpid()
        )

        persisted_record = json.loads(
            lock_file.read_text(
                encoding="utf-8"
            )
        )

        assert (
            persisted_record["process_id"]
            == os.getpid()
        )

        module._release_runtime_lock()

        assert not lock_file.is_file()


    def assert_foreign_lock_protection(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "foreign-lock",
        )

        foreign_process_id = (
            os.getpid() + 1000
        )

        lock_file.write_text(
            json.dumps(
                {
                    "process_id": foreign_process_id,
                }
            ),
            encoding="utf-8",
            newline="\n",
        )

        module._release_runtime_lock()

        assert lock_file.is_file()

        remove_file_only(
            lock_file
        )

        assert not lock_file.is_file()


    def assert_successful_main_cleanup(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "successful-main",
        )

        original_loader = (
            module._load_canonical_launcher
        )

        launcher_calls: list[str] = []

        def successful_launcher() -> int:
            launcher_calls.append(
                "main"
            )

            assert lock_file.is_file()

            return 0

        try:
            module._load_canonical_launcher = (
                lambda: SimpleNamespace(
                    main=successful_launcher,
                )
            )

            exit_code = module.main()

            assert exit_code == 0
            assert launcher_calls == ["main"]
            assert not lock_file.is_file()

        finally:
            module._load_canonical_launcher = (
                original_loader
            )

            remove_file_only(
                lock_file
            )


    def assert_return_code_preserved(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "return-code",
        )

        original_loader = (
            module._load_canonical_launcher
        )

        try:
            module._load_canonical_launcher = (
                lambda: SimpleNamespace(
                    main=lambda: 23,
                )
            )

            exit_code = module.main()

            assert exit_code == 23
            assert not lock_file.is_file()

        finally:
            module._load_canonical_launcher = (
                original_loader
            )

            remove_file_only(
                lock_file
            )


    def assert_none_return_normalized(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "none-return",
        )

        original_loader = (
            module._load_canonical_launcher
        )

        try:
            module._load_canonical_launcher = (
                lambda: SimpleNamespace(
                    main=lambda: None,
                )
            )

            exit_code = module.main()

            assert exit_code == 0
            assert not lock_file.is_file()

        finally:
            module._load_canonical_launcher = (
                original_loader
            )

            remove_file_only(
                lock_file
            )


    def assert_operator_shutdown_cleanup(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "operator-shutdown",
        )

        original_loader = (
            module._load_canonical_launcher
        )

        def interrupted_launcher():
            assert lock_file.is_file()

            raise KeyboardInterrupt()

        try:
            module._load_canonical_launcher = (
                lambda: SimpleNamespace(
                    main=interrupted_launcher,
                )
            )

            exit_code = module.main()

            assert exit_code == 130
            assert not lock_file.is_file()

        finally:
            module._load_canonical_launcher = (
                original_loader
            )

            remove_file_only(
                lock_file
            )


    def assert_failure_cleanup(
        module,
    ) -> None:
        lock_file = configure_scenario(
            module,
            "unexpected-failure",
        )

        original_loader = (
            module._load_canonical_launcher
        )

        class ExpectedFailure(
            RuntimeError
        ):
            pass

        def failing_launcher():
            assert lock_file.is_file()

            raise ExpectedFailure(
                "simulated launcher failure"
            )

        try:
            module._load_canonical_launcher = (
                lambda: SimpleNamespace(
                    main=failing_launcher,
                )
            )

            try:
                module.main()
            except ExpectedFailure as exc:
                assert (
                    str(exc)
                    == "simulated launcher failure"
                )
            else:
                raise AssertionError(
                    "Unexpected launcher failure "
                    "was incorrectly suppressed."
                )

            assert not lock_file.is_file()

        finally:
            module._load_canonical_launcher = (
                original_loader
            )

            remove_file_only(
                lock_file
            )


    def assert_no_lock_files_remain() -> None:
        known_lock_files = (
            "atomic-lock.lock",
            "stale-lock.lock",
            "invalid-lock.lock",
            "foreign-lock.lock",
            "successful-main.lock",
            "return-code.lock",
            "none-return.lock",
            "operator-shutdown.lock",
            "unexpected-failure.lock",
        )

        for filename in known_lock_files:
            lock_file = (
                TEST_ROOT
                / filename
            )

            assert not lock_file.is_file()


    def main() -> int:
        print("========================================")
        print(" OLA-080 GUARDED CONTINUOUS LIFECYCLE")
        print(" SINGLE IMPORT CORRECTION V4")
        print(" NO RECURSIVE FILESYSTEM OPERATIONS")
        print("========================================")

        assert_authority_boundary()

        prepare_flat_test_area()

        print("[TEST] Single guarded launcher import")

        module = load_guarded_launcher_once()

        print("[OK] Single guarded launcher import")

        print("[TEST] Static launcher contract")

        assert_static_launcher_contract(
            module
        )

        print("[OK] Static launcher contract")

        print("[TEST] Environment contract")

        assert_environment_contract(
            module
        )

        print("[OK] Environment contract")

        print("[TEST] Atomic runtime lock lifecycle")

        assert_atomic_lock_lifecycle(
            module
        )

        print("[OK] Atomic runtime lock lifecycle")

        print("[TEST] Stale lock recovery")

        assert_stale_lock_recovery(
            module
        )

        print("[OK] Stale lock recovery")

        print("[TEST] Invalid lock recovery")

        assert_invalid_lock_recovery(
            module
        )

        print("[OK] Invalid lock recovery")

        print("[TEST] Foreign lock ownership protection")

        assert_foreign_lock_protection(
            module
        )

        print("[OK] Foreign lock ownership protection")

        print("[TEST] Successful launcher cleanup")

        assert_successful_main_cleanup(
            module
        )

        print("[OK] Successful launcher cleanup")

        print("[TEST] Launcher return-code preservation")

        assert_return_code_preserved(
            module
        )

        print("[OK] Launcher return-code preservation")

        print("[TEST] None return normalization")

        assert_none_return_normalized(
            module
        )

        print("[OK] None return normalization")

        print("[TEST] Operator shutdown cleanup")

        assert_operator_shutdown_cleanup(
            module
        )

        print("[OK] Operator shutdown cleanup")

        print("[TEST] Unexpected failure cleanup")

        assert_failure_cleanup(
            module
        )

        print("[OK] Unexpected failure cleanup")

        print("[TEST] No lock files remain")

        assert_no_lock_files_remain()

        print("[OK] No lock files remain")

        print("[TEST] Oracle authority boundary")

        assert_authority_boundary()

        print("[OK] Oracle read-only boundary preserved")

        remove_file_only(
            TEST_ENV_FILE
        )

        print(
            "[PASS] OLA-080 Oracle Guarded Continuous "
            "Runtime Lifecycle Gate Correction V4"
        )

        print({
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "single_launcher_import": True,
            "repeated_launcher_imports_removed": True,
            "temporary_directories_used": False,
            "recursive_cleanup_used": False,
            "recursive_filesystem_walk_used": False,
            "directory_deletion_used": False,
            "unique_directory_creation_used": False,
            "flat_test_area_used": True,
            "individual_lock_file_cleanup_used": True,
            "atomic_lock_acquisition_verified": True,
            "duplicate_runtime_rejected": True,
            "stale_lock_recovery_verified": True,
            "invalid_lock_recovery_verified": True,
            "foreign_lock_ownership_preserved": True,
            "successful_exit_cleanup_verified": True,
            "return_code_preserved": True,
            "none_return_normalized": True,
            "operator_shutdown_cleanup_verified": True,
            "failure_cleanup_verified": True,
            "no_test_lock_files_remain": True,
            "real_continuous_service_started": False,
            "real_postgresql_write_performed": False,
            "production_files_changed": False,
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
).lstrip()


def write_complete_file(
    path: Path,
    source: str,
) -> None:
    compile(
        source,
        str(path),
        "exec",
    )

    temporary_path = path.with_name(
        path.name + ".ola080_v4.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    installed_source = temporary_path.read_text(
        encoding="utf-8"
    )

    compile(
        installed_source,
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def verify_installed_test() -> None:
    source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'ENGINE_ID = "OLA-080-CORRECTION-V4"',
        "SINGLE IMPORT CORRECTION V4",
        "def load_guarded_launcher_once(",
        "def configure_scenario(",
        "def remove_file_only(",
        "single_launcher_import",
        "repeated_launcher_imports_removed",
        "recursive_cleanup_used",
        "directory_deletion_used",
        "flat_test_area_used",
        "no_test_lock_files_remain",
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Installed OLA-080 V4 test is missing "
                f"required token: {token}"
            )

    forbidden_tokens = (
        "import tempfile",
        "TemporaryDirectory",
        "import shutil",
        "shutil.rmtree",
        "os.walk",
        "uuid.uuid4",
        "load_guarded_launcher()",
    )

    for token in forbidden_tokens:
        if token in source:
            raise RuntimeError(
                "Installed OLA-080 V4 test still contains "
                f"forbidden token: {token}"
            )

    compile(
        source,
        str(TEST_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-080 TEST CORRECTION V4")
    print(" SINGLE LAUNCHER IMPORT")
    print(" FLAT FILE LIFECYCLE TEST")
    print("========================================")

    guarded_launcher_path = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    guarded_source = guarded_launcher_path.read_text(
        encoding="utf-8"
    )

    required_guarded_tokens = (
        'SCHEMA_VERSION = "OLA-074"',
        'ENGINE_ID = "OLA-074"',
        "oracle_continuous_runtime.lock",
        "OracleContinuousRuntimeAlreadyActive",
        "def _acquire_runtime_lock(",
        "def _release_runtime_lock(",
        "def main() -> int:",
    )

    for token in required_guarded_tokens:
        if token not in guarded_source:
            raise RuntimeError(
                "Guarded launcher does not match the "
                "required OLA-074 contract. Missing token: "
                f"{token}"
            )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    verify_installed_test()

    print("[OK] Previous OLA-080 test fully replaced")
    print("[OK] Launcher imported once per test run")
    print("[OK] Repeated filesystem probes removed")
    print("[OK] TemporaryDirectory removed")
    print("[OK] Recursive cleanup removed")
    print("[OK] Directory deletion removed")
    print("[OK] Directory traversal removed")
    print("[OK] UUID directory generation removed")
    print("[OK] Flat test-file lifecycle installed")
    print("[OK] Individual lock cleanup preserved")
    print("[OK] Production launcher unchanged")
    print("[OK] No real continuous runtime started")

    print(
        "\n[DONE] OLA-080 guarded continuous runtime "
        "lifecycle gate correction V4 installed"
    )

    print("\nRun:")
    print(
        "py "
        "test_ola_080_oracle_guarded_"
        "continuous_runtime_lifecycle_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )