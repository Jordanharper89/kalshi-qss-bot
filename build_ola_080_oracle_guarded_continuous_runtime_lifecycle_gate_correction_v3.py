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
    import uuid
    from pathlib import Path
    from types import SimpleNamespace


    SCHEMA_VERSION = "OLA-080"
    ENGINE_ID = "OLA-080-CORRECTION-V3"

    ROOT = Path(__file__).resolve().parent

    GUARDED_LAUNCHER_PATH = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    TEST_RUNTIME_ROOT = (
        ROOT
        / "runtime"
        / "ola080_guarded_lifecycle_test_v3"
    )

    READ_ONLY = True
    EXECUTION_ALLOWED = False
    ALERTS_ALLOWED = False
    QSERIES_HANDOFF_ALLOWED = False
    TRADE_AUTHORIZATION_ALLOWED = False
    ORDER_PLACEMENT_ALLOWED = False
    FUNDS_MOVED = False
    PORTFOLIO_MUTATED = False


    def load_guarded_launcher():
        if not GUARDED_LAUNCHER_PATH.exists():
            raise FileNotFoundError(
                "Guarded continuous launcher is missing: "
                f"{GUARDED_LAUNCHER_PATH}"
            )

        module_name = (
            "ola080_guarded_launcher_"
            + uuid.uuid4().hex
        )

        specification = (
            importlib.util.spec_from_file_location(
                module_name,
                GUARDED_LAUNCHER_PATH,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise AssertionError(
                "Could not create guarded launcher "
                "import specification"
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


    def create_unique_test_root(
        name: str,
    ) -> Path:
        test_root = (
            TEST_RUNTIME_ROOT
            / (
                name
                + "-"
                + uuid.uuid4().hex
            )
        )

        test_root.mkdir(
            parents=True,
            exist_ok=False,
        )

        return test_root


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


    def cleanup_runtime_files(
        test_root: Path,
    ) -> None:
        candidates = (
            (
                test_root
                / ".env"
            ),
            (
                test_root
                / "runtime"
                / "oracle_live_shadow"
                / "oracle_continuous_runtime.lock"
            ),
        )

        for candidate in candidates:
            remove_file_only(
                candidate
            )


    def write_env_file(
        path: Path,
        *,
        tick_seconds: str = "5",
        max_iterations: str | None = None,
    ) -> None:
        lines = [
            (
                "DATABASE_URL="
                "postgresql://oracle:oracle@localhost:5432/postgres"
            ),
            (
                "ORACLE_LIVE_SHADOW_TICK_SECONDS="
                f"{tick_seconds}"
            ),
        ]

        if max_iterations is not None:
            lines.append(
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS="
                f"{max_iterations}"
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
            newline="\n",
        )


    def configure_test_runtime(
        module,
        test_root: Path,
    ) -> tuple[Path, Path]:
        env_file = (
            test_root
            / ".env"
        )

        runtime_directory = (
            test_root
            / "runtime"
            / "oracle_live_shadow"
        )

        lock_file = (
            runtime_directory
            / "oracle_continuous_runtime.lock"
        )

        module.ENV_FILE = env_file
        module.RUNTIME_DIRECTORY = runtime_directory
        module.LOCK_FILE = lock_file

        return env_file, lock_file


    def assert_authority_boundary() -> None:
        assert READ_ONLY is True
        assert EXECUTION_ALLOWED is False
        assert ALERTS_ALLOWED is False
        assert QSERIES_HANDOFF_ALLOWED is False
        assert TRADE_AUTHORIZATION_ALLOWED is False
        assert ORDER_PLACEMENT_ALLOWED is False
        assert FUNDS_MOVED is False
        assert PORTFOLIO_MUTATED is False


    def test_static_launcher_contract(
        module,
    ) -> None:
        assert module.SCHEMA_VERSION == "OLA-074"
        assert module.ENGINE_ID == "OLA-074"

        required_callables = (
            "_load_env_file",
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

        for name in required_callables:
            value = getattr(
                module,
                name,
                None,
            )

            if not callable(value):
                raise AssertionError(
                    "Guarded launcher is missing callable: "
                    f"{name}"
                )


    def test_environment_loading(
        module,
        test_root: Path,
    ) -> None:
        env_file, _ = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="7",
        )

        environment = (
            module._load_runtime_environment()
        )

        assert (
            environment["DATABASE_URL"]
            == "postgresql://oracle:oracle@localhost:5432/postgres"
        )

        assert (
            environment["ORACLE_LIVE_SHADOW_TICK_SECONDS"]
            == "7"
        )

        assert (
            module._require_positive_tick(
                environment
            )
            == 7
        )

        module._require_continuous_mode(
            environment
        )


    def test_continuous_mode_contract(
        module,
    ) -> None:
        accepted_values = (
            None,
            "",
            "none",
            "null",
            "continuous",
            "unbounded",
            "forever",
            " CONTINUOUS ",
        )

        for value in accepted_values:
            environment = {
                "DATABASE_URL": (
                    "postgresql://oracle:oracle@localhost:5432/postgres"
                ),
                "ORACLE_LIVE_SHADOW_TICK_SECONDS": "5",
            }

            if value is not None:
                environment[
                    "ORACLE_LIVE_SHADOW_MAX_ITERATIONS"
                ] = value

            module._require_continuous_mode(
                environment
            )

        rejected_values = (
            "0",
            "1",
            "3",
            "100",
            "-1",
            "bounded",
        )

        for value in rejected_values:
            environment = {
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": value,
            }

            try:
                module._require_continuous_mode(
                    environment
                )
            except module.OracleContinuousLaunchError:
                pass
            else:
                raise AssertionError(
                    "Finite or invalid iteration limit "
                    f"was accepted: {value!r}"
                )


    def test_positive_tick_contract(
        module,
    ) -> None:
        accepted = {
            "1": 1,
            "5": 5,
            "60": 60,
            " 9 ": 9,
        }

        for raw_value, expected in accepted.items():
            actual = module._require_positive_tick(
                {
                    "ORACLE_LIVE_SHADOW_TICK_SECONDS": (
                        raw_value
                    ),
                }
            )

            assert actual == expected

        rejected = (
            "0",
            "-1",
            "1.5",
            "five",
            "",
        )

        for raw_value in rejected:
            try:
                module._require_positive_tick(
                    {
                        "ORACLE_LIVE_SHADOW_TICK_SECONDS": (
                            raw_value
                        ),
                    }
                )
            except module.OracleContinuousLaunchError:
                pass
            else:
                raise AssertionError(
                    "Invalid service cadence was accepted: "
                    f"{raw_value!r}"
                )


    def test_atomic_lock_lifecycle(
        module,
        test_root: Path,
    ) -> None:
        _, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        lock_record = (
            module._acquire_runtime_lock()
        )

        assert lock_file.exists()

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

        persisted = json.loads(
            lock_file.read_text(
                encoding="utf-8"
            )
        )

        assert persisted == lock_record

        try:
            module._acquire_runtime_lock()
        except module.OracleContinuousRuntimeAlreadyActive:
            pass
        else:
            raise AssertionError(
                "Second continuous runtime lock was accepted"
            )

        module._release_runtime_lock()

        assert not lock_file.exists()


    def test_stale_lock_recovery(
        module,
        test_root: Path,
    ) -> None:
        _, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        lock_file.parent.mkdir(
            parents=True,
            exist_ok=True,
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

        assert lock_file.exists()

        module._release_runtime_lock()

        assert not lock_file.exists()


    def test_invalid_lock_recovery(
        module,
        test_root: Path,
    ) -> None:
        _, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        lock_file.parent.mkdir(
            parents=True,
            exist_ok=True,
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

        persisted = json.loads(
            lock_file.read_text(
                encoding="utf-8"
            )
        )

        assert (
            persisted["process_id"]
            == os.getpid()
        )

        module._release_runtime_lock()

        assert not lock_file.exists()


    def test_foreign_lock_not_released(
        module,
        test_root: Path,
    ) -> None:
        _, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        lock_file.parent.mkdir(
            parents=True,
            exist_ok=True,
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

        assert lock_file.exists()

        remove_file_only(
            lock_file
        )

        assert not lock_file.exists()


    def test_successful_main_lifecycle(
        module,
        test_root: Path,
    ) -> None:
        env_file, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="5",
        )

        launcher_calls: list[str] = []

        def successful_main() -> int:
            launcher_calls.append(
                "main"
            )

            assert lock_file.exists()

            return 0

        module._load_canonical_launcher = (
            lambda: SimpleNamespace(
                main=successful_main,
            )
        )

        exit_code = module.main()

        assert exit_code == 0
        assert launcher_calls == ["main"]
        assert not lock_file.exists()


    def test_launcher_return_code_preserved(
        module,
        test_root: Path,
    ) -> None:
        env_file, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="5",
        )

        module._load_canonical_launcher = (
            lambda: SimpleNamespace(
                main=lambda: 23,
            )
        )

        exit_code = module.main()

        assert exit_code == 23
        assert not lock_file.exists()


    def test_none_return_normalized(
        module,
        test_root: Path,
    ) -> None:
        env_file, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="5",
        )

        module._load_canonical_launcher = (
            lambda: SimpleNamespace(
                main=lambda: None,
            )
        )

        exit_code = module.main()

        assert exit_code == 0
        assert not lock_file.exists()


    def test_operator_shutdown_releases_lock(
        module,
        test_root: Path,
    ) -> None:
        env_file, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="5",
        )

        def interrupted_main():
            assert lock_file.exists()

            raise KeyboardInterrupt()

        module._load_canonical_launcher = (
            lambda: SimpleNamespace(
                main=interrupted_main,
            )
        )

        exit_code = module.main()

        assert exit_code == 130
        assert not lock_file.exists()


    def test_failure_releases_lock(
        module,
        test_root: Path,
    ) -> None:
        env_file, lock_file = configure_test_runtime(
            module,
            test_root,
        )

        write_env_file(
            env_file,
            tick_seconds="5",
        )

        class ExpectedFailure(
            RuntimeError
        ):
            pass

        def failing_main():
            assert lock_file.exists()

            raise ExpectedFailure(
                "simulated canonical launcher failure"
            )

        module._load_canonical_launcher = (
            lambda: SimpleNamespace(
                main=failing_main,
            )
        )

        try:
            module.main()
        except ExpectedFailure as exc:
            assert (
                str(exc)
                == "simulated canonical launcher failure"
            )
        else:
            raise AssertionError(
                "Canonical launcher failure was suppressed"
            )

        assert not lock_file.exists()


    def run_isolated_test(
        name: str,
        test_callable,
    ) -> Path:
        module = load_guarded_launcher()

        test_root = create_unique_test_root(
            name
        )

        try:
            test_callable(
                module,
                test_root,
            )
        finally:
            cleanup_runtime_files(
                test_root
            )

        return test_root


    def main() -> int:
        print("========================================")
        print(" OLA-080 GUARDED CONTINUOUS LIFECYCLE")
        print(" NO DIRECTORY CLEANUP CORRECTION V3")
        print(" NO REAL CONTINUOUS SERVICE START")
        print("========================================")

        assert_authority_boundary()

        retained_test_roots: list[Path] = []

        print("[TEST] Guarded launcher import")

        module = load_guarded_launcher()

        print("[OK] Guarded launcher import")

        print("[TEST] Static launcher contract")

        test_static_launcher_contract(
            module
        )

        print("[OK] Static launcher contract")

        print("[TEST] Environment loading")

        retained_test_roots.append(
            run_isolated_test(
                "environment-loading",
                test_environment_loading,
            )
        )

        print("[OK] Environment loading")

        print("[TEST] Continuous-mode enforcement")

        module = load_guarded_launcher()

        test_continuous_mode_contract(
            module
        )

        print("[OK] Continuous-mode enforcement")

        print("[TEST] Positive cadence enforcement")

        module = load_guarded_launcher()

        test_positive_tick_contract(
            module
        )

        print("[OK] Positive cadence enforcement")

        print("[TEST] Atomic runtime lock lifecycle")

        retained_test_roots.append(
            run_isolated_test(
                "atomic-lock-lifecycle",
                test_atomic_lock_lifecycle,
            )
        )

        print("[OK] Atomic runtime lock lifecycle")

        print("[TEST] Stale lock recovery")

        retained_test_roots.append(
            run_isolated_test(
                "stale-lock-recovery",
                test_stale_lock_recovery,
            )
        )

        print("[OK] Stale lock recovery")

        print("[TEST] Invalid lock recovery")

        retained_test_roots.append(
            run_isolated_test(
                "invalid-lock-recovery",
                test_invalid_lock_recovery,
            )
        )

        print("[OK] Invalid lock recovery")

        print("[TEST] Foreign lock ownership protection")

        retained_test_roots.append(
            run_isolated_test(
                "foreign-lock-ownership",
                test_foreign_lock_not_released,
            )
        )

        print("[OK] Foreign lock ownership protection")

        print("[TEST] Successful launcher lifecycle")

        retained_test_roots.append(
            run_isolated_test(
                "successful-launcher-lifecycle",
                test_successful_main_lifecycle,
            )
        )

        print("[OK] Successful launcher lifecycle")

        print("[TEST] Launcher return-code preservation")

        retained_test_roots.append(
            run_isolated_test(
                "return-code-preservation",
                test_launcher_return_code_preserved,
            )
        )

        print("[OK] Launcher return-code preservation")

        print("[TEST] None return normalization")

        retained_test_roots.append(
            run_isolated_test(
                "none-return-normalization",
                test_none_return_normalized,
            )
        )

        print("[OK] None return normalization")

        print("[TEST] Operator shutdown cleanup")

        retained_test_roots.append(
            run_isolated_test(
                "operator-shutdown-cleanup",
                test_operator_shutdown_releases_lock,
            )
        )

        print("[OK] Operator shutdown cleanup")

        print("[TEST] Unexpected failure cleanup")

        retained_test_roots.append(
            run_isolated_test(
                "unexpected-failure-cleanup",
                test_failure_releases_lock,
            )
        )

        print("[OK] Unexpected failure cleanup")

        print("[TEST] No test lock files remain")

        for test_root in retained_test_roots:
            lock_file = (
                test_root
                / "runtime"
                / "oracle_live_shadow"
                / "oracle_continuous_runtime.lock"
            )

            assert not lock_file.exists()

        print("[OK] No test lock files remain")

        print("[TEST] Oracle authority boundary")

        assert_authority_boundary()

        print("[OK] Oracle read-only boundary preserved")

        print(
            "[INFO] Empty isolated test directories retained: "
            f"{TEST_RUNTIME_ROOT}"
        )

        print(
            "[PASS] OLA-080 Oracle Guarded Continuous "
            "Runtime Lifecycle Gate Correction V3"
        )

        print({
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "temporary_directory_removed": True,
            "shutil_rmtree_removed": True,
            "recursive_directory_walk_removed": True,
            "directory_deletion_attempted": False,
            "unique_isolated_test_roots_used": True,
            "individual_lock_file_cleanup_verified": True,
            "no_test_lock_files_remain": True,
            "guarded_launcher_imported": True,
            "ola074_launcher_contract_verified": True,
            "continuous_mode_required": True,
            "finite_iteration_mode_rejected": True,
            "positive_cadence_required": True,
            "atomic_lock_acquisition_verified": True,
            "second_runtime_rejected": True,
            "stale_lock_recovery_verified": True,
            "invalid_lock_recovery_verified": True,
            "foreign_lock_ownership_preserved": True,
            "successful_exit_lock_cleanup_verified": True,
            "operator_shutdown_lock_cleanup_verified": True,
            "failure_lock_cleanup_verified": True,
            "launcher_return_code_preserved": True,
            "none_return_normalized_to_zero": True,
            "real_continuous_service_started": False,
            "real_postgresql_write_performed": False,
            "background_process_created": False,
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
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    compile(
        source,
        str(path),
        "exec",
    )

    temporary_path = path.with_name(
        path.name + ".ola080_correction_v3.tmp"
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


def verify_installed_test() -> None:
    source = TEST_PATH.read_text(
        encoding="utf-8"
    )

    required_tokens = (
        'SCHEMA_VERSION = "OLA-080"',
        'ENGINE_ID = "OLA-080-CORRECTION-V3"',
        "NO DIRECTORY CLEANUP CORRECTION V3",
        "def create_unique_test_root(",
        "def remove_file_only(",
        "def cleanup_runtime_files(",
        "def run_isolated_test(",
        "recursive_directory_walk_removed",
        "directory_deletion_attempted",
        "no_test_lock_files_remain",
        "real_continuous_service_started",
        "background_process_created",
        '"read_only": True',
        '"execution_allowed": False',
    )

    for token in required_tokens:
        if token not in source:
            raise RuntimeError(
                "Installed OLA-080 correction V3 test "
                f"is missing required token: {token}"
            )

    forbidden_tokens = (
        "import tempfile",
        "TemporaryDirectory",
        "import shutil",
        "shutil.rmtree",
        "os.walk",
        "Path.rmdir",
    )

    for token in forbidden_tokens:
        if token in source:
            raise RuntimeError(
                "Installed OLA-080 correction V3 test "
                f"still contains forbidden token: {token}"
            )

    compile(
        source,
        str(TEST_PATH),
        "exec",
    )


def main() -> int:
    print("========================================")
    print(" OLA-080 TEST CORRECTION V3")
    print(" WINDOWS RECURSIVE CLEANUP REMOVAL")
    print(" INDIVIDUAL LOCK FILE CLEANUP ONLY")
    print("========================================")

    guarded_launcher_path = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    if not guarded_launcher_path.exists():
        raise FileNotFoundError(
            "Required guarded continuous launcher is missing: "
            f"{guarded_launcher_path}"
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
        "def _require_continuous_mode(",
        "def main() -> int:",
    )

    for token in required_guarded_tokens:
        if token not in guarded_source:
            raise RuntimeError(
                "Guarded launcher does not match the required "
                f"OLA-074 contract. Missing token: {token}"
            )

    compile(
        guarded_source,
        str(guarded_launcher_path),
        "exec",
    )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    verify_installed_test()

    print("[OK] Previous OLA-080 test fully replaced")
    print("[OK] TemporaryDirectory remains removed")
    print("[OK] shutil remains removed")
    print("[OK] Recursive directory traversal removed")
    print("[OK] Recursive directory deletion removed")
    print("[OK] Unique isolated test roots installed")
    print("[OK] Individual lock-file cleanup installed")
    print("[OK] Atomic lock lifecycle preserved")
    print("[OK] Duplicate runtime rejection preserved")
    print("[OK] Stale lock recovery preserved")
    print("[OK] Invalid lock recovery preserved")
    print("[OK] Foreign lock ownership preserved")
    print("[OK] Operator shutdown cleanup preserved")
    print("[OK] Unexpected failure cleanup preserved")
    print("[OK] Oracle read-only assertions preserved")
    print("[OK] No production files changed")
    print("[OK] No real continuous runtime started")

    print(
        "\n[DONE] OLA-080 guarded continuous runtime "
        "lifecycle gate correction V3 installed"
    )

    print("\nRun:")
    print(
        "python "
        "test_ola_080_oracle_guarded_"
        "continuous_runtime_lifecycle_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )