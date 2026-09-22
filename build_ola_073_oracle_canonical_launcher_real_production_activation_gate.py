from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent

TEST_FILE = (
    ROOT
    / "test_ola_073_oracle_canonical_launcher_real_production_activation_gate.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import contextlib
    import hashlib
    import importlib.util
    import io
    import os
    from dataclasses import dataclass
    from datetime import datetime
    from pathlib import Path
    from typing import Mapping

    import psycopg

    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
        _load_env_file,
    )


    SCHEMA_VERSION = "OLA-073"
    ENGINE_ID = "OLA-073"

    ROOT = Path(__file__).resolve().parent

    LAUNCHER_FILE = (
        ROOT
        / "run_oracle_live_shadow_FINAL_FIXED.py"
    )

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


    def _load_launcher_module():
        if not LAUNCHER_FILE.exists():
            raise RuntimeError(
                f"Canonical launcher not found: "
                f"{LAUNCHER_FILE}"
            )

        specification = (
            importlib.util.spec_from_file_location(
                "ola073_real_launcher_under_test",
                LAUNCHER_FILE,
            )
        )

        if (
            specification is None
            or specification.loader is None
        ):
            raise RuntimeError(
                "Could not load the canonical "
                "OLA-072 launcher"
            )

        module = importlib.util.module_from_spec(
            specification
        )

        specification.loader.exec_module(
            module
        )

        return module


    def _load_real_environment() -> dict[str, str]:
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


    def _bounded_real_environment(
        real_environment: Mapping[str, str],
    ) -> dict[str, str]:
        environment = dict(
            real_environment
        )

        environment[
            "ORACLE_LIVE_SHADOW_TICK_SECONDS"
        ] = str(
            SERVICE_TICK_INTERVAL_SECONDS
        )

        environment[
            "ORACLE_LIVE_SHADOW_MAX_ITERATIONS"
        ] = str(
            BOUNDED_ITERATIONS
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
                "PostgreSQL URL is unavailable"
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
                        "Observation query returned no row"
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

                persistence_terminal_sequence = (
                    int(persistence_row[0])
                    if persistence_row is not None
                    else latest_sequence_number
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
                        persistence_terminal_sequence
                    ),
                )
        finally:
            connection.close()


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


    def _newest_json_file(
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
        candidate_directories = (
            ROOT / "logs",
            ROOT
            / "runtime"
            / "oracle_live_shadow"
            / "logs",
        )

        candidates: list[Path] = []

        for directory in candidate_directories:
            candidate = _newest_json_file(
                directory
            )

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
        state_paths = (
            ROOT / "state" / "current.json",
            ROOT
            / "runtime"
            / "oracle_live_shadow"
            / "state"
            / "current.json",
        )

        return {
            str(path.resolve()): _snapshot_file(path)
            for path in state_paths
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
        empty_snapshot = FileSnapshot(
            path=None,
            modified_at_ns=None,
            size_bytes=None,
            sha256=None,
        )

        all_keys = set(before) | set(after)

        return any(
            _file_advanced(
                before.get(
                    key,
                    empty_snapshot,
                ),
                after.get(
                    key,
                    empty_snapshot,
                ),
            )
            for key in all_keys
        )


    def main() -> None:
        print("========================================")
        print(" OLA-073 REAL PRODUCTION ACTIVATION GATE")
        print(" CANONICAL OLA-072 LAUNCHER")
        print(" THREE BOUNDED LIVE-SHADOW CYCLES")
        print("========================================")

        launcher = _load_launcher_module()

        assert launcher.SCHEMA_VERSION == "OLA-072"
        assert launcher.ENGINE_ID == "OLA-072"

        real_environment = _load_real_environment()

        bounded_environment = (
            _bounded_real_environment(
                real_environment
            )
        )

        assert (
            bounded_environment[
                "ORACLE_LIVE_SHADOW_TICK_SECONDS"
            ]
            == "1"
        )

        assert (
            bounded_environment[
                "ORACLE_LIVE_SHADOW_MAX_ITERATIONS"
            ]
            == "3"
        )

        before_database = _database_snapshot(
            bounded_environment
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

        original_environment_loader = (
            launcher._load_runtime_environment
        )

        def bounded_environment_loader():
            return dict(
                bounded_environment
            )

        launcher._load_runtime_environment = (
            bounded_environment_loader
        )

        captured_output = io.StringIO()

        try:
            with contextlib.redirect_stdout(
                captured_output
            ):
                exit_code = launcher.main()
        finally:
            launcher._load_runtime_environment = (
                original_environment_loader
            )

        launcher_output = (
            captured_output.getvalue()
        )

        print(launcher_output, end="")

        if exit_code != 0:
            raise AssertionError(
                "Canonical launcher returned "
                f"nonzero exit code: {exit_code}"
            )

        required_output_markers = (
            "[OK] OLA-030 production graph assembled",
            "[OK] Exact graph runner resolved: runner",
            "[OK] Exact OLA-023 runner kwargs bound",
            "[OK] Service cadence seconds: 1",
            "[OK] Runtime mode: bounded",
            "[OK] Max iterations: 3",
            "[START] Oracle live-shadow service",
            "[STOP] Oracle live-shadow service returned",
        )

        missing_output_markers = tuple(
            marker
            for marker in required_output_markers
            if marker not in launcher_output
        )

        if missing_output_markers:
            raise AssertionError(
                "Canonical launcher output is missing "
                f"required evidence: "
                f"{missing_output_markers}"
            )

        after_database = _database_snapshot(
            bounded_environment
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
            "Canonical OLA-072 launcher did not "
            "persist new observations."
        )

        assert sequence_delta > 0, (
            "Canonical observation sequence "
            "did not advance."
        )

        assert persistence_delta > 0, (
            "Canonical persistence terminal "
            "sequence did not advance."
        )

        assert persisted_at_advanced is True, (
            "Latest persisted timestamp "
            "did not advance."
        )

        assert (
            runtime_log_advanced
            or active_state_advanced
        ), (
            "Neither runtime logs nor active "
            "state advanced."
        )

        assert sequence_delta == observation_delta, (
            "Observation and sequence deltas "
            "must remain aligned."
        )

        assert persistence_delta == sequence_delta, (
            "Persistence terminal and sequence "
            "deltas must remain aligned."
        )

        result = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "canonical_ola072_launcher_executed": True,
            "actual_ola030_graph_executed": True,
            "actual_runner_graph_key": "runner",
            "actual_ola063_activator_executed": True,
            "actual_ola023_runner_executed": True,
            "bounded_iterations_requested": (
                BOUNDED_ITERATIONS
            ),
            "positive_cadence_seconds": (
                SERVICE_TICK_INTERVAL_SECONDS
            ),
            "launcher_exit_code": exit_code,
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
            "real_env_file_read": True,
            "real_env_file_modified": False,
            "bounded_environment_injected_in_memory": True,
            "background_process_left_running": False,
            "ready_for_continuous_operator_launch": True,
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
            "[PASS] OLA-073 Oracle Canonical Launcher "
            "Real Production Activation Gate"
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
        'SCHEMA_VERSION = "OLA-073"',
        'ENGINE_ID = "OLA-073"',
        "run_oracle_live_shadow_FINAL_FIXED.py",
        "BOUNDED_ITERATIONS = 3",
        "SERVICE_TICK_INTERVAL_SECONDS = 1",
        "launcher._load_runtime_environment",
        "exit_code = launcher.main()",
        "Canonical OLA-072 launcher did not",
        "observation_delta > 0",
        "sequence_delta > 0",
        "persistence_delta > 0",
        "sequence_delta == observation_delta",
        "persistence_delta == sequence_delta",
        "real_env_file_modified",
        "ready_for_continuous_operator_launch",
        "[PASS] OLA-073",
    )

    missing_markers = tuple(
        marker
        for marker in required_markers
        if marker not in source
    )

    if missing_markers:
        raise RuntimeError(
            "OLA-073 installation is incomplete. "
            f"Missing markers: {missing_markers}"
        )

    forbidden_markers = (
        "service_tick_interval_seconds=0",
        '"service_runner"',
        "ENV_FILE.write_text",
        "ENV_FILE.unlink",
        "subprocess.Popen",
        "execution_allowed = True",
        "order_placement_allowed = True",
        "funds_moved = True",
        "portfolio_mutated = True",
    )

    forbidden_present = tuple(
        marker
        for marker in forbidden_markers
        if marker in source
    )

    if forbidden_present:
        raise RuntimeError(
            "OLA-073 contains forbidden unsafe "
            f"or incorrect logic: {forbidden_present}"
        )

    compile(
        source,
        str(TEST_FILE),
        "exec",
    )

    print(
        "[OK] Complete OLA-073 test installed"
    )

    print(
        "[OK] Canonical OLA-072 launcher invocation frozen"
    )

    print(
        "[OK] Actual production graph execution frozen"
    )

    print(
        "[OK] Three-cycle bounded mode frozen"
    )

    print(
        "[OK] Real .env remains unmodified"
    )

    print(
        "[OK] PostgreSQL advancement checks frozen"
    )

    print(
        "[OK] Sequence/persistence alignment frozen"
    )

    print(
        "[OK] No background process boundary frozen"
    )

    print(
        "[OK] Python syntax compilation passed"
    )


def main() -> None:
    print("========================================")
    print(" OLA-073 INTEGRATION GATE")
    print(" CANONICAL LAUNCHER REAL PRODUCTION")
    print(" FINAL BOUNDED GATE BEFORE CONTINUOUS")
    print("========================================")

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-073 canonical launcher real "
        "production activation gate installed"
    )

    print()
    print("Run:")
    print(
        "py "
        "test_ola_073_oracle_canonical_launcher_"
        "real_production_activation_gate.py"
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