"""
Test OPS-002.2 Runtime Historical Pipeline Integration.
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


def test_ops_002_2():
    bus = FakeEventBus()
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "runtime_history.sqlite3")

    runtime = build_qseries_runtime(
        environment="demo",
        cache_refresh_seconds=0.2,
        history_record_seconds=0.25,
        oracle_scan_seconds=0.4,
        diagnostics_seconds=0.5,
        history_db_path=db_path,
        event_bus=bus,
    )

    boot = runtime.boot()

    assert boot["status"] == "running"
    assert boot["read_only"] is True
    assert runtime.historical_store is not None
    assert runtime.historical_pipeline is not None
    assert runtime.scheduler is not None

    time.sleep(0.9)

    diag = runtime.diagnostics()

    assert diag["status"] == "running"
    assert diag["scheduler"]["job_count"] == 4
    assert "ops.history.record_snapshot" in diag["scheduler"]["jobs"]
    assert diag["historical_store"]["status"] == "ok"
    assert diag["historical_pipeline"]["status"] in ("ok", "warning")

    shutdown = runtime.shutdown()
    assert shutdown["status"] == "stopped"

    print("[PASS] OPS-002.2 Runtime Historical Pipeline Integration")
    print({
        "runtime_status": diag["status"],
        "scheduler_jobs": diag["scheduler"]["job_count"],
        "services": diag["supervisor"]["service_count"],
        "history_observations": diag["historical_store"]["observation_count"],
        "history_snapshots": diag["historical_store"]["snapshot_count"],
        "pipeline_records": diag["historical_pipeline"]["record_count"],
        "events": len(bus.events),
    })


if __name__ == "__main__":
    test_ops_002_2()
