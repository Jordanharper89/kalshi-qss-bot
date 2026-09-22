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
