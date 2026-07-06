"""
Test OPS-001 Service Supervisor.
"""

from qseries_v2.ops.service_supervisor import (
    QSeriesServiceSupervisor,
    ServiceSupervisorError,
)


class FakeService:
    def __init__(self):
        self.running = False
        self.starts = 0
        self.stops = 0

    def start(self):
        self.running = True
        self.starts += 1
        return {"started": True}

    def stop(self):
        self.running = False
        self.stops += 1
        return {"stopped": True}

    def health(self):
        return {
            "status": "ok" if self.running else "stopped",
            "starts": self.starts,
            "stops": self.stops,
        }


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_001():
    bus = FakeEventBus()
    supervisor = QSeriesServiceSupervisor(event_bus=bus)
    fake = FakeService()

    registered = supervisor.register_service(
        name="adp.market_cache",
        start_callable=fake.start,
        stop_callable=fake.stop,
        health_callable=fake.health,
        restart_on_failure=True,
        metadata={"layer": "ADP", "build": "ADP-013"},
    )

    assert registered["status"] == "ok"

    started = supervisor.start_service("adp.market_cache")
    assert started["status"] == "ok"
    assert fake.running is True

    second_start = supervisor.start_service("adp.market_cache")
    assert second_start["status"] == "already_running"

    status = supervisor.service_status("adp.market_cache")
    assert status["state"] == "RUNNING"
    assert status["health"]["status"] == "ok"
    assert status["metadata"]["build"] == "ADP-013"

    restarted = supervisor.restart_service("adp.market_cache")
    assert restarted["status"] == "ok"
    assert fake.running is True

    stopped = supervisor.stop_service("adp.market_cache")
    assert stopped["status"] == "ok"
    assert fake.running is False

    diag = supervisor.diagnostics()
    assert diag["service_count"] == 1
    assert diag["running_count"] == 0
    assert len(bus.events) >= 4

    try:
        supervisor.start_service("missing.service")
        raise AssertionError("Missing service should fail")
    except ServiceSupervisorError:
        pass

    print("[PASS] OPS-001 Service Supervisor")
    print(diag)


if __name__ == "__main__":
    test_ops_001()
