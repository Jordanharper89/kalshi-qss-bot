from __future__ import annotations

import importlib.util
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "OLA-074"
ENGINE_ID = "OLA-074"

ROOT = Path(__file__).resolve().parent

CANONICAL_LAUNCHER_FILE = (
    ROOT
    / "run_oracle_live_shadow_FINAL_FIXED.py"
)

ENV_FILE = ROOT / ".env"

RUNTIME_DIRECTORY = (
    ROOT
    / "runtime"
    / "oracle_live_shadow"
)

LOCK_FILE = (
    RUNTIME_DIRECTORY
    / "oracle_continuous_runtime.lock"
)

DEFAULT_TICK_SECONDS = 5


class OracleContinuousLaunchError(
    RuntimeError
):
    pass


class OracleContinuousRuntimeAlreadyActive(
    OracleContinuousLaunchError
):
    pass


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _load_env_file(
    path: Path,
) -> dict[str, str]:
    if not path.exists():
        raise OracleContinuousLaunchError(
            f"Required .env file not found: {path}"
        )

    values: dict[str, str] = {}

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

        name, value = line.split(
            "=",
            1,
        )

        normalized_name = (
            name.strip()
        )

        normalized_value = (
            value.strip()
        )

        if (
            len(normalized_value) >= 2
            and normalized_value[0]
            == normalized_value[-1]
            and normalized_value[0]
            in {"'", '"'}
        ):
            normalized_value = (
                normalized_value[1:-1]
            )

        values[
            normalized_name
        ] = normalized_value

    return values


def _load_runtime_environment() -> dict[str, str]:
    environment = dict(
        os.environ
    )

    environment.update(
        _load_env_file(
            ENV_FILE
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
        raise OracleContinuousLaunchError(
            "DATABASE_URL or "
            "ORACLE_POSTGRES_URL "
            "is missing from .env"
        )

    return environment


def _require_positive_tick(
    environment: Mapping[str, str],
) -> int:
    raw_value = environment.get(
        "ORACLE_LIVE_SHADOW_TICK_SECONDS",
        str(DEFAULT_TICK_SECONDS),
    ).strip()

    try:
        value = int(
            raw_value
        )
    except ValueError as exc:
        raise OracleContinuousLaunchError(
            "ORACLE_LIVE_SHADOW_TICK_SECONDS "
            "must be an integer"
        ) from exc

    if value < 1:
        raise OracleContinuousLaunchError(
            "ORACLE_LIVE_SHADOW_TICK_SECONDS "
            "must be greater than zero"
        )

    return value


def _require_continuous_mode(
    environment: Mapping[str, str],
) -> None:
    raw_value = environment.get(
        "ORACLE_LIVE_SHADOW_MAX_ITERATIONS"
    )

    if raw_value is None:
        return

    normalized = (
        raw_value.strip().lower()
    )

    continuous_values = {
        "",
        "none",
        "null",
        "continuous",
        "unbounded",
        "forever",
    }

    if normalized in continuous_values:
        return

    raise OracleContinuousLaunchError(
        "Guarded production launch requires "
        "continuous mode. Remove "
        "ORACLE_LIVE_SHADOW_MAX_ITERATIONS "
        "from .env or set it to continuous."
    )


def _process_is_alive(
    process_id: int,
) -> bool:
    if process_id < 1:
        return False

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


def _read_existing_lock() -> dict[str, Any] | None:
    if not LOCK_FILE.exists():
        return None

    try:
        payload = json.loads(
            LOCK_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        ValueError,
        TypeError,
    ):
        return {
            "invalid_lock_file": True,
        }

    if not isinstance(
        payload,
        dict,
    ):
        return {
            "invalid_lock_file": True,
        }

    return payload


def _remove_stale_lock() -> None:
    existing = _read_existing_lock()

    if existing is None:
        return

    process_id = existing.get(
        "process_id"
    )

    if (
        isinstance(
            process_id,
            int,
        )
        and _process_is_alive(
            process_id
        )
    ):
        raise OracleContinuousRuntimeAlreadyActive(
            "Oracle continuous runtime is already "
            f"active under process {process_id}."
        )

    LOCK_FILE.unlink(
        missing_ok=True
    )

    print(
        "[OK] Removed stale Oracle runtime lock"
    )


def _acquire_runtime_lock() -> dict[str, Any]:
    RUNTIME_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    _remove_stale_lock()

    lock_record = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "process_id": os.getpid(),
        "hostname": socket.gethostname(),
        "started_at": (
            _utc_now().isoformat()
        ),
        "launcher": (
            "run_oracle_live_shadow_"
            "CONTINUOUS_GUARDED.py"
        ),
        "runtime_mode": (
            "continuous_live_shadow"
        ),
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    serialized = json.dumps(
        lock_record,
        sort_keys=True,
        separators=(",", ":"),
    )

    try:
        file_descriptor = os.open(
            str(LOCK_FILE),
            (
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
            ),
        )
    except FileExistsError as exc:
        raise (
            OracleContinuousRuntimeAlreadyActive(
                "Oracle continuous runtime lock "
                "already exists."
            )
        ) from exc

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                serialized
            )

            handle.write("\n")
    except Exception:
        LOCK_FILE.unlink(
            missing_ok=True
        )
        raise

    print(
        f"[OK] Runtime lock acquired: "
        f"{LOCK_FILE}"
    )

    return lock_record


def _release_runtime_lock() -> None:
    if not LOCK_FILE.exists():
        return

    existing = _read_existing_lock()

    if (
        existing is not None
        and existing.get(
            "process_id"
        )
        not in {
            None,
            os.getpid(),
        }
    ):
        print(
            "[WARN] Runtime lock belongs to "
            "another process; not removing it"
        )

        return

    LOCK_FILE.unlink(
        missing_ok=True
    )

    print(
        "[OK] Runtime lock released"
    )


def _load_canonical_launcher():
    if not CANONICAL_LAUNCHER_FILE.exists():
        raise OracleContinuousLaunchError(
            "Canonical OLA-072 launcher "
            f"not found: "
            f"{CANONICAL_LAUNCHER_FILE}"
        )

    specification = (
        importlib.util.spec_from_file_location(
            "ola074_canonical_launcher",
            CANONICAL_LAUNCHER_FILE,
        )
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise OracleContinuousLaunchError(
            "Could not load canonical "
            "OLA-072 launcher"
        )

    module = (
        importlib.util.module_from_spec(
            specification
        )
    )

    specification.loader.exec_module(
        module
    )

    if getattr(
        module,
        "SCHEMA_VERSION",
        None,
    ) != "OLA-072":
        raise OracleContinuousLaunchError(
            "Canonical launcher is not "
            "the certified OLA-072 launcher"
        )

    if not callable(
        getattr(
            module,
            "main",
            None,
        )
    ):
        raise OracleContinuousLaunchError(
            "Canonical OLA-072 launcher "
            "does not expose main()"
        )

    return module


def main() -> int:
    print("========================================")
    print(" ORACLE GUARDED CONTINUOUS PRODUCTION")
    print(" OLA-074 SINGLE-RUNTIME STARTUP GUARD")
    print(" READ-ONLY NONSTOP LIVE SHADOW")
    print("========================================")

    environment = (
        _load_runtime_environment()
    )

    tick_seconds = (
        _require_positive_tick(
            environment
        )
    )

    _require_continuous_mode(
        environment
    )

    print(
        "[OK] Continuous runtime mode verified"
    )

    print(
        "[OK] Positive service cadence:",
        tick_seconds,
    )

    print(
        "[OK] PostgreSQL configuration present"
    )

    print(
        "[OK] Read-only production boundary frozen"
    )

    canonical_launcher = (
        _load_canonical_launcher()
    )

    print(
        "[OK] Certified OLA-072 launcher resolved"
    )

    lock_record = (
        _acquire_runtime_lock()
    )

    print(
        "[START] Oracle guarded continuous runtime"
    )

    print(
        "[INFO] Process ID:",
        lock_record["process_id"],
    )

    print(
        "[INFO] Press Ctrl+C for operator shutdown"
    )

    try:
        exit_code = (
            canonical_launcher.main()
        )

        if exit_code is None:
            exit_code = 0

        return int(
            exit_code
        )

    except KeyboardInterrupt:
        print(
            "\n[STOP] Operator shutdown requested"
        )

        return 130

    finally:
        _release_runtime_lock()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
