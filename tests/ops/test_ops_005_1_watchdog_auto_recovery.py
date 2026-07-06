"""
Test OPS-005.1 Watchdog & Auto-Recovery.
"""

from qseries_v2.ops.service_supervisor import build_service_supervisor, ServiceState
from qseries_v2.ops.watchdog import build_watchdog


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


class FakeScheduler:
    def __init__(self):
        self.started = False

    def diagnostics(self):
        return {
            "scheduler_running": self.started,
            "jobs": {},
        }

    def start(self):
        self.started = True
        return {"status": "started"}


class FakeCache:
    def diagnostics(self):
        return {"error_count": 0, "last_error": None}


class FakePipeline:
    def diagnostics(self):
        return {"error_count": 0, "last_error": None}


def test_ops_005_1():
    bus = FakeEventBus()
    supervisor = build_service_supervisor(event_bus=bus)
    scheduler = FakeScheduler()

    state = {"starts": 0, "stops": 0}

    def start_bad_service():
        state["starts"] += 1
        return {"status": "started"}

    def stop_bad_service():
        state["stops"] += 1
        return {"status": "stopped"}

    supervisor.register_service(
        name="test.recoverable",
        start_callable=start_bad_service,
        stop_callable=stop_bad_service,
        restart_on_failure=True,
    )

    supervisor.start_service("test.recoverable")

    supervisor._services["test.recoverable"].state = ServiceState.ERROR
    supervisor._services["test.recoverable"].last_error = "forced failure"

    watchdog = build_watchdog(
        supervisor=supervisor,
        scheduler=scheduler,
        market_cache=FakeCache(),
        historical_pipeline=FakePipeline(),
        event_bus=bus,
    )

    result = watchdog.check_once()

    assert result["status"] == "warning"
    assert len(result["issues"]) >= 1
    assert len(result["recoveries"]) >= 1
    assert scheduler.started is True

    diag = watchdog.diagnostics()
    assert diag["check_count"] == 1
    assert diag["recovery_count"] >= 1
    assert len(bus.events) >= 1

    print("[PASS] OPS-005.1 Watchdog & Auto-Recovery Fix")
    print(diag)


if __name__ == "__main__":
    test_ops_005_1()
