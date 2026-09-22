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
