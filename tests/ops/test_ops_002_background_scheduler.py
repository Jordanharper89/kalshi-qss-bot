"""
Test OPS-002 Background Scheduler.
"""

import time

from qseries_v2.ops.background_scheduler import (
    QSeriesBackgroundScheduler,
    BackgroundSchedulerError,
)


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_ops_002():
    bus = FakeEventBus()
    scheduler = QSeriesBackgroundScheduler(event_bus=bus, tick_seconds=0.05)

    state = {"runs": 0}

    def job():
        state["runs"] += 1
        return {"runs": state["runs"]}

    registered = scheduler.register_job(
        name="adp.market_cache.refresh",
        interval_seconds=0.1,
        job_callable=job,
        run_immediately=True,
        metadata={"layer": "ADP", "purpose": "market cache refresh"},
    )

    assert registered["status"] == "ok"

    manual = scheduler.run_job_now("adp.market_cache.refresh")
    assert manual["status"] == "ok"
    assert state["runs"] == 1

    started = scheduler.start()
    assert started["status"] == "started"

    time.sleep(0.35)

    status = scheduler.job_status("adp.market_cache.refresh")
    assert status["run_count"] >= 2
    assert state["runs"] >= 2

    paused = scheduler.pause_job("adp.market_cache.refresh")
    assert paused["state"] == "PAUSED"

    paused_runs = state["runs"]
    time.sleep(0.2)
    assert state["runs"] == paused_runs

    resumed = scheduler.resume_job("adp.market_cache.refresh")
    assert resumed["state"] == "REGISTERED"

    time.sleep(0.2)
    assert state["runs"] > paused_runs

    stopped = scheduler.stop()
    assert stopped["status"] == "stopping"

    diag = scheduler.diagnostics()
    assert diag["job_count"] == 1
    assert len(bus.events) >= 4

    try:
        scheduler.register_job("bad", 0, job)
        raise AssertionError("Bad interval should fail")
    except BackgroundSchedulerError:
        pass

    print("[PASS] OPS-002 Background Scheduler")
    print(diag)


if __name__ == "__main__":
    test_ops_002()
