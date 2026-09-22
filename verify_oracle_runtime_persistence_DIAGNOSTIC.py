from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg

from qseries_v2.oracle_intelligence.live_acquisition_model.oracle_first_real_shadow_corpus_launch_command import (
    _load_env_file,
)


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
DIAGNOSTIC_LAUNCHER = (
    ROOT / "run_oracle_live_shadow_DIAGNOSTIC.py"
)

RUNTIME_ROOTS = (
    ROOT,
    ROOT / "runtime" / "oracle_live_shadow",
)


@dataclass(frozen=True)
class FileSnapshot:
    path: str | None
    modified_at: str | None
    size_bytes: int | None
    sha256: str | None


@dataclass(frozen=True)
class DatabaseSnapshot:
    observation_count: int
    latest_sequence_number: int
    latest_persisted_at: str | None
    persistence_terminal_sequence: int
    checkpoint_count: int
    latest_checkpointed_at: str | None


def _utc_now_text() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


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

            digest.update(
                block
            )

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
            modified_at=None,
            size_bytes=None,
            sha256=None,
        )

    stat = path.stat()

    return FileSnapshot(
        path=str(
            path.resolve()
        ),
        modified_at=datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        size_bytes=stat.st_size,
        sha256=_sha256_file(
            path
        ),
    )


def _newest_json_file(
    directory: Path,
) -> Path | None:
    if not directory.exists():
        return None

    files = [
        path
        for path in directory.rglob(
            "*.json"
        )
        if path.is_file()
    ]

    if not files:
        return None

    return max(
        files,
        key=lambda path: (
            path.stat().st_mtime_ns,
            str(path),
        ),
    )


def _newest_runtime_log() -> FileSnapshot:
    candidates: list[Path] = []

    for runtime_root in RUNTIME_ROOTS:
        logs_directory = (
            runtime_root / "logs"
        )

        newest = _newest_json_file(
            logs_directory
        )

        if newest is not None:
            candidates.append(
                newest
            )

    if not candidates:
        return _snapshot_file(
            None
        )

    newest = max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns,
            str(path),
        ),
    )

    return _snapshot_file(
        newest
    )


def _current_state_snapshots() -> dict[str, FileSnapshot]:
    snapshots: dict[str, FileSnapshot] = {}

    for runtime_root in RUNTIME_ROOTS:
        current_file = (
            runtime_root
            / "state"
            / "current.json"
        )

        snapshots[
            str(runtime_root.resolve())
        ] = _snapshot_file(
            current_file
        )

    return snapshots


def _database_snapshot(
    environment: dict[str, str],
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
            "DATABASE_URL or ORACLE_POSTGRES_URL "
            "is missing from .env"
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

            observation_row = (
                cursor.fetchone()
            )

            cursor.execute(
                """
                SELECT
                    terminal_sequence_number
                FROM oracle_canonical_persistence_state
                WHERE state_id = 1
                """
            )

            persistence_state_row = (
                cursor.fetchone()
            )

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    MAX(checkpointed_at)
                FROM oracle_persistence_snapshot_checkpoints
                """
            )

            checkpoint_row = (
                cursor.fetchone()
            )

    finally:
        connection.close()

    latest_persisted_at = (
        observation_row[2].isoformat()
        if observation_row[2] is not None
        else None
    )

    latest_checkpointed_at = (
        checkpoint_row[1].isoformat()
        if checkpoint_row[1] is not None
        else None
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
            int(
                persistence_state_row[0]
            )
            if persistence_state_row
            is not None
            else 0
        ),
        checkpoint_count=int(
            checkpoint_row[0]
        ),
        latest_checkpointed_at=(
            latest_checkpointed_at
        ),
    )


def _print_file_snapshot(
    label: str,
    snapshot: FileSnapshot,
) -> None:
    print(
        f"{label}:",
        flush=True,
    )
    print(
        f"  path: {snapshot.path}",
        flush=True,
    )
    print(
        f"  modified_at: "
        f"{snapshot.modified_at}",
        flush=True,
    )
    print(
        f"  size_bytes: "
        f"{snapshot.size_bytes}",
        flush=True,
    )
    print(
        f"  sha256: {snapshot.sha256}",
        flush=True,
    )


def _print_database_snapshot(
    label: str,
    snapshot: DatabaseSnapshot,
) -> None:
    print(
        f"{label}:",
        flush=True,
    )
    print(
        f"  observation_count: "
        f"{snapshot.observation_count}",
        flush=True,
    )
    print(
        f"  latest_sequence_number: "
        f"{snapshot.latest_sequence_number}",
        flush=True,
    )
    print(
        f"  latest_persisted_at: "
        f"{snapshot.latest_persisted_at}",
        flush=True,
    )
    print(
        f"  persistence_terminal_sequence: "
        f"{snapshot.persistence_terminal_sequence}",
        flush=True,
    )
    print(
        f"  checkpoint_count: "
        f"{snapshot.checkpoint_count}",
        flush=True,
    )
    print(
        f"  latest_checkpointed_at: "
        f"{snapshot.latest_checkpointed_at}",
        flush=True,
    )


def _file_changed(
    before: FileSnapshot,
    after: FileSnapshot,
) -> bool:
    return (
        before.path != after.path
        or before.modified_at
        != after.modified_at
        or before.size_bytes
        != after.size_bytes
        or before.sha256
        != after.sha256
    )


def main() -> int:
    print(
        "========================================",
        flush=True,
    )
    print(
        " ORACLE RUNTIME PERSISTENCE DIAGNOSTIC",
        flush=True,
    )
    print(
        " BOUNDED THREE-ITERATION VERIFICATION",
        flush=True,
    )
    print(
        " READ-ONLY / NO EXECUTION",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )

    print(
        f"[DIAG] Started at: "
        f"{_utc_now_text()}",
        flush=True,
    )

    if not ENV_FILE.exists():
        print(
            f"[FAIL] Missing environment file: "
            f"{ENV_FILE}",
            flush=True,
        )
        return 1

    if not DIAGNOSTIC_LAUNCHER.exists():
        print(
            f"[FAIL] Missing diagnostic launcher: "
            f"{DIAGNOSTIC_LAUNCHER}",
            flush=True,
        )
        return 1

    environment = dict(
        _load_env_file(
            ENV_FILE
        )
    )

    print(
        "[STEP 1] Capturing BEFORE state...",
        flush=True,
    )

    try:
        database_before = (
            _database_snapshot(
                environment
            )
        )
    except BaseException as exc:
        print(
            "[FAIL] Could not read PostgreSQL "
            "BEFORE state",
            flush=True,
        )
        print(
            f"[FAIL] {type(exc).__name__}: "
            f"{exc}",
            flush=True,
        )
        traceback.print_exc()
        return 1

    log_before = (
        _newest_runtime_log()
    )

    states_before = (
        _current_state_snapshots()
    )

    _print_database_snapshot(
        "[BEFORE] PostgreSQL",
        database_before,
    )

    _print_file_snapshot(
        "[BEFORE] Newest runtime log",
        log_before,
    )

    for root_name, snapshot in (
        states_before.items()
    ):
        _print_file_snapshot(
            f"[BEFORE] current.json "
            f"under {root_name}",
            snapshot,
        )

    print(
        "",
        flush=True,
    )
    print(
        "[STEP 2] Running existing bounded "
        "three-iteration diagnostic...",
        flush=True,
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(
                DIAGNOSTIC_LAUNCHER
            ),
        ],
        cwd=str(
            ROOT
        ),
        env={
            **os.environ,
            **environment,
        },
        text=True,
    )

    print(
        f"[DIAG] Diagnostic exit code: "
        f"{completed.returncode}",
        flush=True,
    )

    if completed.returncode != 0:
        print(
            "[FAIL] Three-iteration diagnostic "
            "did not complete successfully",
            flush=True,
        )
        return completed.returncode

    print(
        "",
        flush=True,
    )
    print(
        "[STEP 3] Capturing AFTER state...",
        flush=True,
    )

    try:
        database_after = (
            _database_snapshot(
                environment
            )
        )
    except BaseException as exc:
        print(
            "[FAIL] Could not read PostgreSQL "
            "AFTER state",
            flush=True,
        )
        print(
            f"[FAIL] {type(exc).__name__}: "
            f"{exc}",
            flush=True,
        )
        traceback.print_exc()
        return 1

    log_after = (
        _newest_runtime_log()
    )

    states_after = (
        _current_state_snapshots()
    )

    _print_database_snapshot(
        "[AFTER] PostgreSQL",
        database_after,
    )

    _print_file_snapshot(
        "[AFTER] Newest runtime log",
        log_after,
    )

    for root_name, snapshot in (
        states_after.items()
    ):
        _print_file_snapshot(
            f"[AFTER] current.json "
            f"under {root_name}",
            snapshot,
        )

    observation_count_delta = (
        database_after.observation_count
        - database_before.observation_count
    )

    sequence_delta = (
        database_after.latest_sequence_number
        - database_before.latest_sequence_number
    )

    terminal_sequence_delta = (
        database_after.persistence_terminal_sequence
        - database_before.persistence_terminal_sequence
    )

    checkpoint_delta = (
        database_after.checkpoint_count
        - database_before.checkpoint_count
    )

    log_changed = _file_changed(
        log_before,
        log_after,
    )

    changed_state_roots = [
        root_name
        for root_name in states_before
        if _file_changed(
            states_before[root_name],
            states_after[root_name],
        )
    ]

    database_advanced = any(
        (
            observation_count_delta > 0,
            sequence_delta > 0,
            terminal_sequence_delta > 0,
            database_after.latest_persisted_at
            != database_before.latest_persisted_at,
            checkpoint_delta > 0,
            database_after.latest_checkpointed_at
            != database_before.latest_checkpointed_at,
        )
    )

    print(
        "",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )
    print(
        " VERIFICATION RESULT",
        flush=True,
    )
    print(
        "========================================",
        flush=True,
    )

    print(
        f"[RESULT] Observation count delta: "
        f"{observation_count_delta}",
        flush=True,
    )
    print(
        f"[RESULT] Latest sequence delta: "
        f"{sequence_delta}",
        flush=True,
    )
    print(
        f"[RESULT] Persistence terminal "
        f"sequence delta: "
        f"{terminal_sequence_delta}",
        flush=True,
    )
    print(
        f"[RESULT] Checkpoint count delta: "
        f"{checkpoint_delta}",
        flush=True,
    )
    print(
        f"[RESULT] New runtime log written "
        f"or changed: {log_changed}",
        flush=True,
    )
    print(
        f"[RESULT] current.json changed under: "
        f"{changed_state_roots}",
        flush=True,
    )
    print(
        f"[RESULT] PostgreSQL persistence "
        f"advanced: {database_advanced}",
        flush=True,
    )

    cycles_proven = (
        log_changed
        or bool(
            changed_state_roots
        )
    )

    if (
        database_advanced
        and cycles_proven
    ):
        print(
            "",
            flush=True,
        )
        print(
            "[PASS] Fresh runtime cycles and "
            "fresh PostgreSQL persistence proved",
            flush=True,
        )
        print(
            "[PASS] Oracle bounded live-shadow "
            "runtime is functioning read-only",
            flush=True,
        )
        return 0

    print(
        "",
        flush=True,
    )

    if not cycles_proven:
        print(
            "[FAIL] No fresh runtime log or "
            "current.json change was proved",
            flush=True,
        )

    if not database_advanced:
        print(
            "[FAIL] PostgreSQL persistence "
            "did not advance",
            flush=True,
        )

    print(
        "[STATUS] Do not claim persistent "
        "Oracle operation yet",
        flush=True,
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )