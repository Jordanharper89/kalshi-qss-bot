from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

MODULE_FILE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_continuous_operator_launch_readiness_gate.py"
)

TEST_FILE = (
    ROOT
    / "test_ola_076_oracle_continuous_operator_launch_readiness_gate.py"
)


MODULE_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import json
    import os
    import sys
    from dataclasses import asdict, dataclass
    from pathlib import Path
    from types import ModuleType
    from typing import Mapping


    SCHEMA_VERSION = "OLA-076"
    ENGINE_ID = "OLA-076"

    READ_ONLY = True
    EXECUTION_ALLOWED = False
    ORDER_PLACEMENT_ALLOWED = False
    FUNDS_MOVEMENT_ALLOWED = False
    PORTFOLIO_MUTATION_ALLOWED = False

    REQUIRED_OPERATOR_SCHEMA_VERSION = "OLA-075"
    REQUIRED_OPERATOR_ENGINE_ID = "OLA-075"

    REQUIRED_GUARDED_SCHEMA_VERSION = "OLA-074"
    REQUIRED_GUARDED_ENGINE_ID = "OLA-074"

    REQUIRED_OPERATOR_COMMAND = (
        "py run_oracle_live_shadow_CONTINUOUS.py"
    )

    DEFAULT_TICK_SECONDS = 5

    ROOT = Path(__file__).resolve().parents[3]

    ENV_FILE = ROOT / ".env"

    OPERATOR_ENTRY_POINT_FILE = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS.py"
    )

    GUARDED_LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
    )

    RUNTIME_DIRECTORY = (
        ROOT
        / "runtime"
        / "oracle_live_shadow"
    )

    RUNTIME_LOCK_FILE = (
        RUNTIME_DIRECTORY
        / "oracle_continuous_runtime.lock"
    )


    class OracleContinuousLaunchReadinessError(
        RuntimeError
    ):
        pass


    class OracleContinuousDependencyError(
        OracleContinuousLaunchReadinessError
    ):
        pass


    class OracleContinuousConfigurationError(
        OracleContinuousLaunchReadinessError
    ):
        pass


    class OracleContinuousRuntimeConflictError(
        OracleContinuousLaunchReadinessError
    ):
        pass


    @dataclass(frozen=True)
    class OracleContinuousLaunchReadinessRecord:
        schema_version: str
        engine_id: str
        status: str
        ready: bool

        operator_entry_point_verified: bool
        guarded_launcher_verified: bool
        exact_dependency_chain_verified: bool

        environment_file_present: bool
        postgresql_configuration_present: bool
        continuous_mode_verified: bool
        positive_tick_verified: bool

        runtime_directory_ready: bool
        runtime_lock_present: bool
        runtime_conflict_detected: bool
        stale_lock_detected: bool

        canonical_operator_command: str

        read_only: bool
        execution_allowed: bool
        order_placement_allowed: bool
        funds_movement_allowed: bool
        portfolio_mutation_allowed: bool

        def to_dict(self) -> dict[str, object]:
            return asdict(self)


    def _load_module_from_path(
        path: Path,
        module_name: str,
    ) -> ModuleType:
        """
        Python 3.14-safe dynamic module loading.

        Dataclass processing resolves annotations through
        sys.modules[cls.__module__]. The module must therefore be
        registered before exec_module() runs.
        """

        if not path.is_file():
            raise OracleContinuousDependencyError(
                f"Required Oracle file not found: {path}"
            )

        specification = (
            importlib.util.spec_from_file_location(
                module_name,
                path,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise OracleContinuousDependencyError(
                "Could not create module specification "
                f"for {path}"
            )

        module = importlib.util.module_from_spec(
            specification
        )

        previous_module = sys.modules.get(
            module_name
        )

        sys.modules[module_name] = module

        try:
            specification.loader.exec_module(
                module
            )

        except BaseException:
            if previous_module is None:
                sys.modules.pop(
                    module_name,
                    None,
                )
            else:
                sys.modules[module_name] = (
                    previous_module
                )

            raise

        return module


    def _validate_module_contract(
        module: ModuleType,
        *,
        expected_schema_version: str,
        expected_engine_id: str,
        dependency_name: str,
    ) -> None:
        actual_schema_version = getattr(
            module,
            "SCHEMA_VERSION",
            None,
        )

        actual_engine_id = getattr(
            module,
            "ENGINE_ID",
            None,
        )

        if (
            actual_schema_version
            != expected_schema_version
        ):
            raise OracleContinuousDependencyError(
                f"{dependency_name} schema mismatch. "
                f"Expected {expected_schema_version}, "
                f"received {actual_schema_version!r}"
            )

        if actual_engine_id != expected_engine_id:
            raise OracleContinuousDependencyError(
                f"{dependency_name} engine mismatch. "
                f"Expected {expected_engine_id}, "
                f"received {actual_engine_id!r}"
            )

        if not callable(
            getattr(
                module,
                "main",
                None,
            )
        ):
            raise OracleContinuousDependencyError(
                f"{dependency_name} does not expose "
                "callable main()"
            )

        if getattr(
            module,
            "READ_ONLY",
            True,
        ) is not True:
            raise OracleContinuousDependencyError(
                f"{dependency_name} is not read-only"
            )

        if getattr(
            module,
            "EXECUTION_ALLOWED",
            False,
        ) is not False:
            raise OracleContinuousDependencyError(
                f"{dependency_name} permits execution"
            )


    def _parse_environment_file(
        path: Path,
    ) -> dict[str, str]:
        if not path.is_file():
            raise OracleContinuousConfigurationError(
                f"Environment file not found: {path}"
            )

        values: dict[str, str] = {}

        for raw_line in path.read_text(
            encoding="utf-8",
        ).splitlines():
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue

            key, value = line.split(
                "=",
                1,
            )

            key = key.strip()
            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in {"'", '"'}
            ):
                value = value[1:-1]

            if key:
                values[key] = value

        return values


    def _merged_environment(
        file_values: Mapping[str, str],
        process_environment: Mapping[str, str],
    ) -> dict[str, str]:
        merged = dict(
            file_values
        )

        for key, value in process_environment.items():
            if value:
                merged[key] = value

        return merged


    def _postgresql_configuration_present(
        environment: Mapping[str, str],
    ) -> bool:
        database_url = environment.get(
            "DATABASE_URL",
            "",
        ).strip()

        if database_url:
            return True

        host = environment.get(
            "ORACLE_POSTGRES_HOST",
            environment.get(
                "PGHOST",
                "",
            ),
        ).strip()

        port = environment.get(
            "ORACLE_POSTGRES_PORT",
            environment.get(
                "PGPORT",
                "",
            ),
        ).strip()

        database = environment.get(
            "ORACLE_POSTGRES_DATABASE",
            environment.get(
                "PGDATABASE",
                "",
            ),
        ).strip()

        username = environment.get(
            "ORACLE_POSTGRES_USERNAME",
            environment.get(
                "PGUSER",
                "",
            ),
        ).strip()

        password = environment.get(
            "ORACLE_POSTGRES_PASSWORD",
            environment.get(
                "PGPASSWORD",
                "",
            ),
        ).strip()

        return all(
            (
                host,
                port,
                database,
                username,
                password,
            )
        )


    def _require_continuous_mode(
        environment: Mapping[str, str],
    ) -> None:
        value = environment.get(
            "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
            "",
        ).strip().lower()

        accepted = {
            "",
            "none",
            "null",
            "continuous",
            "unbounded",
            "forever",
        }

        if value not in accepted:
            raise OracleContinuousConfigurationError(
                "Oracle continuous runtime requires an "
                "unbounded iteration configuration. "
                "Received "
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS="
                f"{value!r}"
            )


    def _require_positive_tick(
        environment: Mapping[str, str],
    ) -> int:
        value = environment.get(
            "ORACLE_LIVE_SHADOW_TICK_SECONDS",
            str(DEFAULT_TICK_SECONDS),
        ).strip()

        try:
            tick_seconds = int(
                value
            )

        except ValueError as exc:
            raise OracleContinuousConfigurationError(
                "ORACLE_LIVE_SHADOW_TICK_SECONDS must "
                f"be an integer. Received {value!r}"
            ) from exc

        if tick_seconds <= 0:
            raise OracleContinuousConfigurationError(
                "ORACLE_LIVE_SHADOW_TICK_SECONDS must "
                "be greater than zero"
            )

        return tick_seconds


    def _process_is_alive(
        process_id: int,
    ) -> bool:
        if process_id <= 0:
            return False

        if process_id == os.getpid():
            return True

        try:
            os.kill(
                process_id,
                0,
            )

        except ProcessLookupError:
            return False

        except PermissionError:
            return True

        except OSError:
            return False

        return True


    def _inspect_runtime_lock(
        lock_file: Path,
    ) -> tuple[bool, bool, bool]:
        if not lock_file.is_file():
            return (
                False,
                False,
                False,
            )

        try:
            payload = json.loads(
                lock_file.read_text(
                    encoding="utf-8",
                )
            )

        except Exception:
            return (
                True,
                False,
                True,
            )

        try:
            process_id = int(
                payload.get(
                    "process_id",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return (
                True,
                False,
                True,
            )

        if _process_is_alive(
            process_id
        ):
            return (
                True,
                True,
                False,
            )

        return (
            True,
            False,
            True,
        )


    def _validate_read_only_boundary() -> None:
        if READ_ONLY is not True:
            raise OracleContinuousLaunchReadinessError(
                "OLA-076 must remain read-only"
            )

        forbidden_flags = {
            "execution_allowed": EXECUTION_ALLOWED,
            "order_placement_allowed": (
                ORDER_PLACEMENT_ALLOWED
            ),
            "funds_movement_allowed": (
                FUNDS_MOVEMENT_ALLOWED
            ),
            "portfolio_mutation_allowed": (
                PORTFOLIO_MUTATION_ALLOWED
            ),
        }

        enabled_flags = tuple(
            name
            for name, value in forbidden_flags.items()
            if value is not False
        )

        if enabled_flags:
            raise OracleContinuousLaunchReadinessError(
                "Oracle execution boundary violation: "
                f"{enabled_flags}"
            )


    def evaluate_launch_readiness(
        *,
        root: Path = ROOT,
        env_file: Path | None = None,
        operator_entry_point_file: Path | None = None,
        guarded_launcher_file: Path | None = None,
        runtime_directory: Path | None = None,
        runtime_lock_file: Path | None = None,
        process_environment: Mapping[
            str,
            str,
        ] | None = None,
    ) -> OracleContinuousLaunchReadinessRecord:
        _validate_read_only_boundary()

        resolved_env_file = (
            env_file
            if env_file is not None
            else root / ".env"
        )

        resolved_operator_file = (
            operator_entry_point_file
            if operator_entry_point_file is not None
            else (
                root
                / "run_oracle_live_shadow_CONTINUOUS.py"
            )
        )

        resolved_guarded_file = (
            guarded_launcher_file
            if guarded_launcher_file is not None
            else (
                root
                / "run_oracle_live_shadow_"
                "CONTINUOUS_GUARDED.py"
            )
        )

        resolved_runtime_directory = (
            runtime_directory
            if runtime_directory is not None
            else (
                root
                / "runtime"
                / "oracle_live_shadow"
            )
        )

        resolved_lock_file = (
            runtime_lock_file
            if runtime_lock_file is not None
            else (
                resolved_runtime_directory
                / "oracle_continuous_runtime.lock"
            )
        )

        operator_module = _load_module_from_path(
            resolved_operator_file,
            "ola076_required_ola075_operator",
        )

        _validate_module_contract(
            operator_module,
            expected_schema_version=(
                REQUIRED_OPERATOR_SCHEMA_VERSION
            ),
            expected_engine_id=(
                REQUIRED_OPERATOR_ENGINE_ID
            ),
            dependency_name=(
                "OLA-075 operator entry point"
            ),
        )

        guarded_module = _load_module_from_path(
            resolved_guarded_file,
            "ola076_required_ola074_guarded",
        )

        _validate_module_contract(
            guarded_module,
            expected_schema_version=(
                REQUIRED_GUARDED_SCHEMA_VERSION
            ),
            expected_engine_id=(
                REQUIRED_GUARDED_ENGINE_ID
            ),
            dependency_name=(
                "OLA-074 guarded launcher"
            ),
        )

        file_environment = _parse_environment_file(
            resolved_env_file
        )

        environment = _merged_environment(
            file_environment,
            (
                process_environment
                if process_environment is not None
                else os.environ
            ),
        )

        if not _postgresql_configuration_present(
            environment
        ):
            raise OracleContinuousConfigurationError(
                "PostgreSQL configuration is missing. "
                "Provide DATABASE_URL or the complete "
                "Oracle PostgreSQL field set."
            )

        _require_continuous_mode(
            environment
        )

        tick_seconds = _require_positive_tick(
            environment
        )

        resolved_runtime_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_probe = (
            resolved_runtime_directory
            / ".ola076_write_probe"
        )

        try:
            write_probe.write_text(
                "OLA-076",
                encoding="utf-8",
            )

            observed = write_probe.read_text(
                encoding="utf-8",
            )

            if observed != "OLA-076":
                raise OracleContinuousLaunchReadinessError(
                    "Runtime directory write probe "
                    "could not be verified"
                )

        finally:
            write_probe.unlink(
                missing_ok=True
            )

        (
            lock_present,
            runtime_conflict,
            stale_lock,
        ) = _inspect_runtime_lock(
            resolved_lock_file
        )

        if runtime_conflict:
            raise OracleContinuousRuntimeConflictError(
                "An active Oracle continuous runtime "
                "already owns the runtime lock: "
                f"{resolved_lock_file}"
            )

        return OracleContinuousLaunchReadinessRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            status="passed",
            ready=True,
            operator_entry_point_verified=True,
            guarded_launcher_verified=True,
            exact_dependency_chain_verified=True,
            environment_file_present=True,
            postgresql_configuration_present=True,
            continuous_mode_verified=True,
            positive_tick_verified=(
                tick_seconds > 0
            ),
            runtime_directory_ready=True,
            runtime_lock_present=lock_present,
            runtime_conflict_detected=False,
            stale_lock_detected=stale_lock,
            canonical_operator_command=(
                REQUIRED_OPERATOR_COMMAND
            ),
            read_only=True,
            execution_allowed=False,
            order_placement_allowed=False,
            funds_movement_allowed=False,
            portfolio_mutation_allowed=False,
        )


    def main() -> int:
        print("========================================")
        print(" ORACLE CONTINUOUS LAUNCH READINESS")
        print(" OLA-076 OPERATOR PREFLIGHT GATE")
        print(" READ-ONLY NONSTOP START CERTIFICATION")
        print("========================================")

        record = evaluate_launch_readiness()

        print(
            "[OK] OLA-075 operator entry point verified"
        )

        print(
            "[OK] OLA-074 guarded launcher verified"
        )

        print(
            "[OK] Exact continuous dependency chain verified"
        )

        print(
            "[OK] PostgreSQL configuration present"
        )

        print(
            "[OK] Continuous runtime mode verified"
        )

        print(
            "[OK] Positive service cadence verified"
        )

        print(
            "[OK] Runtime directory writable"
        )

        if record.stale_lock_detected:
            print(
                "[INFO] Stale runtime lock detected; "
                "OLA-074 will remove it at launch"
            )
        else:
            print(
                "[OK] No conflicting active runtime detected"
            )

        print(
            "[OK] Oracle read-only boundary frozen"
        )

        print(
            "[READY] Canonical operator command:"
        )

        print(
            REQUIRED_OPERATOR_COMMAND
        )

        print(
            "[PASS] OLA-076 Oracle Continuous "
            "Operator Launch Readiness Gate"
        )

        print(
            record.to_dict()
        )

        return 0


    if __name__ == "__main__":
        try:
            raise SystemExit(
                main()
            )

        except Exception as exc:
            print()
            print(
                "[ERROR]",
                type(exc).__name__ + ":",
                str(exc),
            )

            raise SystemExit(1)
    '''
).lstrip()


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import json
    import os
    import shutil
    import sys
    import uuid
    from pathlib import Path


    ROOT = Path(__file__).resolve().parent

    MODULE_FILE = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / "oracle_continuous_operator_launch_readiness_gate.py"
    )

    TEST_SANDBOX_ROOT = (
        ROOT
        / "runtime"
        / "ola076_test_sandbox"
    )


    def _load_module():
        module_name = "ola076_under_test"

        specification = (
            importlib.util.spec_from_file_location(
                module_name,
                MODULE_FILE,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise RuntimeError(
                "Could not load OLA-076 module"
            )

        module = importlib.util.module_from_spec(
            specification
        )

        previous_module = sys.modules.get(
            module_name
        )

        sys.modules[module_name] = module

        try:
            specification.loader.exec_module(
                module
            )

        except BaseException:
            if previous_module is None:
                sys.modules.pop(
                    module_name,
                    None,
                )
            else:
                sys.modules[module_name] = (
                    previous_module
                )

            raise

        return module


    def _write_dependency(
        path: Path,
        *,
        schema_version: str,
        engine_id: str,
        read_only: bool = True,
        execution_allowed: bool = False,
        include_main: bool = True,
    ) -> None:
        lines = [
            f'SCHEMA_VERSION = "{schema_version}"',
            f'ENGINE_ID = "{engine_id}"',
            f"READ_ONLY = {read_only!r}",
            (
                "EXECUTION_ALLOWED = "
                f"{execution_allowed!r}"
            ),
        ]

        if include_main:
            lines.extend(
                (
                    "",
                    "def main():",
                    "    return 0",
                )
            )

        path.write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )


    def _assert_raises(
        expected_exception: type[BaseException],
        callable_object,
    ) -> BaseException:
        try:
            callable_object()

        except expected_exception as exc:
            return exc

        raise AssertionError(
            "Expected exception was not raised: "
            f"{expected_exception.__name__}"
        )


    def main() -> None:
        print("========================================")
        print(" OLA-076 LAUNCH READINESS GATE TEST")
        print(" PYTHON 3.14 IMPORT CORRECTION V2")
        print(" NO REAL CONTINUOUS SERVICE START")
        print("========================================")

        module = _load_module()

        assert module.SCHEMA_VERSION == "OLA-076"
        assert module.ENGINE_ID == "OLA-076"
        assert module.READ_ONLY is True
        assert module.EXECUTION_ALLOWED is False
        assert (
            module.ORDER_PLACEMENT_ALLOWED
            is False
        )
        assert (
            module.FUNDS_MOVEMENT_ALLOWED
            is False
        )
        assert (
            module.PORTFOLIO_MUTATION_ALLOWED
            is False
        )

        assert (
            sys.modules.get(
                "ola076_under_test"
            )
            is module
        )

        print(
            "[OK] Python 3.14 module registration verified"
        )

        print(
            "[OK] OLA-076 dataclass module loaded"
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

        try:
            operator_file = (
                sandbox
                / "run_oracle_live_shadow_CONTINUOUS.py"
            )

            guarded_file = (
                sandbox
                / (
                    "run_oracle_live_shadow_"
                    "CONTINUOUS_GUARDED.py"
                )
            )

            env_file = sandbox / ".env"

            runtime_directory = (
                sandbox
                / "runtime"
                / "oracle_live_shadow"
            )

            runtime_lock_file = (
                runtime_directory
                / "oracle_continuous_runtime.lock"
            )

            _write_dependency(
                operator_file,
                schema_version="OLA-075",
                engine_id="OLA-075",
            )

            _write_dependency(
                guarded_file,
                schema_version="OLA-074",
                engine_id="OLA-074",
            )

            env_file.write_text(
                "\n".join(
                    (
                        (
                            "DATABASE_URL="
                            "postgresql://oracle:test@"
                            "localhost:5432/postgres"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "TICK_SECONDS=5"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "MAX_ITERATIONS=continuous"
                        ),
                        "",
                    )
                ),
                encoding="utf-8",
            )

            print(
                "[TEST] Fully ready machine configuration"
            )

            record = module.evaluate_launch_readiness(
                root=sandbox,
                env_file=env_file,
                operator_entry_point_file=(
                    operator_file
                ),
                guarded_launcher_file=guarded_file,
                runtime_directory=runtime_directory,
                runtime_lock_file=runtime_lock_file,
                process_environment={},
            )

            assert record.ready is True
            assert record.status == "passed"
            assert (
                record.operator_entry_point_verified
                is True
            )
            assert (
                record.guarded_launcher_verified
                is True
            )
            assert (
                record.exact_dependency_chain_verified
                is True
            )
            assert (
                record.postgresql_configuration_present
                is True
            )
            assert (
                record.continuous_mode_verified
                is True
            )
            assert (
                record.positive_tick_verified
                is True
            )
            assert (
                record.runtime_directory_ready
                is True
            )
            assert (
                record.runtime_conflict_detected
                is False
            )
            assert (
                record.canonical_operator_command
                == (
                    "py "
                    "run_oracle_live_shadow_CONTINUOUS.py"
                )
            )
            assert record.read_only is True
            assert record.execution_allowed is False

            print(
                "[OK] Ready machine configuration passed"
            )

            runtime_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            print(
                "[TEST] Stale runtime lock detection"
            )

            runtime_lock_file.write_text(
                json.dumps(
                    {
                        "schema_version": "OLA-074",
                        "engine_id": "OLA-074",
                        "process_id": 999999999,
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ),
                encoding="utf-8",
            )

            stale_record = (
                module.evaluate_launch_readiness(
                    root=sandbox,
                    env_file=env_file,
                    operator_entry_point_file=(
                        operator_file
                    ),
                    guarded_launcher_file=guarded_file,
                    runtime_directory=(
                        runtime_directory
                    ),
                    runtime_lock_file=(
                        runtime_lock_file
                    ),
                    process_environment={},
                )
            )

            assert (
                stale_record.runtime_lock_present
                is True
            )
            assert (
                stale_record.stale_lock_detected
                is True
            )
            assert (
                stale_record.runtime_conflict_detected
                is False
            )

            print(
                "[OK] Stale runtime lock classified safely"
            )

            print(
                "[TEST] Active runtime conflict rejection"
            )

            runtime_lock_file.write_text(
                json.dumps(
                    {
                        "schema_version": "OLA-074",
                        "engine_id": "OLA-074",
                        "process_id": os.getpid(),
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ),
                encoding="utf-8",
            )

            _assert_raises(
                module.OracleContinuousRuntimeConflictError,
                lambda: module.evaluate_launch_readiness(
                    root=sandbox,
                    env_file=env_file,
                    operator_entry_point_file=(
                        operator_file
                    ),
                    guarded_launcher_file=guarded_file,
                    runtime_directory=(
                        runtime_directory
                    ),
                    runtime_lock_file=(
                        runtime_lock_file
                    ),
                    process_environment={},
                ),
            )

            runtime_lock_file.unlink(
                missing_ok=True
            )

            print(
                "[OK] Active runtime conflict rejected"
            )

            print(
                "[TEST] Bounded runtime rejection"
            )

            env_file.write_text(
                "\n".join(
                    (
                        (
                            "DATABASE_URL="
                            "postgresql://oracle:test@"
                            "localhost:5432/postgres"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "TICK_SECONDS=5"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "MAX_ITERATIONS=3"
                        ),
                        "",
                    )
                ),
                encoding="utf-8",
            )

            _assert_raises(
                module.OracleContinuousConfigurationError,
                lambda: module.evaluate_launch_readiness(
                    root=sandbox,
                    env_file=env_file,
                    operator_entry_point_file=(
                        operator_file
                    ),
                    guarded_launcher_file=guarded_file,
                    runtime_directory=(
                        runtime_directory
                    ),
                    runtime_lock_file=(
                        runtime_lock_file
                    ),
                    process_environment={},
                ),
            )

            print(
                "[OK] Bounded runtime rejected"
            )

            print(
                "[TEST] Missing PostgreSQL configuration"
            )

            env_file.write_text(
                "\n".join(
                    (
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "TICK_SECONDS=5"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "MAX_ITERATIONS=continuous"
                        ),
                        "",
                    )
                ),
                encoding="utf-8",
            )

            _assert_raises(
                module.OracleContinuousConfigurationError,
                lambda: module.evaluate_launch_readiness(
                    root=sandbox,
                    env_file=env_file,
                    operator_entry_point_file=(
                        operator_file
                    ),
                    guarded_launcher_file=guarded_file,
                    runtime_directory=(
                        runtime_directory
                    ),
                    runtime_lock_file=(
                        runtime_lock_file
                    ),
                    process_environment={},
                ),
            )

            print(
                "[OK] Missing PostgreSQL configuration rejected"
            )

            print(
                "[TEST] Incorrect dependency schema"
            )

            env_file.write_text(
                "\n".join(
                    (
                        (
                            "DATABASE_URL="
                            "postgresql://oracle:test@"
                            "localhost:5432/postgres"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "TICK_SECONDS=5"
                        ),
                        (
                            "ORACLE_LIVE_SHADOW_"
                            "MAX_ITERATIONS=continuous"
                        ),
                        "",
                    )
                ),
                encoding="utf-8",
            )

            _write_dependency(
                operator_file,
                schema_version="OLA-999",
                engine_id="OLA-075",
            )

            _assert_raises(
                module.OracleContinuousDependencyError,
                lambda: module.evaluate_launch_readiness(
                    root=sandbox,
                    env_file=env_file,
                    operator_entry_point_file=(
                        operator_file
                    ),
                    guarded_launcher_file=guarded_file,
                    runtime_directory=(
                        runtime_directory
                    ),
                    runtime_lock_file=(
                        runtime_lock_file
                    ),
                    process_environment={},
                ),
            )

            print(
                "[OK] Incorrect dependency schema rejected"
            )

        finally:
            if sandbox.exists():
                shutil.rmtree(
                    sandbox
                )

        print(
            "[OK] Deterministic sandbox removed"
        )

        source = MODULE_FILE.read_text(
            encoding="utf-8"
        )

        required_markers = (
            'SCHEMA_VERSION = "OLA-076"',
            'ENGINE_ID = "OLA-076"',
            "import sys",
            "sys.modules[module_name] = module",
            "specification.loader.exec_module(",
            "previous_module",
            "OracleContinuousLaunchReadinessRecord",
            "_postgresql_configuration_present",
            "_require_continuous_mode",
            "_require_positive_tick",
            "_inspect_runtime_lock",
            "evaluate_launch_readiness",
            "READ_ONLY = True",
            "EXECUTION_ALLOWED = False",
        )

        missing_markers = tuple(
            marker
            for marker in required_markers
            if marker not in source
        )

        if missing_markers:
            raise AssertionError(
                "OLA-076 source is incomplete: "
                f"{missing_markers}"
            )

        result = {
            "schema_version": "OLA-076",
            "engine_id": "OLA-076",
            "status": "passed",
            "python_314_dynamic_import_corrected": True,
            "module_registered_before_exec": True,
            "dataclass_import_supported": True,
            "production_dependency_loader_corrected": True,
            "test_module_loader_corrected": True,
            "continuous_launch_readiness_gate_installed": True,
            "ola075_operator_entry_point_required": True,
            "ola074_guarded_launcher_required": True,
            "exact_dependency_chain_enforced": True,
            "environment_file_required": True,
            "postgresql_configuration_required": True,
            "continuous_mode_required": True,
            "positive_tick_required": True,
            "runtime_directory_write_probe_verified": True,
            "active_runtime_conflict_blocked": True,
            "stale_runtime_lock_detected": True,
            "canonical_operator_command": (
                "py run_oracle_live_shadow_CONTINUOUS.py"
            ),
            "real_continuous_runtime_started_during_test": False,
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
            "[PASS] OLA-076 Oracle Continuous "
            "Operator Launch Readiness Gate"
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
    module_source = MODULE_FILE.read_text(
        encoding="utf-8"
    )

    test_source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    module_markers = (
        "import sys",
        "sys.modules[module_name] = module",
        "previous_module",
        "except BaseException:",
        "OracleContinuousLaunchReadinessRecord",
        "evaluate_launch_readiness",
        "[PASS] OLA-076",
    )

    test_markers = (
        "PYTHON 3.14 IMPORT CORRECTION V2",
        "import sys",
        "sys.modules[module_name] = module",
        "previous_module",
        "Python 3.14 module registration verified",
        "dataclass module loaded",
        "[PASS] OLA-076",
    )

    missing_module_markers = tuple(
        marker
        for marker in module_markers
        if marker not in module_source
    )

    missing_test_markers = tuple(
        marker
        for marker in test_markers
        if marker not in test_source
    )

    if missing_module_markers:
        raise RuntimeError(
            "OLA-076 production correction is incomplete. "
            f"Missing markers: {missing_module_markers}"
        )

    if missing_test_markers:
        raise RuntimeError(
            "OLA-076 test correction is incomplete. "
            f"Missing markers: {missing_test_markers}"
        )

    compile(
        module_source,
        str(MODULE_FILE),
        "exec",
    )

    compile(
        test_source,
        str(TEST_FILE),
        "exec",
    )

    print(
        "[OK] Complete OLA-076 production module replaced"
    )

    print(
        "[OK] Complete OLA-076 test replaced"
    )

    print(
        "[OK] Python 3.14 sys.modules registration installed"
    )

    print(
        "[OK] Dataclass dynamic-import failure corrected"
    )

    print(
        "[OK] Production dependency loader hardened"
    )

    print(
        "[OK] Failed-import module restoration installed"
    )

    print(
        "[OK] No real continuous runtime starts in test"
    )

    print(
        "[OK] Oracle read-only boundary preserved"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-076 PRODUCTION CORRECTION V2")
    print(" PYTHON 3.14 DYNAMIC IMPORT CONTRACT")
    print(" DATACLASS MODULE REGISTRATION")
    print("========================================")

    write_full_replacement(
        MODULE_FILE,
        MODULE_SOURCE,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-076 Python 3.14 dynamic "
        "import correction V2 installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_076_oracle_continuous_"
        "operator_launch_readiness_gate.py"
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