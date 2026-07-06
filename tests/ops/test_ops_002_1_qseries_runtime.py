"""
Test OPS-002.1 Q Series Runtime Bootstrap.
"""

import time

from qseries_v2.ops.qseries_runtime import build_qseries_runtime


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_002_1():
    bus = FakeEventBus()

    runtime = build_qseries_runtime(
        environment="demo",
        cache_refresh_seconds=0.2,
        oracle_scan_seconds=0.3,
        diagnostics_seconds=0.5,
        event_bus=bus,
    )

    boot = runtime.boot()

    assert boot["status"] == "ok"
    assert boot["read_only"] is True
    assert runtime.supervisor is not None
    assert runtime.scheduler is not None
    assert runtime.market_cache is not None

    time.sleep(0.7)

    diag = runtime.diagnostics()

    assert diag["status"] == "running"
    assert diag["scheduler"]["scheduler_running"] is True
    assert diag["scheduler"]["job_count"] == 3
    assert "adp.market_cache.refresh" in diag["scheduler"]["jobs"]

    shutdown = runtime.shutdown()
    assert shutdown["status"] == "stopped"

    print("[PASS] OPS-002.1 Q Series Runtime Bootstrap")
    print({
        "runtime_status": diag["status"],
        "scheduler_jobs": diag["scheduler"]["job_count"],
        "services": diag["supervisor"]["service_count"],
        "events": len(bus.events),
    })


if __name__ == "__main__":
    test_ops_002_1()
