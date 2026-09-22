from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import oracle_live_shadow_operator as operator


def main() -> int:
    assert operator.SCHEMA_VERSION == "OLA-064"
    assert operator.ENGINE_ID == "OLA-064"

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        pid_file = root / "oracle.pid.json"
        state_file = root / "state" / "current.json"
        log_root = root / "logs"
        output_log = root / "operator.log"

        state_file.parent.mkdir(parents=True)
        log_root.mkdir(parents=True)
        state_file.write_text('{"status":"ok"}\n', encoding="utf-8")

        runtime_log = log_root / "run-a" / "iteration-a" / "log.json"
        runtime_log.parent.mkdir(parents=True)
        runtime_log.write_text('{"status":"ok"}\n', encoding="utf-8")

        now = time.time()
        state_file.touch()
        runtime_log.touch()

        pid_file.write_text(
            json.dumps(
                {
                    "schema_version": "OLA-064",
                    "engine_id": "OLA-064",
                    "pid": 43210,
                    "read_only": True,
                    "execution_allowed": False,
                }
            ),
            encoding="utf-8",
        )

        with (
            patch.object(operator, "PID_FILE", pid_file),
            patch.object(operator, "ACTIVE_STATE_FILE", state_file),
            patch.object(operator, "ACTIVE_LOG_ROOT", log_root),
            patch.object(operator, "OUTPUT_LOG", output_log),
            patch.object(operator, "_process_is_alive", return_value=True),
        ):
            payload = operator._status_payload(stale_seconds=30)

        assert payload["status"] == "RUNNING"
        assert payload["process_alive"] is True
        assert payload["runtime_fresh"] is True
        assert payload["pid"] == 43210
        assert payload["read_only"] is True
        assert payload["execution_allowed"] is False

        with (
            patch.object(operator, "PID_FILE", pid_file),
            patch.object(operator, "ACTIVE_STATE_FILE", state_file),
            patch.object(operator, "ACTIVE_LOG_ROOT", log_root),
            patch.object(operator, "_process_is_alive", return_value=False),
        ):
            stopped_payload = operator._status_payload(stale_seconds=30)

        assert stopped_payload["status"] == "STOPPED"
        assert stopped_payload["runtime_fresh"] is False

    print("[PASS] OLA-064 Oracle Live Shadow Operator Control")
    print(
        {
            "schema_version": "OLA-064",
            "engine_id": "OLA-064",
            "status": "passed",
            "read_only": True,
            "execution_allowed": False,
            "commands": ("start", "status", "tail", "stop"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
