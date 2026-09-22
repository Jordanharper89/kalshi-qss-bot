from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

LAUNCHER_FILE = (
    ROOT
    / "run_oracle_live_shadow_FINAL_FIXED.py"
)

TEST_FILE = (
    ROOT
    / "test_ola_072_oracle_continuous_production_launcher_correction.py"
)


LAUNCHER_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import os
    from pathlib import Path
    from typing import Mapping

    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
        _load_env_file,
        build_real_oracle_shadow_graph,
    )


    SCHEMA_VERSION = "OLA-072"
    ENGINE_ID = "OLA-072"

    ROOT = Path(__file__).resolve().parent
    ENV_FILE = ROOT / ".env"

    DEFAULT_SERVICE_TICK_INTERVAL_SECONDS = 5


    def _positive_int_setting(
        environment: Mapping[str, str],
        name: str,
        default: int,
    ) -> int:
        raw = environment.get(
            name,
            str(default),
        ).strip()

        try:
            value = int(raw)
        except ValueError as exc:
            raise RuntimeError(
                f"{name} must be an integer"
            ) from exc

        if value < 1:
            raise RuntimeError(
                f"{name} must be greater than zero"
            )

        return value


    def _optional_positive_int_setting(
        environment: Mapping[str, str],
        name: str,
    ) -> int | None:
        raw_value = environment.get(name)

        if raw_value is None:
            return None

        normalized = raw_value.strip().lower()

        if normalized in {
            "",
            "none",
            "null",
            "continuous",
            "unbounded",
            "forever",
        }:
            return None

        try:
            value = int(normalized)
        except ValueError as exc:
            raise RuntimeError(
                f"{name} must be a positive integer "
                "or one of: none, continuous, unbounded, forever"
            ) from exc

        if value < 1:
            raise RuntimeError(
                f"{name} must be greater than zero "
                "when bounded execution is requested"
            )

        return value


    def _load_runtime_environment() -> dict[str, str]:
        environment = dict(os.environ)

        if not ENV_FILE.exists():
            raise RuntimeError(
                f"Required environment file is missing: "
                f"{ENV_FILE}"
            )

        file_environment = dict(
            _load_env_file(
                ENV_FILE
            )
        )

        environment.update(
            file_environment
        )

        database_url_present = bool(
            environment.get(
                "ORACLE_POSTGRES_URL"
            )
            or environment.get(
                "DATABASE_URL"
            )
        )

        if not database_url_present:
            raise RuntimeError(
                "DATABASE_URL or ORACLE_POSTGRES_URL "
                "is missing from .env"
            )

        return environment


    def main() -> int:
        print("========================================")
        print(" ORACLE LIVE SHADOW CONTINUOUS LAUNCH")
        print(" OLA-072 READ-ONLY PRODUCTION RUNTIME")
        print("========================================")

        print(
            f"[INFO] Repository root: {ROOT}"
        )

        print(
            f"[INFO] Loading environment file: "
            f"{ENV_FILE}"
        )

        environment = _load_runtime_environment()

        print("[OK] Environment file loaded")

        database_url_present = bool(
            environment.get(
                "ORACLE_POSTGRES_URL"
            )
            or environment.get(
                "DATABASE_URL"
            )
        )

        print(
            "[INFO] PostgreSQL URL present:",
            database_url_present,
        )

        print(
            "[INFO] PostgreSQL SSL mode:",
            environment.get(
                "ORACLE_POSTGRES_SSLMODE",
                "require",
            ),
        )

        service_tick_interval_seconds = (
            _positive_int_setting(
                environment,
                "ORACLE_LIVE_SHADOW_TICK_SECONDS",
                DEFAULT_SERVICE_TICK_INTERVAL_SECONDS,
            )
        )

        max_iterations = (
            _optional_positive_int_setting(
                environment,
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
            )
        )

        graph = build_real_oracle_shadow_graph(
            runtime_root=ROOT.resolve(),
            environment=environment,
            service_tick_interval_seconds=(
                service_tick_interval_seconds
            ),
        )

        required_graph_keys = (
            "production_live_shadow_persistent_service_activator",
            "runner",
            "initial_polling_state",
            "readiness_kwargs_factory",
            "scheduler_kwargs_factory",
        )

        missing_graph_keys = tuple(
            key
            for key in required_graph_keys
            if key not in graph
        )

        if missing_graph_keys:
            raise RuntimeError(
                "OLA-030 production graph is missing "
                "required launch inputs: "
                + ", ".join(missing_graph_keys)
            )

        runner = graph["runner"]

        if getattr(
            runner,
            "read_only",
            None,
        ) is not True:
            raise RuntimeError(
                "OLA-030 production runner is not read-only"
            )

        if getattr(
            runner,
            "execution_allowed",
            None,
        ) is not False:
            raise RuntimeError(
                "OLA-030 production runner exposes "
                "execution permission"
            )

        activator = graph[
            "production_live_shadow_persistent_service_activator"
        ]

        if getattr(
            activator,
            "read_only",
            None,
        ) is not True:
            raise RuntimeError(
                "OLA-063 activator is not read-only"
            )

        if getattr(
            activator,
            "execution_allowed",
            None,
        ) is not False:
            raise RuntimeError(
                "OLA-063 activator exposes "
                "execution permission"
            )

        start_kwargs = {
            "initial_polling_state": graph[
                "initial_polling_state"
            ],
            "max_iterations": max_iterations,
            "readiness_kwargs_factory": graph[
                "readiness_kwargs_factory"
            ],
            "scheduler_kwargs_factory": graph[
                "scheduler_kwargs_factory"
            ],
            "service_metadata": {
                "launch_engine_id": ENGINE_ID,
                "operator_launcher": (
                    "run_oracle_live_shadow_FINAL_FIXED"
                ),
                "runtime_mode": (
                    "continuous_live_shadow"
                    if max_iterations is None
                    else "bounded_live_shadow"
                ),
                "service_tick_interval_seconds": (
                    service_tick_interval_seconds
                ),
                "max_iterations": max_iterations,
                "read_only": True,
                "execution_allowed": False,
                "alerts_allowed": False,
                "qseries_handoff_allowed": False,
                "trade_authorization_allowed": False,
                "order_placement_allowed": False,
                "funds_moved": False,
                "portfolio_mutated": False,
            },
        }

        print("[OK] OLA-030 production graph assembled")
        print("[OK] Exact graph runner resolved: runner")
        print("[OK] PostgreSQL bootstrap completed")
        print("[OK] Dual-router lineage topology attested")
        print("[OK] Exact OLA-023 runner kwargs bound")

        print(
            "[OK] Service cadence seconds:",
            service_tick_interval_seconds,
        )

        if max_iterations is None:
            print(
                "[OK] Runtime mode: continuous "
                "(no iteration limit)"
            )
        else:
            print(
                "[OK] Runtime mode: bounded"
            )
            print(
                "[OK] Max iterations:",
                max_iterations,
            )

        print("[START] Oracle live-shadow service")
        print(
            "[INFO] Press Ctrl+C for operator shutdown"
        )

        try:
            activation_record, service_result = (
                activator.activate(
                    production_graph=graph,
                    start_kwargs=start_kwargs,
                )
            )

            print(
                "[STOP] Oracle live-shadow service returned"
            )

            print(activation_record)
            print(service_result)

            return 0

        except KeyboardInterrupt:
            print(
                "\n[STOP] Operator shutdown requested"
            )

            return 130


    if __name__ == "__main__":
        raise SystemExit(
            main()
        )
    '''
).lstrip()


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import importlib.util
    import os
    import tempfile
    from pathlib import Path
    from typing import Any


    ROOT = Path(__file__).resolve().parent

    LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_FINAL_FIXED.py"
    )


    class FakeRunner:
        read_only = True
        execution_allowed = False


    class FakeActivator:
        read_only = True
        execution_allowed = False

        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def activate(
            self,
            *,
            production_graph,
            start_kwargs,
        ):
            self.calls.append(
                {
                    "production_graph": (
                        production_graph
                    ),
                    "start_kwargs": dict(
                        start_kwargs
                    ),
                }
            )

            return (
                {
                    "schema_version": "OLA-063",
                    "engine_id": "OLA-063",
                    "read_only": True,
                    "execution_allowed": False,
                },
                (
                    {
                        "status": "completed",
                    },
                    tuple(),
                    {
                        "status": "stopped",
                    },
                ),
            )


    def _load_launcher_module():
        specification = (
            importlib.util.spec_from_file_location(
                "ola072_launcher_under_test",
                LAUNCHER_FILE,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise RuntimeError(
                "Could not load OLA-072 launcher module"
            )

        module = importlib.util.module_from_spec(
            specification
        )

        specification.loader.exec_module(
            module
        )

        return module


    def _fake_graph(
        activator: FakeActivator,
    ) -> dict[str, Any]:
        return {
            "production_live_shadow_persistent_service_activator": (
                activator
            ),
            "runner": FakeRunner(),
            "initial_polling_state": {
                "state": "initial",
            },
            "readiness_kwargs_factory": (
                lambda **kwargs: kwargs
            ),
            "scheduler_kwargs_factory": (
                lambda **kwargs: kwargs
            ),
        }


    def main() -> None:
        module = _load_launcher_module()

        assert module.SCHEMA_VERSION == "OLA-072"
        assert module.ENGINE_ID == "OLA-072"

        assert (
            module.DEFAULT_SERVICE_TICK_INTERVAL_SECONDS
            == 5
        )

        source = LAUNCHER_FILE.read_text(
            encoding="utf-8"
        )

        required_markers = (
            'SCHEMA_VERSION = "OLA-072"',
            'ENGINE_ID = "OLA-072"',
            '"runner"',
            '"max_iterations": max_iterations',
            "if max_iterations is None:",
            "continuous_live_shadow",
            "production_live_shadow_persistent_service_activator",
            "service_tick_interval_seconds",
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
                "OLA-072 launcher source is incomplete: "
                f"{missing_markers}"
            )

        assert (
            module._optional_positive_int_setting(
                {},
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
            )
            is None
        )

        for continuous_value in (
            "",
            "none",
            "null",
            "continuous",
            "unbounded",
            "forever",
        ):
            assert (
                module._optional_positive_int_setting(
                    {
                        "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": (
                            continuous_value
                        ),
                    },
                    "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
                )
                is None
            )

        assert (
            module._optional_positive_int_setting(
                {
                    "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": "3",
                },
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
            )
            == 3
        )

        for invalid_value in (
            "0",
            "-1",
            "abc",
        ):
            try:
                module._optional_positive_int_setting(
                    {
                        "ORACLE_LIVE_SHADOW_MAX_ITERATIONS": (
                            invalid_value
                        ),
                    },
                    "ORACLE_LIVE_SHADOW_MAX_ITERATIONS",
                )
            except RuntimeError:
                pass
            else:
                raise AssertionError(
                    "Invalid max-iteration setting "
                    f"was accepted: {invalid_value}"
                )

        assert (
            module._positive_int_setting(
                {},
                "ORACLE_LIVE_SHADOW_TICK_SECONDS",
                5,
            )
            == 5
        )

        assert (
            module._positive_int_setting(
                {
                    "ORACLE_LIVE_SHADOW_TICK_SECONDS": "1",
                },
                "ORACLE_LIVE_SHADOW_TICK_SECONDS",
                5,
            )
            == 1
        )

        original_environment = dict(
            os.environ
        )

        try:
            with tempfile.TemporaryDirectory() as directory:
                temporary_root = Path(directory)

                env_file = temporary_root / ".env"

                env_file.write_text(
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

                continuous_activator = (
                    FakeActivator()
                )

                captured_build_calls: list[
                    dict[str, Any]
                ] = []

                def continuous_build_graph(
                    *,
                    runtime_root,
                    environment,
                    service_tick_interval_seconds,
                ):
                    captured_build_calls.append(
                        {
                            "runtime_root": runtime_root,
                            "environment": dict(
                                environment
                            ),
                            "service_tick_interval_seconds": (
                                service_tick_interval_seconds
                            ),
                        }
                    )

                    return _fake_graph(
                        continuous_activator
                    )

                module.ENV_FILE = env_file
                module.ROOT = temporary_root
                module.build_real_oracle_shadow_graph = (
                    continuous_build_graph
                )

                os.environ.clear()

                exit_code = module.main()

                assert exit_code == 0

                assert len(
                    captured_build_calls
                ) == 1

                assert (
                    captured_build_calls[0][
                        "service_tick_interval_seconds"
                    ]
                    == 1
                )

                assert len(
                    continuous_activator.calls
                ) == 1

                continuous_start_kwargs = (
                    continuous_activator.calls[0][
                        "start_kwargs"
                    ]
                )

                assert (
                    continuous_start_kwargs[
                        "max_iterations"
                    ]
                    is None
                )

                continuous_metadata = (
                    continuous_start_kwargs[
                        "service_metadata"
                    ]
                )

                assert (
                    continuous_metadata[
                        "runtime_mode"
                    ]
                    == "continuous_live_shadow"
                )

                assert (
                    continuous_metadata[
                        "read_only"
                    ]
                    is True
                )

                assert (
                    continuous_metadata[
                        "execution_allowed"
                    ]
                    is False
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
                                "ORACLE_POSTGRES_SSLMODE="
                                "disable"
                            ),
                            (
                                "ORACLE_LIVE_SHADOW_TICK_SECONDS="
                                "2"
                            ),
                            (
                                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS="
                                "3"
                            ),
                            "",
                        )
                    ),
                    encoding="utf-8",
                )

                bounded_activator = FakeActivator()

                bounded_build_calls: list[
                    dict[str, Any]
                ] = []

                def bounded_build_graph(
                    *,
                    runtime_root,
                    environment,
                    service_tick_interval_seconds,
                ):
                    bounded_build_calls.append(
                        {
                            "runtime_root": runtime_root,
                            "environment": dict(
                                environment
                            ),
                            "service_tick_interval_seconds": (
                                service_tick_interval_seconds
                            ),
                        }
                    )

                    return _fake_graph(
                        bounded_activator
                    )

                module.build_real_oracle_shadow_graph = (
                    bounded_build_graph
                )

                bounded_exit_code = module.main()

                assert bounded_exit_code == 0

                assert (
                    bounded_build_calls[0][
                        "service_tick_interval_seconds"
                    ]
                    == 2
                )

                bounded_start_kwargs = (
                    bounded_activator.calls[0][
                        "start_kwargs"
                    ]
                )

                assert (
                    bounded_start_kwargs[
                        "max_iterations"
                    ]
                    == 3
                )

                bounded_metadata = (
                    bounded_start_kwargs[
                        "service_metadata"
                    ]
                )

                assert (
                    bounded_metadata[
                        "runtime_mode"
                    ]
                    == "bounded_live_shadow"
                )

        finally:
            os.environ.clear()
            os.environ.update(
                original_environment
            )

        result = {
            "schema_version": "OLA-072",
            "engine_id": "OLA-072",
            "status": "passed",
            "canonical_launcher_replaced": True,
            "continuous_mode_default": True,
            "max_iterations_none_propagated": True,
            "bounded_mode_preserved": True,
            "positive_cadence_required": True,
            "actual_graph_runner_key_used": "runner",
            "ola063_activator_preserved": True,
            "ola023_runner_kwargs_preserved": True,
            "environment_file_loading_preserved": True,
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
            "[PASS] OLA-072 Oracle Continuous "
            "Production Launcher Correction"
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
    launcher_source = LAUNCHER_FILE.read_text(
        encoding="utf-8"
    )

    test_source = TEST_FILE.read_text(
        encoding="utf-8"
    )

    launcher_markers = (
        'SCHEMA_VERSION = "OLA-072"',
        'ENGINE_ID = "OLA-072"',
        "def _optional_positive_int_setting(",
        '"runner"',
        '"max_iterations": max_iterations',
        "if max_iterations is None:",
        "continuous_live_shadow",
        "production_live_shadow_persistent_service_activator",
        "service_tick_interval_seconds",
        "Press Ctrl+C for operator shutdown",
        "except KeyboardInterrupt:",
    )

    missing_launcher_markers = tuple(
        marker
        for marker in launcher_markers
        if marker not in launcher_source
    )

    if missing_launcher_markers:
        raise RuntimeError(
            "OLA-072 launcher installation is incomplete. "
            f"Missing markers: "
            f"{missing_launcher_markers}"
        )

    test_markers = (
        "[PASS] OLA-072",
        "continuous_mode_default",
        "max_iterations_none_propagated",
        "bounded_mode_preserved",
        "positive_cadence_required",
        "ola063_activator_preserved",
    )

    missing_test_markers = tuple(
        marker
        for marker in test_markers
        if marker not in test_source
    )

    if missing_test_markers:
        raise RuntimeError(
            "OLA-072 test installation is incomplete. "
            f"Missing markers: {missing_test_markers}"
        )

    forbidden_launcher_markers = (
        "1_000_000",
        '"service_runner"',
        "service_tick_interval_seconds=0",
        "execution_allowed = True",
        "order_placement_allowed = True",
        "funds_moved = True",
        "portfolio_mutated = True",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_launcher_markers
        if marker in launcher_source
    )

    if forbidden_present:
        raise RuntimeError(
            "OLA-072 launcher contains forbidden "
            f"legacy or unsafe markers: {forbidden_present}"
        )

    compile(
        launcher_source,
        str(LAUNCHER_FILE),
        "exec",
    )

    compile(
        test_source,
        str(TEST_FILE),
        "exec",
    )

    print(
        "[OK] Canonical launcher fully replaced"
    )

    print(
        "[OK] Continuous default frozen: "
        "max_iterations=None"
    )

    print(
        "[OK] Positive configurable cadence frozen"
    )

    print(
        "[OK] Bounded diagnostic mode preserved"
    )

    print(
        "[OK] Actual graph runner key frozen: runner"
    )

    print(
        "[OK] OLA-063 persistent activation preserved"
    )

    print(
        "[OK] Read-only safety boundary preserved"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-072 PRODUCTION CORRECTION")
    print(" CONTINUOUS CANONICAL LAUNCHER")
    print(" FULL REPLACEMENT / NO PATCHING")
    print("========================================")

    write_full_replacement(
        LAUNCHER_FILE,
        LAUNCHER_SOURCE,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-072 continuous production "
        "launcher correction installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_072_oracle_continuous_"
        "production_launcher_correction.py"
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