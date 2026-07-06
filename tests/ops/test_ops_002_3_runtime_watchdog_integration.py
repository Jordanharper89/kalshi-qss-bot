"""
Test OPS-002.3 Runtime Watchdog Integration.
"""

import time
import tempfile
from pathlib import Path

from qseries_v2.ops.qseries_runtime import build_qseries_runtime


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_002_3():
    bus = FakeEventBus()
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "runtime_watchdog.sqlite3")

    runtime = build_qseries_runtime(
        environment="demo",
        cache_refresh_seconds=0.2,
        history_record_seconds=0.25,
        oracle_scan_seconds=0.4,
        watchdog_seconds=0.3,
        diagnostics_seconds=0.5,
        history_db_path=db_path,
        event_bus=bus,
    )

    boot = runtime.boot()

    assert boot["status"] == "running"
    assert boot["read_only"] is True
    assert runtime.watchdog is not None
    assert runtime.scheduler is not None

    runtime.watchdog.check_once()

    time.sleep(0.95)

    diag = runtime.diagnostics()

    assert diag["status"] == "running"
    assert diag["scheduler"]["job_count"] == 5
    assert "ops.watchdog.check" in diag["scheduler"]["jobs"]
    assert diag["watchdog"]["check_count"] >= 1
    assert diag["supervisor"]["service_count"] == 5

    shutdown = runtime.shutdown()
    assert shutdown["status"] == "stopped"

    print("[PASS] OPS-002.3 Runtime Watchdog Integration")
    print({
        "runtime_status": diag["status"],
        "scheduler_jobs": diag["scheduler"]["job_count"],
        "services": diag["supervisor"]["service_count"],
        "watchdog_checks": diag["watchdog"]["check_count"],
        "watchdog_recoveries": diag["watchdog"]["recovery_count"],
        "events": len(bus.events),
    })


if __name__ == "__main__":
    test_ops_002_3()
