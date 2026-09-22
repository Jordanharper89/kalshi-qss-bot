from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_continuous_runtime_advancement_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_081_oracle_live_continuous_runtime_advancement_gate.py"
)


PRODUCTION_SOURCE = r'''"""
OLA-081
Oracle Live Continuous Runtime Advancement Gate
Windows Process-Liveness Correction V2

Observes an already-running OLA-074 guarded Oracle process without
starting, stopping, restarting, importing, or modifying that process.

This correction replaces the invalid Windows os.kill(pid, 0) liveness
assumption with the native Windows OpenProcess/GetExitCodeProcess contract.
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
import time
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "OLA-081"
ENGINE_ID = "OLA-081"

EXPECTED_LOCK_SCHEMA_VERSION = "OLA-074"
EXPECTED_LOCK_ENGINE_ID = "OLA-074"
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

DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_POLL_INTERVAL_SECONDS = 1.0

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
    """Malformed lock, state, log, or invocation contract."""


class OracleLiveContinuousRuntimeNotActive(
    OracleLiveContinuousRuntimeAdvancementGateError
):
    """No active canonical continuous Oracle process was found."""


class OracleLiveContinuousRuntimeDidNotAdvance(
    OracleLiveContinuousRuntimeAdvancementGateError
):
    """The continuous Oracle runtime did not observably advance."""


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


def _require_positive_number(
    value: Any,
    field_name: str,
) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(
            value,
            (int, float),
        )
    ):
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} must be a positive number"
        )

    normalized = float(
        value
    )

    if normalized <= 0.0:
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} must be greater than zero"
        )

    return normalized


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


def _sha256_file(
    path: Path,
) -> str:
    digest = sha256()

    with path.open(
        "rb"
    ) as handle:
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


def _read_json_object(
    path: Path,
    field_name: str,
) -> dict[str, Any]:
    if not path.is_file():
        raise OracleLiveContinuousRuntimeContractError(
            f"{field_name} does not exist: {path}"
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


def _windows_process_is_alive(
    process_id: int,
) -> bool:
    """
    Resolve process existence through the native Windows process API.

    OpenProcess returning ERROR_ACCESS_DENIED still proves that the process
    exists. A successfully opened handle must report STILL_ACTIVE.
    """

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

    desired_access = (
        PROCESS_QUERY_LIMITED_INFORMATION
        | SYNCHRONIZE
    )

    ctypes.set_last_error(
        0
    )

    handle = open_process(
        desired_access,
        False,
        process_id,
    )

    if not handle:
        error_code = ctypes.get_last_error()

        if error_code == ERROR_ACCESS_DENIED:
            return True

        return False

    try:
        exit_code = wintypes.DWORD()

        success = get_exit_code_process(
            handle,
            ctypes.byref(
                exit_code
            ),
        )

        if not success:
            return False

        return exit_code.value == STILL_ACTIVE
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
            f"{key} must be exactly {expected}"
        )


def _validate_lock_record(
    lock_record: Mapping[str, Any],
    process_is_alive: Callable[[int], bool],
) -> int:
    if lock_record.get(
        "schema_version"
    ) != EXPECTED_LOCK_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock schema_version must be OLA-074"
        )

    if lock_record.get(
        "engine_id"
    ) != EXPECTED_LOCK_ENGINE_ID:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock engine_id must be OLA-074"
        )

    if lock_record.get(
        "runtime_mode"
    ) != EXPECTED_RUNTIME_MODE:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock mode must be continuous_live_shadow"
        )

    if lock_record.get(
        "launcher"
    ) != EXPECTED_LAUNCHER:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock launcher identity mismatch"
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
            "runtime lock process_id must be a positive int"
        )

    started_at_raw = lock_record.get(
        "started_at"
    )

    if not isinstance(
        started_at_raw,
        str,
    ):
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock started_at must be a string"
        )

    try:
        started_at = datetime.fromisoformat(
            started_at_raw
        )
    except ValueError as exc:
        raise OracleLiveContinuousRuntimeContractError(
            "runtime lock started_at must be ISO-8601"
        ) from exc

    _require_aware_datetime(
        started_at,
        "runtime lock started_at",
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

    if not process_is_alive(
        process_id
    ):
        raise OracleLiveContinuousRuntimeNotActive(
            "runtime lock process is not alive: "
            f"{process_id}"
        )

    return process_id


@dataclass(frozen=True)
class RuntimeFileSnapshot:
    path: str
    modified_at_ns: int
    size_bytes: int
    sha256: str

    def to_canonical_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "path": self.path,
            "modified_at_ns": self.modified_at_ns,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


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

    timeout_seconds: float
    poll_interval_seconds: float
    observation_attempt_count: int

    initial_state: RuntimeFileSnapshot
    final_state: RuntimeFileSnapshot
    initial_log: RuntimeFileSnapshot
    final_log: RuntimeFileSnapshot

    state_advanced: bool
    log_advanced: bool
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
            "timeout_seconds": self.timeout_seconds,
            "poll_interval_seconds": (
                self.poll_interval_seconds
            ),
            "observation_attempt_count": (
                self.observation_attempt_count
            ),
            "initial_state": (
                self.initial_state.to_canonical_dict()
            ),
            "final_state": (
                self.final_state.to_canonical_dict()
            ),
            "initial_log": (
                self.initial_log.to_canonical_dict()
            ),
            "final_log": (
                self.final_log.to_canonical_dict()
            ),
            "state_advanced": self.state_advanced,
            "log_advanced": self.log_advanced,
            "process_remained_alive": (
                self.process_remained_alive
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_hash:
            result["record_hash"] = self.record_hash

        return result

    def verify_record_hash(
        self,
    ) -> bool:
        return self.record_hash == stable_hash(
            self.to_canonical_dict(
                include_hash=False
            )
        )


def snapshot_runtime_file(
    path: Path,
) -> RuntimeFileSnapshot:
    path = Path(
        path
    )

    if not path.is_file():
        raise OracleLiveContinuousRuntimeContractError(
            f"runtime file does not exist: {path}"
        )

    stat = path.stat()

    return RuntimeFileSnapshot(
        path=str(
            path.resolve()
        ),
        modified_at_ns=stat.st_mtime_ns,
        size_bytes=stat.st_size,
        sha256=_sha256_file(
            path
        ),
    )


def newest_json_file(
    directory: Path,
) -> Path:
    directory = Path(
        directory
    )

    candidates = [
        path
        for path in directory.rglob(
            "*.json"
        )
        if path.is_file()
    ]

    if not candidates:
        raise OracleLiveContinuousRuntimeContractError(
            f"no JSON runtime files found under: {directory}"
        )

    return max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns,
            str(path),
        ),
    )


def _snapshot_changed(
    initial: RuntimeFileSnapshot,
    final: RuntimeFileSnapshot,
) -> bool:
    return (
        initial.path != final.path
        or initial.modified_at_ns != final.modified_at_ns
        or initial.size_bytes != final.size_bytes
        or initial.sha256 != final.sha256
    )


def evaluate_oracle_live_continuous_runtime_advancement(
    *,
    runtime_root: Path,
    checked_at: datetime,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    process_is_alive: Callable[[int], bool] = (
        default_process_is_alive
    ),
    sleep_callable: Callable[[float], None] = time.sleep,
    now_callable: Callable[[], datetime] = _utc_now,
) -> OracleLiveContinuousRuntimeAdvancementRecord:
    runtime_root = Path(
        runtime_root
    ).resolve()

    checked_at = _require_aware_datetime(
        checked_at,
        "checked_at",
    )

    timeout_seconds = _require_positive_number(
        timeout_seconds,
        "timeout_seconds",
    )

    poll_interval_seconds = _require_positive_number(
        poll_interval_seconds,
        "poll_interval_seconds",
    )

    if poll_interval_seconds > timeout_seconds:
        raise OracleLiveContinuousRuntimeContractError(
            "poll interval cannot exceed timeout"
        )

    for callable_value, field_name in (
        (process_is_alive, "process_is_alive"),
        (sleep_callable, "sleep_callable"),
        (now_callable, "now_callable"),
    ):
        if not callable(
            callable_value
        ):
            raise OracleLiveContinuousRuntimeContractError(
                f"{field_name} must be callable"
            )

    lock_file = (
        runtime_root
        / "oracle_continuous_runtime.lock"
    )

    state_file = (
        runtime_root
        / "state"
        / "current.json"
    )

    logs_directory = (
        runtime_root
        / "logs"
    )

    lock_record = _read_json_object(
        lock_file,
        "runtime lock",
    )

    process_id = _validate_lock_record(
        lock_record,
        process_is_alive,
    )

    initial_state = snapshot_runtime_file(
        state_file
    )

    initial_log = snapshot_runtime_file(
        newest_json_file(
            logs_directory
        )
    )

    elapsed = 0.0
    attempt_count = 0

    final_state = initial_state
    final_log = initial_log
    state_advanced = False
    log_advanced = False

    while elapsed < timeout_seconds:
        attempt_count += 1

        sleep_callable(
            poll_interval_seconds
        )

        elapsed += poll_interval_seconds

        if not process_is_alive(
            process_id
        ):
            raise OracleLiveContinuousRuntimeNotActive(
                "Oracle stopped during observation"
            )

        final_state = snapshot_runtime_file(
            state_file
        )

        final_log = snapshot_runtime_file(
            newest_json_file(
                logs_directory
            )
        )

        state_advanced = _snapshot_changed(
            initial_state,
            final_state,
        )

        log_advanced = _snapshot_changed(
            initial_log,
            final_log,
        )

        if (
            state_advanced
            and log_advanced
        ):
            break

    if not state_advanced:
        raise OracleLiveContinuousRuntimeDidNotAdvance(
            "canonical runtime state did not advance "
            f"within {timeout_seconds} seconds"
        )

    if not log_advanced:
        raise OracleLiveContinuousRuntimeDidNotAdvance(
            "canonical runtime log did not advance "
            f"within {timeout_seconds} seconds"
        )

    completed_at = _require_aware_datetime(
        now_callable(),
        "completed_at",
    )

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
        "timeout_seconds": timeout_seconds,
        "poll_interval_seconds": (
            poll_interval_seconds
        ),
        "observation_attempt_count": (
            attempt_count
        ),
        "initial_state": initial_state,
        "final_state": final_state,
        "initial_log": initial_log,
        "final_log": final_log,
        "state_advanced": state_advanced,
        "log_advanced": log_advanced,
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

    record_hash = stable_hash(
        record_without_hash
    )

    return OracleLiveContinuousRuntimeAdvancementRecord(
        **record_without_hash,
        record_hash=record_hash,
    )
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_advancement_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeAdvancementRecord,
    default_process_is_alive,
    evaluate_oracle_live_continuous_runtime_advancement,
)


ROOT = Path(__file__).resolve().parent

RUNTIME_ROOT = (
    ROOT
    / "runtime"
    / "oracle_live_shadow"
)


def main() -> int:
    print("========================================")
    print(" OLA-081 CORRECTION V2")
    print(" LIVE CONTINUOUS RUNTIME ADVANCEMENT")
    print(" WINDOWS NATIVE PROCESS LIVENESS")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-081"
    assert ENGINE_ID == "OLA-081"

    print(
        "[TEST] Native process-liveness contract"
    )

    assert default_process_is_alive(
        os.getpid()
    ) is True

    assert default_process_is_alive(
        -1
    ) is False

    assert default_process_is_alive(
        0
    ) is False

    assert default_process_is_alive(
        True
    ) is False

    print(
        "[PASS] Current Python process resolved as alive"
    )

    if os.name == "nt":
        print(
            "[PASS] Windows OpenProcess/GetExitCodeProcess "
            "contract active"
        )
    else:
        print(
            "[PASS] POSIX signal-zero contract active"
        )

    print(
        "[TEST] Resolve active OLA-074 runtime lock"
    )
    print(
        "[TEST] Observe live state and log advancement"
    )
    print(
        "[INFO] Observation window: up to 20 seconds"
    )
    print(
        "[INFO] Oracle process will not be restarted"
    )

    record = (
        evaluate_oracle_live_continuous_runtime_advancement(
            runtime_root=RUNTIME_ROOT,
            checked_at=datetime.now(
                timezone.utc
            ),
            timeout_seconds=20.0,
            poll_interval_seconds=1.0,
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeAdvancementRecord,
    )

    assert record.schema_version == "OLA-081"
    assert record.engine_id == "OLA-081"
    assert record.gate_status == "passed"

    assert record.process_id > 0

    assert (
        record.runtime_mode
        == "continuous_live_shadow"
    )

    assert (
        record.launcher
        == "run_oracle_live_shadow_"
        "CONTINUOUS_GUARDED.py"
    )

    if os.name == "nt":
        assert (
            record.process_liveness_contract
            == "windows_open_process_exit_code"
        )

    assert record.observation_attempt_count >= 1
    assert record.state_advanced is True
    assert record.log_advanced is True
    assert record.process_remained_alive is True

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False
    assert record.trade_authorization_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    assert record.verify_record_hash() is True

    print(
        "[PASS] Active OLA-074 runtime lock verified"
    )
    print(
        f"[PASS] Live Oracle process verified: "
        f"{record.process_id}"
    )
    print(
        "[PASS] Canonical runtime state advanced"
    )
    print(
        "[PASS] Canonical runtime log advanced"
    )
    print(
        "[PASS] Continuous process remained alive"
    )
    print(
        "[PASS] OLA-081 evidence record hash verified"
    )
    print(
        "[PASS] Oracle remained read-only"
    )
    print(
        "[PASS] Execution, orders, funds, and "
        "portfolio mutation remained disabled"
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
    print("========================================")
    print(" OLA-081 PRODUCTION CORRECTION V2")
    print(" WINDOWS PROCESS-LIVENESS CONTRACT")
    print(" LIVE ORACLE PROCESS UNCHANGED")
    print("========================================")

    write_full_replacement(
        PRODUCTION_PATH,
        PRODUCTION_SOURCE,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    print(
        "[OK] Invalid Windows os.kill liveness "
        "assumption removed"
    )
    print(
        "[OK] Native OpenProcess contract installed"
    )
    print(
        "[OK] Native GetExitCodeProcess contract installed"
    )
    print(
        "[OK] Current-process liveness test installed"
    )
    print(
        "[OK] Active OLA-074 lock validation preserved"
    )
    print(
        "[OK] Runtime state/log advancement gate preserved"
    )
    print(
        "[OK] Oracle process is not imported or restarted"
    )
    print(
        "[OK] Oracle remains read-only"
    )
    print(
        "[DONE] OLA-081 correction V2 installed"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )