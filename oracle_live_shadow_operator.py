from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "OLA-064"
ENGINE_ID = "OLA-064"

ROOT = Path(__file__).resolve().parent
LAUNCHER = ROOT / "run_oracle_live_shadow_FINAL_FIXED.py"
OPERATOR_ROOT = ROOT / "runtime" / "oracle_operator"
PID_FILE = OPERATOR_ROOT / "oracle_live_shadow.pid.json"
OUTPUT_LOG = OPERATOR_ROOT / "oracle_live_shadow.stdout.log"
ACTIVE_STATE_FILE = ROOT / "state" / "current.json"
ACTIVE_LOG_ROOT = ROOT / "logs"
DEFAULT_STALE_SECONDS = 30


class OracleOperatorError(RuntimeError):
    pass


def _utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_operator_root() -> None:
    OPERATOR_ROOT.mkdir(parents=True, exist_ok=True)


def _read_pid_record() -> dict[str, Any] | None:
    if not PID_FILE.exists():
        return None

    try:
        payload = json.loads(PID_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleOperatorError(
            f"Could not read operator PID file: {PID_FILE}"
        ) from exc

    if not isinstance(payload, dict):
        raise OracleOperatorError(
            "Operator PID file must contain a JSON object"
        )

    return payload


def _write_pid_record(pid: int) -> None:
    _ensure_operator_root()

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "service": "oracle_live_shadow",
        "pid": pid,
        "started_at": _utc_now_text(),
        "launcher": str(LAUNCHER.resolve()),
        "read_only": True,
        "execution_allowed": False,
    }

    temporary = PID_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, PID_FILE)


def _remove_pid_file() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def _process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name == "nt":
        completed = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        text = completed.stdout.strip()
        return bool(
            completed.returncode == 0
            and text
            and "No tasks are running" not in text
            and f'"{pid}"' in text
        )

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def _newest_runtime_log() -> Path | None:
    if not ACTIVE_LOG_ROOT.exists():
        return None

    candidates = [
        path
        for path in ACTIVE_LOG_ROOT.rglob("*.json")
        if path.is_file()
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: (path.stat().st_mtime_ns, str(path)),
    )


def _age_seconds(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    return max(0.0, time.time() - path.stat().st_mtime)


def _format_age(age: float | None) -> str:
    return "missing" if age is None else f"{age:.1f} seconds"


def _status_payload(
    *,
    stale_seconds: int = DEFAULT_STALE_SECONDS,
) -> dict[str, Any]:
    record = _read_pid_record()
    pid = None
    alive = False

    if record is not None:
        raw_pid = record.get("pid")
        if isinstance(raw_pid, int):
            pid = raw_pid
            alive = _process_is_alive(pid)

    newest_log = _newest_runtime_log()
    state_age = _age_seconds(ACTIVE_STATE_FILE)
    log_age = _age_seconds(newest_log)

    fresh = (
        alive
        and state_age is not None
        and log_age is not None
        and state_age <= stale_seconds
        and log_age <= stale_seconds
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "pid_record_exists": record is not None,
        "pid": pid,
        "process_alive": alive,
        "state_file": str(ACTIVE_STATE_FILE.resolve()),
        "state_age_seconds": state_age,
        "newest_log": (
            str(newest_log.resolve()) if newest_log is not None else None
        ),
        "newest_log_age_seconds": log_age,
        "freshness_limit_seconds": stale_seconds,
        "runtime_fresh": fresh,
        "status": (
            "RUNNING"
            if fresh
            else "ALIVE_BUT_STALE"
            if alive
            else "STOPPED"
        ),
        "read_only": True,
        "execution_allowed": False,
    }


def _print_status(*, stale_seconds: int = DEFAULT_STALE_SECONDS) -> int:
    payload = _status_payload(stale_seconds=stale_seconds)

    print("========================================")
    print(" ORACLE LIVE SHADOW STATUS")
    print(" READ-ONLY OPERATOR CONTROL")
    print("========================================")
    print(f"[STATUS] {payload['status']}")
    print(f"[INFO] PID: {payload['pid']}")
    print(f"[INFO] Process alive: {payload['process_alive']}")
    print(
        "[INFO] state\\current.json age: "
        f"{_format_age(payload['state_age_seconds'])}"
    )
    print(
        "[INFO] newest runtime log age: "
        f"{_format_age(payload['newest_log_age_seconds'])}"
    )
    print(f"[INFO] Freshness limit: {stale_seconds} seconds")
    print(f"[INFO] Operator output log: {OUTPUT_LOG.resolve()}")

    if payload["runtime_fresh"]:
        print("[PASS] Oracle is alive and producing fresh runtime evidence")
        return 0

    if payload["process_alive"]:
        print(
            "[WARN] Oracle process exists but fresh runtime "
            "evidence was not proved"
        )
        return 2

    print("[INFO] Oracle is not running")
    return 1


def _start() -> int:
    if not LAUNCHER.exists():
        raise OracleOperatorError(
            f"Persistent launcher is missing: {LAUNCHER}"
        )

    existing = _read_pid_record()
    if existing is not None:
        raw_pid = existing.get("pid")
        if isinstance(raw_pid, int) and _process_is_alive(raw_pid):
            print(f"[BLOCKED] Oracle is already running under PID {raw_pid}")
            return 2
        print("[INFO] Removing stale operator PID file")
        _remove_pid_file()

    _ensure_operator_root()
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
        )

    output_handle = OUTPUT_LOG.open("a", encoding="utf-8", buffering=1)
    output_handle.write(
        "\n========================================\n"
        f" OLA-064 OPERATOR START {_utc_now_text()}\n"
        "========================================\n"
    )
    output_handle.flush()

    try:
        process = subprocess.Popen(
            [sys.executable, str(LAUNCHER)],
            cwd=str(ROOT),
            stdin=subprocess.DEVNULL,
            stdout=output_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=(os.name != "nt"),
        )
    except BaseException:
        output_handle.close()
        raise

    output_handle.close()
    _write_pid_record(process.pid)

    print("========================================")
    print(" ORACLE LIVE SHADOW START")
    print(" READ-ONLY OPERATOR CONTROL")
    print("========================================")
    print(f"[OK] Process started under PID {process.pid}")
    print(f"[INFO] Output: {OUTPUT_LOG.resolve()}")
    print("[INFO] Waiting for fresh runtime evidence...")

    deadline = time.time() + 30
    while time.time() < deadline:
        payload = _status_payload(stale_seconds=30)
        if payload["runtime_fresh"]:
            print(
                "[PASS] Oracle is running and fresh runtime "
                "evidence is advancing"
            )
            return 0
        if not payload["process_alive"]:
            print("[FAIL] Oracle exited during startup")
            print(f"[INFO] Review: {OUTPUT_LOG.resolve()}")
            _remove_pid_file()
            return 1
        time.sleep(2)

    print(
        "[WARN] Process remains alive, but fresh runtime "
        "evidence was not proved within 30 seconds"
    )
    print(f"[INFO] Review: {OUTPUT_LOG.resolve()}")
    return 2


def _stop() -> int:
    record = _read_pid_record()
    if record is None:
        print("[INFO] Oracle is already stopped")
        return 0

    raw_pid = record.get("pid")
    if not isinstance(raw_pid, int):
        _remove_pid_file()
        raise OracleOperatorError(
            "Operator PID file does not contain a valid PID"
        )

    if not _process_is_alive(raw_pid):
        print(f"[INFO] PID {raw_pid} is no longer running")
        _remove_pid_file()
        return 0

    print("========================================")
    print(" ORACLE LIVE SHADOW STOP")
    print(" READ-ONLY OPERATOR CONTROL")
    print("========================================")
    print(f"[INFO] Stopping PID {raw_pid}")

    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(raw_pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise OracleOperatorError(
                "Windows taskkill failed: "
                + (
                    completed.stderr.strip()
                    or completed.stdout.strip()
                    or "unknown taskkill error"
                )
            )
    else:
        os.kill(raw_pid, signal.SIGTERM)
        deadline = time.time() + 10
        while time.time() < deadline and _process_is_alive(raw_pid):
            time.sleep(0.25)
        if _process_is_alive(raw_pid):
            os.kill(raw_pid, signal.SIGKILL)

    _remove_pid_file()
    print("[PASS] Oracle process stopped")
    return 0


def _tail(lines: int) -> int:
    if lines < 1:
        raise OracleOperatorError("--lines must be greater than zero")

    if not OUTPUT_LOG.exists():
        print(f"[INFO] Operator output log does not exist: {OUTPUT_LOG}")
        return 1

    content = OUTPUT_LOG.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()

    for line in content[-lines:]:
        print(line)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OLA-064 Oracle live-shadow operator control"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start")
    subparsers.add_parser("stop")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument(
        "--stale-seconds",
        type=int,
        default=DEFAULT_STALE_SECONDS,
    )

    tail_parser = subparsers.add_parser("tail")
    tail_parser.add_argument("--lines", type=int, default=40)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        if arguments.command == "start":
            return _start()
        if arguments.command == "stop":
            return _stop()
        if arguments.command == "status":
            if arguments.stale_seconds < 1:
                raise OracleOperatorError(
                    "--stale-seconds must be greater than zero"
                )
            return _print_status(stale_seconds=arguments.stale_seconds)
        if arguments.command == "tail":
            return _tail(arguments.lines)
        raise OracleOperatorError(f"Unsupported command: {arguments.command}")
    except OracleOperatorError as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
