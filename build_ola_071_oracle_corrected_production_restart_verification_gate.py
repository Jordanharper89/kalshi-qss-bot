from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent


REPOSITORY_ROOT = Path(__file__).resolve().parent

TEST_FILE = (
    REPOSITORY_ROOT
    / "test_ola_071_oracle_corrected_production_restart_verification_gate.py"
)


TEST_SOURCE = dedent(
    r'''
    from __future__ import annotations

    import hashlib
    import os
    from dataclasses import dataclass
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any, Mapping

    import psycopg

    from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
        _load_env_file,
        build_real_oracle_shadow_graph,
    )


    SCHEMA_VERSION = "OLA-071"
    ENGINE_ID = "OLA-071"

    ROOT = Path(__file__).resolve().parent
    ENV_FILE = ROOT / ".env"

    RUNTIME_ROOTS = (
        ROOT,
        ROOT / "runtime" / "oracle_live_shadow",
    )


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


    def _sha256_file(
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
            sha256=_sha256_file(path),
        )


    def _newest_json_file(
        directory: Path,
    ) -> Path | None:
        if not directory.exists():
            return None

        candidates = [
            path
            for path in directory.rglob("*.json")
            if path.is_file()
        ]

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda path: (
                path.stat().st_mtime_ns,
                str(path),
            ),
        )


    def _newest_runtime_log() -> FileSnapshot:
        candidates: list[Path] = []

        for runtime_root in RUNTIME_ROOTS:
            candidate = _newest_json_file(
                runtime_root / "logs"
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


    def _current_state_snapshots(
        *,
        runtime_roots: tuple[Path, ...] = RUNTIME_ROOTS,
    ) -> dict[str, FileSnapshot]:
        return {
            str(runtime_root.resolve()): _snapshot_file(
                runtime_root
                / "state"
                / "current.json"
            )
            for runtime_root in runtime_roots
        }


    def _load_environment() -> dict[str, str]:
        if not ENV_FILE.exists():
            raise RuntimeError(
                f"Required environment file is missing: "
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
            environment.get("ORACLE_POSTGRES_URL")
            or environment.get("DATABASE_URL")
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
            environment.get("ORACLE_POSTGRES_URL")
            or environment.get("DATABASE_URL")
        )

        if not database_url:
            raise RuntimeError(
                "PostgreSQL URL is missing."
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
                        "Observation query returned no row."
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

                persistence_terminal_sequence = (
                    int(persistence_row[0])
                    if persistence_row is not None
                    else int(observation_row[1])
                )

                latest_persisted_at = observation_row[2]

                if (
                    latest_persisted_at is not None
                    and (
                        latest_persisted_at.tzinfo is None
                        or latest_persisted_at.utcoffset()
                        is None
                    )
                ):
                    raise RuntimeError(
                        "latest_persisted_at must be "
                        "timezone-aware."
                    )

                return DatabaseSnapshot(
                    observation_count=int(
                        observation_row[0]
                    ),
                    latest_sequence_number=int(
                        observation_row[1]
                    ),
                    latest_persisted_at=(
                        latest_persisted_at
                    ),
                    persistence_terminal_sequence=(
                        persistence_terminal_sequence
                    ),
                )
        finally:
            connection.close()


    def _file_advanced(
        before: FileSnapshot,
        after: FileSnapshot,
    ) -> bool:
        if after.path is None:
            return False

        if before.path != after.path:
            return True

        if (
            before.modified_at_ns
            != after.modified_at_ns
        ):
            return True

        if before.size_bytes != after.size_bytes:
            return True

        if before.sha256 != after.sha256:
            return True

        return False


    def _any_state_advanced(
        before: Mapping[str, FileSnapshot],
        after: Mapping[str, FileSnapshot],
    ) -> bool:
        keys = set(before) | set(after)

        return any(
            _file_advanced(
                before.get(
                    key,
                    FileSnapshot(
                        path=None,
                        modified_at_ns=None,
                        size_bytes=None,
                        sha256=None,
                    ),
                ),
                after.get(
                    key,
                    FileSnapshot(
                        path=None,
                        modified_at_ns=None,
                        size_bytes=None,
                        sha256=None,
                    ),
                ),
            )
            for key in keys
        )


    def main() -> None:
        print("========================================")
        print(" OLA-071 PRODUCTION RESTART VERIFICATION")
        print(" CORRECTED READINESS / THREE REAL CYCLES")
        print(" READ-ONLY BOUNDED PRODUCTION EXECUTION")
        print("========================================")

        environment = _load_environment()

        print(
            "[INFO] PostgreSQL URL present:",
            bool(
                environment.get(
                    "ORACLE_POSTGRES_URL"
                )
                or environment.get(
                    "DATABASE_URL"
                )
            ),
        )

        before_database = _database_snapshot(
            environment
        )

        before_log = _newest_runtime_log()

        before_states = _current_state_snapshots()

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
            service_tick_interval_seconds=0,
        )

        required_graph_keys = (
            "production_live_shadow_persistent_service_activator",
            "initial_polling_state",
            "readiness_kwargs_factory",
            "scheduler_kwargs_factory",
        )

        missing_graph_keys = [
            key
            for key in required_graph_keys
            if key not in graph
        ]

        if missing_graph_keys:
            raise AssertionError(
                "Production graph is missing required keys: "
                + ", ".join(missing_graph_keys)
            )

        activator = graph[
            "production_live_shadow_persistent_service_activator"
        ]

        start_kwargs = {
            "initial_polling_state": graph[
                "initial_polling_state"
            ],
            "max_iterations": 3,
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
                "bounded_iterations": 3,
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

        print("[START] Three-cycle production verification")

        activation_record, service_result = (
            activator.activate(
                production_graph=graph,
                start_kwargs=start_kwargs,
            )
        )

        print("[STOP] Bounded production service returned")

        after_database = _database_snapshot(
            environment
        )

        after_log = _newest_runtime_log()

        after_states = _current_state_snapshots()

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

        active_state_advanced = (
            _any_state_advanced(
                before_states,
                after_states,
            )
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
            "[ADVANCED] latest_persisted_at:",
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
            "The bounded production restart did not "
            "persist new observations."
        )

        assert sequence_delta > 0, (
            "The canonical sequence number did not advance."
        )

        assert persistence_delta > 0, (
            "The persistence terminal sequence did not "
            "advance."
        )

        assert persisted_at_advanced is True, (
            "The latest persisted timestamp did not advance."
        )

        assert (
            runtime_log_advanced
            or active_state_advanced
        ), (
            "Neither runtime logs nor active state advanced."
        )

        assert getattr(
            activation_record,
            "read_only",
            None,
        ) is True

        assert getattr(
            activation_record,
            "execution_allowed",
            None,
        ) is False

        assert getattr(
            activation_record,
            "alerts_allowed",
            False,
        ) is False

        assert getattr(
            activation_record,
            "service_start_invoked",
            None,
        ) is True

        assert service_result is not None

        result = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "status": "passed",
            "real_production_graph_assembled": True,
            "actual_persistent_activator_invoked": True,
            "bounded_iterations_requested": 3,
            "bounded_service_returned": True,
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
    text = TEST_FILE.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-071"',
        "build_real_oracle_shadow_graph",
        "max_iterations",
        '"max_iterations": 3',
        "production_live_shadow_persistent_service_activator",
        "observation_delta > 0",
        "sequence_delta > 0",
        "persistence_delta > 0",
        "background_process_left_running",
        "[PASS] OLA-071",
    )

    missing = [
        marker
        for marker in required_markers
        if marker not in text
    ]

    if missing:
        raise RuntimeError(
            "OLA-071 installation is incomplete. "
            f"Missing markers: {missing}"
        )


def main() -> None:
    print("========================================")
    print(" OLA-071 INSTALLER")
    print(" CORRECTED PRODUCTION RESTART")
    print(" THREE-CYCLE PERSISTENCE VERIFICATION")
    print("========================================")

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    validate_installation()

    print()
    print(
        "[DONE] OLA-071 corrected production restart "
        "verification gate installed"
    )
    print()
    print("Run:")
    print(
        "py "
        "test_ola_071_oracle_corrected_"
        "production_restart_verification_gate.py"
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