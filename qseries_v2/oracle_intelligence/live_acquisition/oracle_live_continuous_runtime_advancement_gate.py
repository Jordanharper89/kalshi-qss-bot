"""
OLA-081
Oracle Live Continuous Runtime Advancement Gate
Repository-Aligned Full Rewrite V3

This gate observes the already-running OLA-074 continuous Oracle process.

Repository alignment:

- OLA-074 owns the single-runtime lock.
- OLA-068 owns passive runtime advancement observation.
- PostgreSQL persistence advancement is the canonical proof that the live
  Oracle acquisition runtime is advancing.
- Runtime state and runtime log movement are supporting evidence and are
  not required to change during every observation window.

This module does not start, stop, restart, invoke, or modify Oracle.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_passive_runtime_advancement_monitor import (
    OraclePassiveRuntimeAdvancementRecord,
    run_repository_passive_monitor,
)


SCHEMA_VERSION = "OLA-081"
ENGINE_ID = "OLA-081"

UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_LOCK_SCHEMA_VERSION = "OLA-074"

EXPECTED_RUNTIME_MODE = "continuous_live_shadow"
EXPECTED_LAUNCHER = (
    "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SYNCHRONIZE = 0x00100000
STILL_ACTIVE = 259
ERROR_ACCESS_DENIED = 5


class OracleLiveContinuousRuntimeAdvancementGateError(
    RuntimeError
):
    """Base OLA-081 failure."""


class OracleLiveContinuousRuntimeContractError(
    OracleLiveContinuousRuntimeAdvancementGateError
):
    """Malformed runtime lock or invocation contract."""


class OracleLiveContinuousRuntimeNotActive(
    OracleLiveContinuousRuntimeAdvancementGateError
):
    """The guarded Oracle process is not active."""


class OracleLiveContinuousRuntimeDidNotAdvance(
    OracleLiveContinuousRuntimeAdvancementGateError
):
    """PostgreSQL persistence did not advance."""


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} must be a datetime"
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} must be timezone-aware"
        )

    return value


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        (bool, int, float, str),
    ):
        return value

    if isinstance(
        value,
        datetime,
    ):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(
        value,
        Path,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        Mapping,
    ):
        result: dict[str, Any] = {}

        for key in sorted(
            value
        ):
            if not isinstance(
                key,
                str,
            ):
                raise OracleLiveContinuousRuntimeContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(
        value,
        (tuple, list),
    ):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise OracleLiveContinuousRuntimeContractError(
        "unsupported canonical type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(
            value
        ),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(
            value
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _read_json_object(
    path: Path,
    field_name: str,
) -> dict[str, Any]:
    if not path.is_file():
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} not found: {path}"
        )

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
    ) as exc:
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} is not valid JSON"
        ) from exc

    if not isinstance(
        value,
        dict,
    ):
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} must contain a JSON object"
        )

    return value


def _load_environment_file(
    environment_file: Path,
) -> dict[str, str]:
    if not environment_file.is_file():
        raise OracleLiveContinuousRuntimeContractError(
            f"environment file not found: {environment_file}"
        )

    values: dict[str, str] = {}

    for raw_line in environment_file.read_text(
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
    repository_root: Path,
) -> str:
    environment = dict(
        os.environ
    )

    environment.update(
        _load_environment_file(
            repository_root
            / ".env"
        )
    )

    database_url = (
        environment.get(
            "ORACLE_POSTGRES_URL"
        )
        or environment.get(
            "DATABASE_URL"
        )
        or environment.get(
            "POSTGRES_URL"
        )
    )

    if not database_url:
        raise OracleLiveContinuousRuntimeContractError(
            "DATABASE_URL, ORACLE_POSTGRES_URL, or "
            "POSTGRES_URL is required"
        )

    return database_url


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

        return bool(
            success
        ) and exit_code.value == STILL_ACTIVE
    finally:
        close_handle(
            handle
        )


def _posix_process_is_alive(
    process_id: int,
) -> bool:
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


def default_process_is_alive(
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

    return _posix_process_is_alive(
        process_id
    )


def _require_exact_bool(
    payload: Mapping[str, Any],
    key: str,
    expected: bool,
) -> None:
    if payload.get(
        key
    ) is not expected:
        raise OracleLiveContinuousRuntimeContractError(
            f"runtime lock {key} must be exactly {expected}"
        )


def _validate_runtime_lock(
    lock_record: Mapping[str, Any],
) -> int:
    if lock_record.get(
        "schema_version"
    ) != UPSTREAM_LOCK_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock schema must be OLA-074"
        )

    if lock_record.get(
        "engine_id"
    ) != UPSTREAM_LOCK_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock engine must be OLA-074"
        )

    if lock_record.get(
        "runtime_mode"
    ) != EXPECTED_RUNTIME_MODE:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime mode must be continuous_live_shadow"
        )

    if lock_record.get(
        "launcher"
    ) != EXPECTED_LAUNCHER:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime launcher identity mismatch"
        )

    process_id = lock_record.get(
        "process_id"
    )

    if (
        isinstance(process_id, bool)
        or not isinstance(process_id, int)
        or process_id < 1
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "runtime process_id must be a positive int"
        )

    started_at_raw = lock_record.get(
        "started_at"
    )

    if not isinstance(
        started_at_raw,
        str,
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "runtime started_at must be a string"
        )

    try:
        started_at = datetime.fromisoformat(
            started_at_raw
        )
    except ValueError as exc:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime started_at must be ISO-8601"
        ) from exc

    _require_aware_datetime(
        started_at,
        "runtime started_at",
    )

    for key, expected in (
        ("read_only", True),
        ("execution_allowed", False),
        ("alerts_allowed", False),
        ("qseries_handoff_allowed", False),
        ("trade_authorization_allowed", False),
        ("order_placement_allowed", False),
        ("funds_moved", False),
        ("portfolio_mutated", False),
    ):
        _require_exact_bool(
            lock_record,
            key,
            expected,
        )

    if not default_process_is_alive(
        process_id
    ):
        raise OracleLiveContinuousRuntimeNotActive(
            "runtime lock process is not alive: "
            f"{process_id}"
        )

    return process_id


@dataclass(frozen=True)
class OracleLiveContinuousRuntimeAdvancementRecord:
    schema_version: str
    engine_id: str
    gate_status: str

    checked_at: datetime
    completed_at: datetime

    process_id: int
    runtime_mode: str
    launcher: str
    process_liveness_contract: str

    upstream_monitor_schema_version: str
    observation_window_seconds: float

    before_snapshot_hash: str
    after_snapshot_hash: str

    observation_count_delta: int
    latest_sequence_delta: int
    persistence_terminal_sequence_delta: int

    latest_persisted_at_advanced: bool
    postgresql_persistence_advanced: bool
    runtime_log_advanced: bool
    active_state_advanced: bool
    runtime_advancing: bool

    existing_runtime_observed_only: bool
    acquisition_cycle_invoked: bool
    scheduler_invoked: bool
    runner_invoked: bool
    process_remained_alive: bool

    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    record_hash: str

    def to_canonical_dict(
        self,
        *,
        include_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "gate_status": self.gate_status,
            "checked_at": self.checked_at,
            "completed_at": self.completed_at,
            "process_id": self.process_id,
            "runtime_mode": self.runtime_mode,
            "launcher": self.launcher,
            "process_liveness_contract": (
                self.process_liveness_contract
            ),
            "upstream_monitor_schema_version": (
                self.upstream_monitor_schema_version
            ),
            "observation_window_seconds": (
                self.observation_window_seconds
            ),
            "before_snapshot_hash": (
                self.before_snapshot_hash
            ),
            "after_snapshot_hash": (
                self.after_snapshot_hash
            ),
            "observation_count_delta": (
                self.observation_count_delta
            ),
            "latest_sequence_delta": (
                self.latest_sequence_delta
            ),
            "persistence_terminal_sequence_delta": (
                self.persistence_terminal_sequence_delta
            ),
            "latest_persisted_at_advanced": (
                self.latest_persisted_at_advanced
            ),
            "postgresql_persistence_advanced": (
                self.postgresql_persistence_advanced
            ),
            "runtime_log_advanced": (
                self.runtime_log_advanced
            ),
            "active_state_advanced": (
                self.active_state_advanced
            ),
            "runtime_advancing": (
                self.runtime_advancing
            ),
            "existing_runtime_observed_only": (
                self.existing_runtime_observed_only
            ),
            "acquisition_cycle_invoked": (
                self.acquisition_cycle_invoked
            ),
            "scheduler_invoked": (
                self.scheduler_invoked
            ),
            "runner_invoked": (
                self.runner_invoked
            ),
            "process_remained_alive": (
                self.process_remained_alive
            ),
            "read_only": self.read_only,
            "execution_allowed": (
                self.execution_allowed
            ),
            "alerts_allowed": (
                self.alerts_allowed
            ),
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": (
                self.funds_moved
            ),
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
        }

        if include_hash:
            result["record_hash"] = (
                self.record_hash
            )

        return result

    def verify_record_hash(
        self,
    ) -> bool:
        return self.record_hash == stable_hash(
            self.to_canonical_dict(
                include_hash=False
            )
        )


def evaluate_oracle_live_continuous_runtime_advancement(
    *,
    repository_root: Path,
    checked_at: datetime,
    observation_window_seconds: float = 30.0,
) -> OracleLiveContinuousRuntimeAdvancementRecord:
    repository_root = Path(
        repository_root
    ).resolve()

    if not repository_root.is_dir():
        raise OracleLiveContinuousRuntimeContractError(
            "repository_root must exist"
        )

    checked_at = _require_aware_datetime(
        checked_at,
        "checked_at",
    )

    if (
        isinstance(
            observation_window_seconds,
            bool,
        )
        or not isinstance(
            observation_window_seconds,
            (int, float),
        )
        or float(
            observation_window_seconds
        ) <= 0.0
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "observation_window_seconds must be positive"
        )

    runtime_root = (
        repository_root
        / "runtime"
        / "oracle_live_shadow"
    )

    lock_file = (
        runtime_root
        / "oracle_continuous_runtime.lock"
    )

    lock_record = _read_json_object(
        lock_file,
        "OLA-074 runtime lock",
    )

    process_id = _validate_runtime_lock(
        lock_record
    )

    database_url = _resolve_database_url(
        repository_root
    )

    upstream_record = (
        run_repository_passive_monitor(
            repository_root=runtime_root,
            observation_window_seconds=float(
                observation_window_seconds
            ),
            database_url=database_url,
        )
    )

    if not isinstance(
        upstream_record,
        OraclePassiveRuntimeAdvancementRecord,
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "OLA-068 returned the wrong record type"
        )

    if not default_process_is_alive(
        process_id
    ):
        raise OracleLiveContinuousRuntimeNotActive(
            "Oracle process stopped during observation"
        )

    if upstream_record.schema_version != "OLA-068":
        raise OracleLiveContinuousRuntimeContractError(
            "upstream monitor schema mismatch"
        )

    if (
        upstream_record.existing_runtime_observed_only
        is not True
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "upstream monitor did not remain passive"
        )

    if (
        upstream_record.acquisition_cycle_invoked
        is not False
        or upstream_record.scheduler_invoked
        is not False
        or upstream_record.runner_invoked
        is not False
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "upstream monitor invoked runtime machinery"
        )

    if (
        upstream_record.postgresql_persistence_advanced
        is not True
        or upstream_record.runtime_advancing
        is not True
        or upstream_record.status != "advancing"
    ):
        raise OracleLiveContinuousRuntimeDidNotAdvance(
            "OLA-068 did not observe canonical PostgreSQL "
            "persistence advancement"
        )

    if upstream_record.observation_count_delta <= 0:
        raise OracleLiveContinuousRuntimeDidNotAdvance(
            "observation count did not increase"
        )

    if upstream_record.latest_sequence_delta <= 0:
        raise OracleLiveContinuousRuntimeDidNotAdvance(
            "latest sequence number did not increase"
        )

    completed_at = _utc_now()

    if completed_at < checked_at:
        raise OracleLiveContinuousRuntimeContractError(
            "completed_at cannot precede checked_at"
        )

    liveness_contract = (
        "windows_open_process_exit_code"
        if os.name == "nt"
        else "posix_signal_zero"
    )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "gate_status": "passed",
        "checked_at": checked_at,
        "completed_at": completed_at,
        "process_id": process_id,
        "runtime_mode": EXPECTED_RUNTIME_MODE,
        "launcher": EXPECTED_LAUNCHER,
        "process_liveness_contract": (
            liveness_contract
        ),
        "upstream_monitor_schema_version": (
            UPSTREAM_MONITOR_SCHEMA_VERSION
        ),
        "observation_window_seconds": float(
            observation_window_seconds
        ),
        "before_snapshot_hash": (
            upstream_record.before_snapshot_hash
        ),
        "after_snapshot_hash": (
            upstream_record.after_snapshot_hash
        ),
        "observation_count_delta": (
            upstream_record.observation_count_delta
        ),
        "latest_sequence_delta": (
            upstream_record.latest_sequence_delta
        ),
        "persistence_terminal_sequence_delta": (
            upstream_record
            .persistence_terminal_sequence_delta
        ),
        "latest_persisted_at_advanced": (
            upstream_record.latest_persisted_at_advanced
        ),
        "postgresql_persistence_advanced": (
            upstream_record.postgresql_persistence_advanced
        ),
        "runtime_log_advanced": (
            upstream_record.runtime_log_advanced
        ),
        "active_state_advanced": (
            upstream_record.active_state_advanced
        ),
        "runtime_advancing": (
            upstream_record.runtime_advancing
        ),
        "existing_runtime_observed_only": (
            upstream_record.existing_runtime_observed_only
        ),
        "acquisition_cycle_invoked": (
            upstream_record.acquisition_cycle_invoked
        ),
        "scheduler_invoked": (
            upstream_record.scheduler_invoked
        ),
        "runner_invoked": (
            upstream_record.runner_invoked
        ),
        "process_remained_alive": True,
        "read_only": READ_ONLY,
        "execution_allowed": EXECUTION_ALLOWED,
        "alerts_allowed": ALERTS_ALLOWED,
        "qseries_handoff_allowed": (
            QSERIES_HANDOFF_ALLOWED
        ),
        "trade_authorization_allowed": (
            TRADE_AUTHORIZATION_ALLOWED
        ),
        "order_placement_allowed": (
            ORDER_PLACEMENT_ALLOWED
        ),
        "funds_moved": FUNDS_MOVED,
        "portfolio_mutated": PORTFOLIO_MUTATED,
    }

    return OracleLiveContinuousRuntimeAdvancementRecord(
        **record_without_hash,
        record_hash=stable_hash(
            record_without_hash
        ),
    )
