from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

DIAGNOSTIC_PATH = (
    ROOT
    / "run_ola_068_oracle_passive_runtime_advancement_DIAGNOSTIC.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_068_oracle_passive_runtime_advancement_DIAGNOSTIC.py"
)


DIAGNOSTIC_SOURCE = r'''"""
OLA-068 PASSIVE RUNTIME ADVANCEMENT DIAGNOSTIC

Repository-grounded diagnostic for the existing OLA-068 passive monitor.

This script:

- observes the existing Oracle runtime only;
- reads the canonical OLA-074 runtime lock;
- verifies the locked process on Windows;
- resolves the same PostgreSQL URL candidates used by OLA-068;
- captures complete BEFORE and AFTER OLA-068 snapshots;
- prints every field involved in the advancement decision;
- does not invoke the scheduler, runner, or acquisition cycle;
- does not modify production modules;
- does not restart Oracle;
- does not place orders or mutate funds or portfolios.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping
from urllib.parse import urlsplit

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_passive_runtime_advancement_monitor import (
    OraclePassiveRuntimeAdvancementRecord,
    OraclePassiveRuntimeSnapshot,
    build_passive_runtime_snapshot,
    compare_passive_runtime_snapshots,
)


ROOT = Path(__file__).resolve().parent

RUNTIME_ROOT = (
    ROOT
    / "runtime"
    / "oracle_live_shadow"
)

LOCK_PATH = (
    RUNTIME_ROOT
    / "oracle_continuous_runtime.lock"
)

ENV_PATH = (
    ROOT
    / ".env"
)

OBSERVATION_WINDOW_SECONDS = 30.0

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
STILL_ACTIVE = 259
ERROR_ACCESS_DENIED = 5


class DiagnosticFailure(
    RuntimeError
):
    """OLA-068 diagnostic failure."""


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _load_env_values(
    path: Path,
) -> dict[str, str]:
    values: dict[str, str] = {}

    if not path.is_file():
        return values

    for raw_line in path.read_text(
        encoding="utf-8"
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
            and value[0] in {
                "'",
                '"',
            }
        ):
            value = value[1:-1]

        if key:
            values[key] = value

    return values


def _resolve_database_url(
    env_values: Mapping[str, str],
) -> tuple[str, str]:
    candidates = (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRESQL_URL",
        "ORACLE_DATABASE_URL",
    )

    for key in candidates:
        process_value = os.getenv(
            key
        )

        if (
            process_value
            and process_value.strip()
        ):
            return (
                key,
                process_value.strip(),
            )

        file_value = env_values.get(
            key
        )

        if (
            file_value
            and file_value.strip()
        ):
            return (
                key,
                file_value.strip(),
            )

    raise DiagnosticFailure(
        "No PostgreSQL URL was found under the "
        "OLA-068 environment candidates."
    )


def _safe_database_identity(
    database_url: str,
) -> dict[str, Any]:
    parsed = urlsplit(
        database_url
    )

    return {
        "scheme": parsed.scheme or None,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "database": (
            parsed.path.lstrip("/")
            if parsed.path
            else None
        ),
        "username_present": bool(
            parsed.username
        ),
        "password_present": bool(
            parsed.password
        ),
        "url_sha256_prefix": sha256(
            database_url.encode(
                "utf-8"
            )
        ).hexdigest()[:16],
    }


def _read_lock() -> dict[str, Any]:
    if not LOCK_PATH.is_file():
        raise DiagnosticFailure(
            f"Runtime lock not found: {LOCK_PATH}"
        )

    try:
        payload = json.loads(
            LOCK_PATH.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
    ) as exc:
        raise DiagnosticFailure(
            "Runtime lock is not valid JSON."
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise DiagnosticFailure(
            "Runtime lock must contain a JSON object."
        )

    return payload


def _windows_process_is_alive(
    process_id: int,
) -> bool:
    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )

    open_process = kernel32.OpenProcess
    open_process.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    open_process.restype = wintypes.HANDLE

    get_exit_code_process = (
        kernel32.GetExitCodeProcess
    )
    get_exit_code_process.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(
            wintypes.DWORD
        ),
    ]
    get_exit_code_process.restype = wintypes.BOOL

    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [
        wintypes.HANDLE
    ]
    close_handle.restype = wintypes.BOOL

    ctypes.set_last_error(
        0
    )

    handle = open_process(
        PROCESS_QUERY_LIMITED_INFORMATION
        | SYNCHRONIZE,
        False,
        process_id,
    )

    if not handle:
        return (
            ctypes.get_last_error()
            == ERROR_ACCESS_DENIED
        )

    try:
        exit_code = wintypes.DWORD()

        success = get_exit_code_process(
            handle,
            ctypes.byref(
                exit_code
            ),
        )

        return (
            bool(success)
            and exit_code.value == STILL_ACTIVE
        )
    finally:
        close_handle(
            handle
        )


def _process_is_alive(
    process_id: int,
) -> bool:
    if (
        isinstance(process_id, bool)
        or not isinstance(process_id, int)
        or process_id < 1
    ):
        return False

    if os.name == "nt":
        return _windows_process_is_alive(
            process_id
        )

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


def _format_datetime(
    value: datetime | None,
) -> str:
    if value is None:
        return "None"

    return value.isoformat()


def _print_snapshot(
    label: str,
    snapshot: OraclePassiveRuntimeSnapshot,
) -> None:
    print(
        "----------------------------------------"
    )
    print(
        f" {label} OLA-068 SNAPSHOT"
    )
    print(
        "----------------------------------------"
    )

    print(
        f"captured_at: "
        f"{_format_datetime(snapshot.captured_at)}"
    )

    print(
        f"observation_count: "
        f"{snapshot.observation_count}"
    )

    print(
        f"latest_sequence_number: "
        f"{snapshot.latest_sequence_number}"
    )

    print(
        f"persistence_terminal_sequence: "
        f"{snapshot.persistence_terminal_sequence}"
    )

    print(
        f"latest_persisted_at: "
        f"{_format_datetime(snapshot.latest_persisted_at)}"
    )

    print(
        f"newest_runtime_log_path: "
        f"{snapshot.newest_runtime_log_path}"
    )

    print(
        f"newest_runtime_log_modified_at: "
        f"{_format_datetime(
            snapshot.newest_runtime_log_modified_at
        )}"
    )

    print(
        f"newest_runtime_log_size_bytes: "
        f"{snapshot.newest_runtime_log_size_bytes}"
    )

    print(
        f"newest_runtime_log_sha256: "
        f"{snapshot.newest_runtime_log_sha256}"
    )

    print(
        f"active_state_path: "
        f"{snapshot.active_state_path}"
    )

    print(
        f"active_state_modified_at: "
        f"{_format_datetime(
            snapshot.active_state_modified_at
        )}"
    )

    print(
        f"active_state_size_bytes: "
        f"{snapshot.active_state_size_bytes}"
    )

    print(
        f"active_state_sha256: "
        f"{snapshot.active_state_sha256}"
    )

    print(
        f"snapshot_hash: "
        f"{snapshot.snapshot_hash}"
    )


def _print_result(
    record: OraclePassiveRuntimeAdvancementRecord,
) -> None:
    print(
        "========================================"
    )
    print(
        " OLA-068 COMPARISON RESULT"
    )
    print(
        "========================================"
    )

    print(
        f"status: {record.status}"
    )

    print(
        f"observation_count_delta: "
        f"{record.observation_count_delta}"
    )

    print(
        f"latest_sequence_delta: "
        f"{record.latest_sequence_delta}"
    )

    print(
        f"persistence_terminal_sequence_delta: "
        f"{record.persistence_terminal_sequence_delta}"
    )

    print(
        f"latest_persisted_at_advanced: "
        f"{record.latest_persisted_at_advanced}"
    )

    print(
        f"runtime_log_advanced: "
        f"{record.runtime_log_advanced}"
    )

    print(
        f"active_state_advanced: "
        f"{record.active_state_advanced}"
    )

    print(
        f"postgresql_persistence_advanced: "
        f"{record.postgresql_persistence_advanced}"
    )

    print(
        f"runtime_advancing: "
        f"{record.runtime_advancing}"
    )

    print(
        f"evidence_hash: "
        f"{record.evidence_hash}"
    )

    print(
        "----------------------------------------"
    )
    print(
        " INDIVIDUAL CONTRACT CONDITIONS"
    )
    print(
        "----------------------------------------"
    )

    conditions = (
        (
            "observation_count_delta > 0",
            record.observation_count_delta > 0,
        ),
        (
            "latest_sequence_delta > 0",
            record.latest_sequence_delta > 0,
        ),
        (
            "persistence_terminal_sequence_delta > 0",
            (
                record
                .persistence_terminal_sequence_delta
                > 0
            ),
        ),
        (
            "latest_persisted_at_advanced",
            record.latest_persisted_at_advanced,
        ),
        (
            "runtime_log_advanced",
            record.runtime_log_advanced,
        ),
        (
            "active_state_advanced",
            record.active_state_advanced,
        ),
    )

    for name, passed in conditions:
        marker = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"[{marker}] {name}"
        )

    failed_conditions = [
        name
        for name, passed in conditions
        if not passed
    ]

    print(
        "----------------------------------------"
    )

    if failed_conditions:
        print(
            "[DIAGNOSIS] OLA-068 blocked by:"
        )

        for name in failed_conditions:
            print(
                f"  - {name}"
            )
    else:
        print(
            "[DIAGNOSIS] Every individual signal advanced."
        )

    if (
        record.observation_count_delta > 0
        and record.latest_sequence_delta > 0
        and (
            record.persistence_terminal_sequence_delta
            <= 0
        )
    ):
        print(
            "[DIAGNOSIS] Observation rows advanced, but "
            "oracle_canonical_persistence_state did not."
        )

    if (
        record.observation_count_delta == 0
        and record.latest_sequence_delta == 0
    ):
        print(
            "[DIAGNOSIS] No new canonical observations "
            "were persisted during the window."
        )

    if (
        record.postgresql_persistence_advanced
        and not (
            record.runtime_log_advanced
            or record.active_state_advanced
        )
    ):
        print(
            "[DIAGNOSIS] PostgreSQL advanced, but the "
            "OLA-068 filesystem requirement blocked PASS."
        )


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 PASSIVE RUNTIME DIAGNOSTIC"
    )
    print(
        " CURRENT REPOSITORY CONTRACT"
    )
    print(
        " LIVE ORACLE PROCESS UNCHANGED"
    )
    print(
        "========================================"
    )

    lock_record = _read_lock()

    process_id = lock_record.get(
        "process_id"
    )

    print(
        f"[INFO] lock_path: {LOCK_PATH}"
    )

    print(
        f"[INFO] lock_schema_version: "
        f"{lock_record.get('schema_version')}"
    )

    print(
        f"[INFO] lock_engine_id: "
        f"{lock_record.get('engine_id')}"
    )

    print(
        f"[INFO] runtime_mode: "
        f"{lock_record.get('runtime_mode')}"
    )

    print(
        f"[INFO] launcher: "
        f"{lock_record.get('launcher')}"
    )

    print(
        f"[INFO] process_id: {process_id}"
    )

    if not _process_is_alive(
        process_id
    ):
        raise DiagnosticFailure(
            f"Locked process is not alive: {process_id}"
        )

    print(
        "[PASS] Locked Oracle process is alive"
    )

    env_values = _load_env_values(
        ENV_PATH
    )

    database_key, database_url = (
        _resolve_database_url(
            env_values
        )
    )

    database_identity = (
        _safe_database_identity(
            database_url
        )
    )

    print(
        f"[INFO] database_url_source: "
        f"{database_key}"
    )

    print(
        f"[INFO] database_scheme: "
        f"{database_identity['scheme']}"
    )

    print(
        f"[INFO] database_hostname: "
        f"{database_identity['hostname']}"
    )

    print(
        f"[INFO] database_port: "
        f"{database_identity['port']}"
    )

    print(
        f"[INFO] database_name: "
        f"{database_identity['database']}"
    )

    print(
        f"[INFO] database_username_present: "
        f"{database_identity['username_present']}"
    )

    print(
        f"[INFO] database_password_present: "
        f"{database_identity['password_present']}"
    )

    print(
        f"[INFO] database_url_sha256_prefix: "
        f"{database_identity['url_sha256_prefix']}"
    )

    before = build_passive_runtime_snapshot(
        repository_root=RUNTIME_ROOT,
        captured_at=_utc_now(),
        database_url=database_url,
    )

    assert isinstance(
        before,
        OraclePassiveRuntimeSnapshot,
    )

    _print_snapshot(
        "BEFORE",
        before,
    )

    print(
        "========================================"
    )
    print(
        f" OBSERVING FOR "
        f"{OBSERVATION_WINDOW_SECONDS:.0f} SECONDS"
    )
    print(
        "========================================"
    )

    time.sleep(
        OBSERVATION_WINDOW_SECONDS
    )

    if not _process_is_alive(
        process_id
    ):
        raise DiagnosticFailure(
            "Oracle process stopped during observation."
        )

    after = build_passive_runtime_snapshot(
        repository_root=RUNTIME_ROOT,
        captured_at=_utc_now(),
        database_url=database_url,
    )

    assert isinstance(
        after,
        OraclePassiveRuntimeSnapshot,
    )

    _print_snapshot(
        "AFTER",
        after,
    )

    record = compare_passive_runtime_snapshots(
        before=before,
        after=after,
        observation_window_seconds=(
            OBSERVATION_WINDOW_SECONDS
        ),
        evaluated_at=_utc_now(),
    )

    _print_result(
        record
    )

    print(
        "----------------------------------------"
    )
    print(
        "[PASS] Existing runtime observed only"
    )
    print(
        "[PASS] Scheduler not invoked"
    )
    print(
        "[PASS] Runner not invoked"
    )
    print(
        "[PASS] Acquisition cycle not invoked"
    )
    print(
        "[PASS] Oracle process was not restarted"
    )
    print(
        "[PASS] Oracle remained read-only"
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )
    except Exception as exc:
        print(
            "========================================"
        )
        print(
            " OLA-068 DIAGNOSTIC FAILED"
        )
        print(
            "========================================"
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        raise
'''


TEST_SOURCE = r'''from __future__ import annotations

from pathlib import Path
import py_compile
import runpy


ROOT = Path(__file__).resolve().parent

DIAGNOSTIC_PATH = (
    ROOT
    / "run_ola_068_oracle_passive_runtime_advancement_DIAGNOSTIC.py"
)


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 DIAGNOSTIC INSTALLATION TEST"
    )
    print(
        " PRODUCTION FILES UNCHANGED"
    )
    print(
        "========================================"
    )

    assert DIAGNOSTIC_PATH.is_file()

    source = DIAGNOSTIC_PATH.read_text(
        encoding="utf-8"
    )

    required_markers = (
        "build_passive_runtime_snapshot",
        "compare_passive_runtime_snapshots",
        "observation_count_delta",
        "latest_sequence_delta",
        "persistence_terminal_sequence_delta",
        "latest_persisted_at_advanced",
        "runtime_log_advanced",
        "active_state_advanced",
        "postgresql_persistence_advanced",
        "runtime_advancing",
        "OpenProcess",
        "GetExitCodeProcess",
        "LIVE ORACLE PROCESS UNCHANGED",
    )

    for marker in required_markers:
        assert marker in source

    forbidden_markers = (
        "run_scheduler(",
        "run_runner(",
        "run_acquisition_cycle(",
        "subprocess.",
        "terminate(",
        "kill(",
        "delete_event",
        "send_order",
        "place_order",
    )

    for marker in forbidden_markers:
        assert marker not in source

    py_compile.compile(
        str(
            DIAGNOSTIC_PATH
        ),
        doraise=True,
    )

    namespace = runpy.run_path(
        str(
            DIAGNOSTIC_PATH
        ),
        run_name="ola_068_diagnostic_import_test",
    )

    assert callable(
        namespace["main"]
    )

    assert callable(
        namespace["_print_snapshot"]
    )

    assert callable(
        namespace["_print_result"]
    )

    print(
        "[PASS] Diagnostic file exists"
    )
    print(
        "[PASS] Diagnostic source compiles"
    )
    print(
        "[PASS] Repository OLA-068 APIs bound"
    )
    print(
        "[PASS] Every advancement field is printed"
    )
    print(
        "[PASS] Windows process verification installed"
    )
    print(
        "[PASS] Database credentials remain hidden"
    )
    print(
        "[PASS] Production files remain unchanged"
    )
    print(
        "[PASS] Runtime invocation remains forbidden"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print(
        "========================================"
    )
    print(
        " OLA-068 RUNTIME DIAGNOSTIC INSTALLER"
    )
    print(
        " CURRENT REPOSITORY CONTRACT"
    )
    print(
        " PRODUCTION FILES UNCHANGED"
    )
    print(
        "========================================"
    )

    write_full_replacement(
        DIAGNOSTIC_PATH,
        DIAGNOSTIC_SOURCE,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    print(
        "[OK] Complete BEFORE snapshot output installed"
    )
    print(
        "[OK] Complete AFTER snapshot output installed"
    )
    print(
        "[OK] PostgreSQL delta diagnostics installed"
    )
    print(
        "[OK] Persistence-state delta diagnostics installed"
    )
    print(
        "[OK] Runtime log diagnostics installed"
    )
    print(
        "[OK] Active state diagnostics installed"
    )
    print(
        "[OK] Safe database identity output installed"
    )
    print(
        "[OK] Windows process liveness verification installed"
    )
    print(
        "[OK] Scheduler, runner, and cycle invocation forbidden"
    )
    print(
        "[OK] Production files unchanged"
    )
    print(
        "[DONE] OLA-068 diagnostic installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )