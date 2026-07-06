"""
Test OPS-006 Metrics & Performance Engine.
"""

from qseries_v2.ops.metrics_engine import build_metrics_engine


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


class FakeSupervisor:
    def diagnostics(self):
        return {
            "status": "ok",
            "service_count": 5,
            "running_count": 5,
            "error_count": 0,
        }


class FakeScheduler:
    def diagnostics(self):
        return {
            "status": "ok",
            "scheduler_running": True,
            "job_count": 5,
            "running_jobs": 0,
            "error_jobs": 0,
        }


class FakeCache:
    def diagnostics(self):
        return {
            "status": "ok",
            "market_count": 100,
            "refresh_count": 12,
            "error_count": 0,
            "last_refresh_duration_seconds": 0.25,
            "background_running": False,
        }


class FakeStore:
    def diagnostics(self):
        return {
            "status": "ok",
            "observation_count": 500,
            "snapshot_count": 5,
        }


class FakePipeline:
    def diagnostics(self):
        return {
            "status": "ok",
            "record_count": 5,
            "market_rows_recorded": 500,
            "skipped_duplicates": 1,
            "error_count": 0,
            "last_duration_seconds": 0.05,
        }


class FakeWatchdog:
    def diagnostics(self):
        return {
            "status": "ok",
            "check_count": 3,
            "recovery_count": 0,
            "error_count": 0,
        }


def test_ops_006():
    bus = FakeEventBus()

    engine = build_metrics_engine(
        supervisor=FakeSupervisor(),
        scheduler=FakeScheduler(),
        market_cache=FakeCache(),
        historical_store=FakeStore(),
        historical_pipeline=FakePipeline(),
        watchdog=FakeWatchdog(),
        event_bus=bus,
    )

    metrics = engine.collect()

    assert metrics["status"] == "ok"
    assert metrics["health_score"]["score"] == 100
    assert metrics["market_cache"]["market_count"] == 100
    assert metrics["history"]["observation_count"] == 500
    assert metrics["pipeline"]["record_count"] == 5
    assert metrics["watchdog"]["check_count"] == 3

    scorecard = engine.scorecard()
    assert scorecard["markets_cached"] == 100
    assert scorecard["history_rows"] == 500
    assert scorecard["scheduler_jobs"] == 5

    diag = engine.diagnostics()
    assert diag["sample_count"] == 1
    assert len(bus.events) >= 1

    print("[PASS] OPS-006 Metrics & Performance Engine")
    print(scorecard)


if __name__ == "__main__":
    test_ops_006()
