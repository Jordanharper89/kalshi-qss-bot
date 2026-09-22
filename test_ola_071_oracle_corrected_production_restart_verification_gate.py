from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

import psycopg

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    _load_env_file,
    build_real_oracle_shadow_graph,
)


SCHEMA_VERSION = "OLA-071"
ENGINE_ID = "OLA-071"

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"

BOUNDED_ITERATIONS = 3
SERVICE_TICK_INTERVAL_SECONDS = 1


@dataclass(frozen=True)
class DatabaseSnapshot:
    observation_count: int
    latest_sequence_number: int
    latest_persisted_at: datetime | None
    persistence_terminal_sequence: int


@dataclass(frozen=True)
class FileSnapshot:
    path: str | None
    modified_at_ns: int | None
    size_bytes: int | None
    sha256: str | None


def _hash_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def _snapshot_file(
    path: Path | None,
) -> FileSnapshot:
    if (
        path is None
        or not path.exists()
        or not path.is_file()
    ):
        return FileSnapshot(
            path=None,
            modified_at_ns=None,
            size_bytes=None,
            sha256=None,
        )

    stat = path.stat()

    return FileSnapshot(
        path=str(path.resolve()),
        modified_at_ns=stat.st_mtime_ns,
        size_bytes=stat.st_size,
        sha256=_hash_file(path),
    )


def _newest_json(
    directory: Path,
) -> Path | None:
    if not directory.exists():
        return None

    candidates = tuple(
        path
        for path in directory.rglob("*.json")
        if path.is_file()
    )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns,
            str(path),
        ),
    )


def _runtime_log_snapshot() -> FileSnapshot:
    directories = (
        ROOT / "logs",
        ROOT
        / "runtime"
        / "oracle_live_shadow"
        / "logs",
    )

    candidates: list[Path] = []

    for directory in directories:
        candidate = _newest_json(directory)

        if candidate is not None:
            candidates.append(candidate)

    if not candidates:
        return _snapshot_file(None)

    newest = max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns,
            str(path),
        ),
    )

    return _snapshot_file(newest)


def _state_snapshots() -> dict[str, FileSnapshot]:
    paths = (
        ROOT / "state" / "current.json",
        ROOT
        / "runtime"
        / "oracle_live_shadow"
        / "state"
        / "current.json",
    )

    return {
        str(path.resolve()): _snapshot_file(path)
        for path in paths
    }


def _file_advanced(
    before: FileSnapshot,
    after: FileSnapshot,
) -> bool:
    if after.path is None:
        return False

    return any(
        (
            before.path != after.path,
            before.modified_at_ns
            != after.modified_at_ns,
            before.size_bytes
            != after.size_bytes,
            before.sha256
            != after.sha256,
        )
    )


def _state_advanced(
    before: Mapping[str, FileSnapshot],
    after: Mapping[str, FileSnapshot],
) -> bool:
    empty = FileSnapshot(
        path=None,
        modified_at_ns=None,
        size_bytes=None,
        sha256=None,
    )

    return any(
        _file_advanced(
            before.get(key, empty),
            after.get(key, empty),
        )
        for key in set(before) | set(after)
    )


def _load_environment() -> dict[str, str]:
    if not ENV_FILE.exists():
        raise RuntimeError(
            f"Required .env file not found: "
            f"{ENV_FILE}"
        )

    environment = dict(os.environ)

    environment.update(
        dict(
            _load_env_file(
                ENV_FILE
            )
        )
    )

    database_url = (
        environment.get(
            "ORACLE_POSTGRES_URL"
        )
        or environment.get(
            "DATABASE_URL"
        )
    )

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL or ORACLE_POSTGRES_URL "
            "is missing from .env"
        )

    return environment


def _database_snapshot(
    environment: Mapping[str, str],
) -> DatabaseSnapshot:
    database_url = (
        environment.get(
            "ORACLE_POSTGRES_URL"
        )
        or environment.get(
            "DATABASE_URL"
        )
    )

    if not database_url:
        raise RuntimeError(
            "PostgreSQL URL is unavailable."
        )

    sslmode = environment.get(
        "ORACLE_POSTGRES_SSLMODE",
        "require",
    ).strip()

    connection = psycopg.connect(
        database_url,
        sslmode=sslmode,
        connect_timeout=10,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(
                        MAX(sequence_number),
                        0
                    ),
                    MAX(persisted_at)
                FROM oracle_canonical_observations
                """
            )

            observation_row = cursor.fetchone()

            if observation_row is None:
                raise RuntimeError(
                    "Observation snapshot query "
                    "returned no row."
                )

            cursor.execute(
                """
                SELECT
                    terminal_sequence_number
                FROM oracle_canonical_persistence_state
                WHERE state_id = 1
                """
            )

            persistence_row = cursor.fetchone()

            latest_sequence_number = int(
                observation_row[1]
            )

            return DatabaseSnapshot(
                observation_count=int(
                    observation_row[0]
                ),
                latest_sequence_number=(
                    latest_sequence_number
                ),
                latest_persisted_at=(
                    observation_row[2]
                ),
                persistence_terminal_sequence=(
                    int(persistence_row[0])
                    if persistence_row is not None
                    else latest_sequence_number
                ),
            )
    finally:
        connection.close()


def main() -> None:
    print("========================================")
    print(" OLA-071 PRODUCTION RESTART VERIFICATION")
    print(" ACTUAL OLA-030 GRAPH CONTRACT")
    print(" THREE REAL READ-ONLY CYCLES")
    print("========================================")

    environment = _load_environment()

    before_database = _database_snapshot(
        environment
    )

    before_log = _runtime_log_snapshot()
    before_states = _state_snapshots()

    print(
        "[BEFORE] observation_count:",
        before_database.observation_count,
    )

    print(
        "[BEFORE] latest_sequence_number:",
        before_database.latest_sequence_number,
    )

    print(
        "[BEFORE] persistence_terminal_sequence:",
        before_database.persistence_terminal_sequence,
    )

    print(
        "[BEFORE] latest_persisted_at:",
        before_database.latest_persisted_at,
    )

    print(
        "[BEFORE] newest_runtime_log:",
        before_log.path,
    )

    graph = build_real_oracle_shadow_graph(
        runtime_root=ROOT.resolve(),
        environment=environment,
        service_tick_interval_seconds=(
            SERVICE_TICK_INTERVAL_SECONDS
        ),
    )

    required_graph_keys = (
        "production_controlled_launch_package_assembler",
        "production_controlled_launch_package_consumer",
        "production_controlled_launch_permit_executor",
        "production_live_shadow_persistent_service_activator",

        # Actual OLA-030 graph contract:
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
        raise AssertionError(
            "Production graph is missing required keys: "
            + ", ".join(missing_graph_keys)
        )

    runner = graph["runner"]

    assert (
        getattr(
            runner,
            "read_only",
            None,
        )
        is True
    ), "OLA-030 runner is not read-only."

    assert (
        getattr(
            runner,
            "execution_allowed",
            None,
        )
        is False
    ), "OLA-030 runner exposes execution permission."

    runner_callable = getattr(
        runner,
        "run",
        None,
    )

    assert callable(
        runner_callable
    ), "OLA-030 runner has no callable run method."

    activator = graph[
        "production_live_shadow_persistent_service_activator"
    ]

    start_kwargs = {
        "initial_polling_state": graph[
            "initial_polling_state"
        ],
        "max_iterations": BOUNDED_ITERATIONS,
        "readiness_kwargs_factory": graph[
            "readiness_kwargs_factory"
        ],
        "scheduler_kwargs_factory": graph[
            "scheduler_kwargs_factory"
        ],
        "service_metadata": {
            "launch_engine_id": ENGINE_ID,
            "operator_launcher": (
                "test_ola_071_oracle_corrected_"
                "production_restart_verification_gate"
            ),
            "runtime_mode": (
                "bounded_production_restart_verification"
            ),
            "bounded_iterations": (
                BOUNDED_ITERATIONS
            ),
            "service_tick_interval_seconds": (
                SERVICE_TICK_INTERVAL_SECONDS
            ),
            "actual_runner_graph_key": "runner",
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

    print(
        "[OK] OLA-030 production graph assembled"
    )

    print(
        "[OK] Exact graph runner resolved: runner"
    )

    print(
        "[START] Executing exactly three "
        "bounded production cycles"
    )

    activation_record, service_result = (
        activator.activate(
            production_graph=graph,
            start_kwargs=start_kwargs,
        )
    )

    print(
        "[STOP] Bounded production service returned"
    )

    if not isinstance(
        service_result,
        tuple,
    ):
        raise AssertionError(
            "OLA-023 service result must be a tuple."
        )

    if len(service_result) != 3:
        raise AssertionError(
            "OLA-023 service result must contain "
            "exactly three values."
        )

    (
        service_run_record,
        iteration_records,
        final_polling_state,
    ) = service_result

    if not isinstance(
        iteration_records,
        tuple,
    ):
        raise AssertionError(
            "OLA-023 iteration records must be "
            "returned as a tuple."
        )

    if (
        len(iteration_records)
        != BOUNDED_ITERATIONS
    ):
        raise AssertionError(
            "Expected exactly "
            f"{BOUNDED_ITERATIONS} iterations; "
            f"received {len(iteration_records)}."
        )

    after_database = _database_snapshot(
        environment
    )

    after_log = _runtime_log_snapshot()
    after_states = _state_snapshots()

    observation_delta = (
        after_database.observation_count
        - before_database.observation_count
    )

    sequence_delta = (
        after_database.latest_sequence_number
        - before_database.latest_sequence_number
    )

    persistence_delta = (
        after_database.persistence_terminal_sequence
        - before_database.persistence_terminal_sequence
    )

    persisted_at_advanced = (
        after_database.latest_persisted_at
        is not None
        and (
            before_database.latest_persisted_at
            is None
            or (
                after_database.latest_persisted_at
                > before_database.latest_persisted_at
            )
        )
    )

    runtime_log_advanced = _file_advanced(
        before_log,
        after_log,
    )

    active_state_advanced = _state_advanced(
        before_states,
        after_states,
    )

    print(
        "[AFTER] observation_count:",
        after_database.observation_count,
    )

    print(
        "[AFTER] latest_sequence_number:",
        after_database.latest_sequence_number,
    )

    print(
        "[AFTER] persistence_terminal_sequence:",
        after_database.persistence_terminal_sequence,
    )

    print(
        "[AFTER] latest_persisted_at:",
        after_database.latest_persisted_at,
    )

    print(
        "[AFTER] newest_runtime_log:",
        after_log.path,
    )

    print(
        "[DELTA] observations:",
        observation_delta,
    )

    print(
        "[DELTA] sequence:",
        sequence_delta,
    )

    print(
        "[DELTA] persistence terminal:",
        persistence_delta,
    )

    print(
        "[ADVANCED] persisted timestamp:",
        persisted_at_advanced,
    )

    print(
        "[ADVANCED] runtime log:",
        runtime_log_advanced,
    )

    print(
        "[ADVANCED] active state:",
        active_state_advanced,
    )

    assert observation_delta > 0, (
        "Production restart did not persist "
        "new observations."
    )

    assert sequence_delta > 0, (
        "Canonical sequence number did not advance."
    )

    assert persistence_delta > 0, (
        "Persistence terminal sequence "
        "did not advance."
    )

    assert persisted_at_advanced is True, (
        "Latest persisted timestamp "
        "did not advance."
    )

    assert (
        runtime_log_advanced
        or active_state_advanced
    ), (
        "Neither runtime logs nor active state "
        "advanced."
    )

    assert (
        getattr(
            activation_record,
            "schema_version",
            None,
        )
        == "OLA-063"
    )

    assert (
        getattr(
            activation_record,
            "engine_id",
            None,
        )
        == "OLA-063"
    )

    assert (
        getattr(
            activation_record,
            "exact_production_graph_required",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "existing_service_runner_required",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "service_start_callable_resolved",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "service_start_invoked",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "single_activation_enforced",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "read_only",
            None,
        )
        is True
    )

    assert (
        getattr(
            activation_record,
            "execution_allowed",
            None,
        )
        is False
    )

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "actual_ola030_graph_contract_used": True,
        "actual_runner_graph_key": "runner",
        "runner_read_only_verified": True,
        "runner_execution_blocked_verified": True,
        "actual_ola063_activator_invoked": True,
        "actual_ola023_result_contract_verified": True,
        "positive_service_cadence_seconds": (
            SERVICE_TICK_INTERVAL_SECONDS
        ),
        "bounded_iterations_requested": (
            BOUNDED_ITERATIONS
        ),
        "bounded_iterations_returned": (
            len(iteration_records)
        ),
        "observation_count_before": (
            before_database.observation_count
        ),
        "observation_count_after": (
            after_database.observation_count
        ),
        "observation_count_delta": (
            observation_delta
        ),
        "latest_sequence_before": (
            before_database.latest_sequence_number
        ),
        "latest_sequence_after": (
            after_database.latest_sequence_number
        ),
        "latest_sequence_delta": (
            sequence_delta
        ),
        "persistence_terminal_before": (
            before_database.persistence_terminal_sequence
        ),
        "persistence_terminal_after": (
            after_database.persistence_terminal_sequence
        ),
        "persistence_terminal_delta": (
            persistence_delta
        ),
        "latest_persisted_at_advanced": (
            persisted_at_advanced
        ),
        "runtime_log_advanced": (
            runtime_log_advanced
        ),
        "active_state_advanced": (
            active_state_advanced
        ),
        "service_run_record_returned": (
            service_run_record is not None
        ),
        "final_polling_state_returned": (
            final_polling_state is not None
        ),
        "readiness_recovery_production_path_used": True,
        "background_process_left_running": False,
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
        "[PASS] OLA-071 Oracle Corrected Production "
        "Restart Verification Gate"
    )

    print(result)


if __name__ == "__main__":
    main()
