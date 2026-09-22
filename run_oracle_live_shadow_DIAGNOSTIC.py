from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    _load_env_file,
    build_real_oracle_shadow_graph,
)


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"


def _trace_mapping(
    label: str,
    value: Any,
) -> None:
    print(
        f"[TRACE] {label} TYPE: {type(value).__name__}",
        flush=True,
    )

    if isinstance(value, Mapping):
        print(
            f"[TRACE] {label} KEYS: {sorted(value.keys())}",
            flush=True,
        )


def main() -> int:
    print(
        "========================================",
        flush=True,
    )
    print(
        " ORACLE LIVE SHADOW DIAGNOSTIC",
        flush=True,
    )
    print(
        " DIRECT OLA-023 RUNNER / 3 ITERATIONS",
        flush=True,
    )
    print(
        " READ-ONLY RUNTIME DIAGNOSIS",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )

    print(
        f"[DIAG] Repository root: {ROOT.resolve()}",
        flush=True,
    )

    print(
        f"[DIAG] Environment file: {ENV_FILE.resolve()}",
        flush=True,
    )

    print(
        f"[DIAG] Environment file exists: {ENV_FILE.exists()}",
        flush=True,
    )

    print(
        "[DIAG] Loading environment through the existing "
        "OLA-030 repository environment loader...",
        flush=True,
    )

    try:
        environment = _load_env_file(
            ENV_FILE
        )
    except BaseException as exc:
        print(
            "[FAIL] Environment loading raised",
            flush=True,
        )
        print(
            f"[FAIL] Exception type: "
            f"{type(exc).__module__}.{type(exc).__name__}",
            flush=True,
        )
        print(
            f"[FAIL] Exception: {exc}",
            flush=True,
        )
        traceback.print_exc()
        return 1

    postgres_configuration_present = {
        "url": any(
            environment.get(name)
            for name in (
                "ORACLE_POSTGRES_URL",
                "DATABASE_URL",
            )
        ),
        "host": any(
            environment.get(name)
            for name in (
                "ORACLE_POSTGRES_HOST",
                "PGHOST",
            )
        ),
        "database": any(
            environment.get(name)
            for name in (
                "ORACLE_POSTGRES_DATABASE",
                "PGDATABASE",
            )
        ),
        "username": any(
            environment.get(name)
            for name in (
                "ORACLE_POSTGRES_USERNAME",
                "ORACLE_POSTGRES_USER",
                "PGUSER",
            )
        ),
        "password": any(
            environment.get(name)
            for name in (
                "ORACLE_POSTGRES_PASSWORD",
                "PGPASSWORD",
            )
        ),
    }

    print(
        "[DIAG] PostgreSQL configuration presence "
        "(values intentionally hidden):",
        flush=True,
    )

    for key, present in (
        postgres_configuration_present.items()
    ):
        print(
            f"[DIAG]   {key}: {present}",
            flush=True,
        )

    print(
        "[DIAG] Building actual OLA-030 production graph...",
        flush=True,
    )

    try:
        graph = build_real_oracle_shadow_graph(
            runtime_root=ROOT.resolve(),
            environment=environment,
            service_tick_interval_seconds=5,
        )
    except BaseException as exc:
        print(
            "",
            flush=True,
        )
        print(
            "========================================",
            flush=True,
        )
        print(
            "[FAIL] OLA-030 PRODUCTION GRAPH ASSEMBLY RAISED",
            flush=True,
        )
        print(
            f"[FAIL] Exception type: "
            f"{type(exc).__module__}.{type(exc).__name__}",
            flush=True,
        )
        print(
            f"[FAIL] Exception: {exc}",
            flush=True,
        )
        print(
            "========================================",
            flush=True,
        )
        traceback.print_exc()
        return 1

    print(
        "[OK] OLA-030 production graph assembled",
        flush=True,
    )

    required_graph_keys = (
        "runner",
        "initial_polling_state",
        "readiness_kwargs_factory",
        "scheduler_kwargs_factory",
    )

    missing = [
        key
        for key in required_graph_keys
        if key not in graph
    ]

    if missing:
        print(
            "[FAIL] OLA-030 production graph is missing: "
            + ", ".join(missing),
            flush=True,
        )
        return 1

    runner = graph["runner"]

    original_readiness_kwargs_factory = graph[
        "readiness_kwargs_factory"
    ]

    original_scheduler_kwargs_factory = graph[
        "scheduler_kwargs_factory"
    ]

    print(
        "[OK] Exact OLA-023 runner resolved",
        flush=True,
    )

    print(
        f"[DIAG] Runner type: "
        f"{type(runner).__module__}.{type(runner).__name__}",
        flush=True,
    )

    print(
        "[DIAG] Max iterations: 3",
        flush=True,
    )

    def traced_readiness_kwargs_factory(
        iteration_number,
        polling_state,
        checked_at,
        evaluated_at,
    ):
        print(
            "",
            flush=True,
        )
        print(
            "----------------------------------------",
            flush=True,
        )
        print(
            f"[TRACE] ITERATION {iteration_number}",
            flush=True,
        )
        print(
            "[TRACE] readiness_kwargs_factory CALL",
            flush=True,
        )
        print(
            f"[TRACE] readiness checked_at: {checked_at!r}",
            flush=True,
        )
        print(
            f"[TRACE] readiness evaluated_at: {evaluated_at!r}",
            flush=True,
        )
        print(
            f"[TRACE] polling state type: "
            f"{type(polling_state).__name__}",
            flush=True,
        )

        try:
            result = (
                original_readiness_kwargs_factory(
                    iteration_number,
                    polling_state,
                    checked_at,
                    evaluated_at,
                )
            )
        except BaseException:
            print(
                "[FAIL] readiness_kwargs_factory RAISED",
                flush=True,
            )
            traceback.print_exc()
            raise

        print(
            "[TRACE] readiness_kwargs_factory RETURN",
            flush=True,
        )

        _trace_mapping(
            "readiness_kwargs_factory return",
            result,
        )

        return result

    def traced_scheduler_kwargs_factory(
        iteration_number,
        readiness,
        polling_state,
        evaluated_at,
        started_at,
        completed_at,
    ):
        print(
            "[TRACE] scheduler_kwargs_factory CALL",
            flush=True,
        )
        print(
            f"[TRACE] scheduler evaluated_at: {evaluated_at!r}",
            flush=True,
        )
        print(
            f"[TRACE] tick started_at: {started_at!r}",
            flush=True,
        )
        print(
            f"[TRACE] tick completed_at: {completed_at!r}",
            flush=True,
        )
        print(
            f"[TRACE] readiness type: "
            f"{type(readiness).__name__}",
            flush=True,
        )
        print(
            f"[TRACE] polling state type: "
            f"{type(polling_state).__name__}",
            flush=True,
        )

        try:
            result = (
                original_scheduler_kwargs_factory(
                    iteration_number,
                    readiness,
                    polling_state,
                    evaluated_at,
                    started_at,
                    completed_at,
                )
            )
        except BaseException:
            print(
                "[FAIL] scheduler_kwargs_factory RAISED",
                flush=True,
            )
            traceback.print_exc()
            raise

        print(
            "[TRACE] scheduler_kwargs_factory RETURN",
            flush=True,
        )

        _trace_mapping(
            "scheduler_kwargs_factory return",
            result,
        )

        return result

    print(
        "",
        flush=True,
    )
    print(
        "[START] Calling existing OLA-023 runner.run() directly",
        flush=True,
    )
    print(
        "[INFO] This diagnostic is bounded to exactly 3 iterations",
        flush=True,
    )
    print(
        "[INFO] Oracle remains strictly read-only",
        flush=True,
    )

    try:
        result = runner.run(
            initial_polling_state=graph[
                "initial_polling_state"
            ],
            max_iterations=3,
            readiness_kwargs_factory=(
                traced_readiness_kwargs_factory
            ),
            scheduler_kwargs_factory=(
                traced_scheduler_kwargs_factory
            ),
            service_metadata={
                "launch_engine_id": "OLA-030",
                "operator_launcher": (
                    "run_oracle_live_shadow_DIAGNOSTIC"
                ),
                "runtime_mode": (
                    "bounded_runtime_diagnostic"
                ),
                "diagnostic": True,
                "max_iterations": 3,
                "read_only": True,
                "execution_allowed": False,
            },
        )

    except KeyboardInterrupt:
        print(
            "\n[STOP] Diagnostic interrupted by operator",
            flush=True,
        )
        return 130

    except BaseException as exc:
        print(
            "",
            flush=True,
        )
        print(
            "========================================",
            flush=True,
        )
        print(
            "[FAIL] OLA-023 DIRECT RUNNER RAISED",
            flush=True,
        )
        print(
            f"[FAIL] Exception type: "
            f"{type(exc).__module__}.{type(exc).__name__}",
            flush=True,
        )
        print(
            f"[FAIL] Exception: {exc}",
            flush=True,
        )
        print(
            "========================================",
            flush=True,
        )
        traceback.print_exc()
        return 1

    print(
        "",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )
    print(
        "[PASS] OLA-023 DIRECT RUNNER RETURNED",
        flush=True,
    )
    print(
        f"[RESULT] Return type: {type(result).__name__}",
        flush=True,
    )

    if isinstance(result, tuple):
        print(
            f"[RESULT] Tuple length: {len(result)}",
            flush=True,
        )

        for index, item in enumerate(
            result,
            start=1,
        ):
            print(
                f"[RESULT] Item {index} type: "
                f"{type(item).__module__}."
                f"{type(item).__name__}",
                flush=True,
            )

            if isinstance(item, tuple):
                print(
                    f"[RESULT] Item {index} length: "
                    f"{len(item)}",
                    flush=True,
                )

    print(
        "[PASS] Three-iteration diagnostic completed",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )