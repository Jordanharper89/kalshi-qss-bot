from pathlib import Path

ROOT = Path("qseries_v2")
OPS = ROOT / "ops"
OPS.mkdir(parents=True, exist_ok=True)

runtime_code = r'''"""
OPS-002.2 — Runtime Historical Pipeline Integration

Adds OPS-003 Historical Data Store and OPS-004 Historical Recording Pipeline
to the Q Series runtime.

Q Series now boots into:
- live market ingestion
- live market cache
- scheduler
- supervisor
- historical database
- automatic snapshot recording

Read-only trading.
No execution.
"""

import time
from typing import Any, Dict, Optional


class QSeriesRuntimeError(Exception):
    pass


class QSeriesRuntime:
    def __init__(
        self,
        environment: str = "production",
        cache_refresh_seconds: float = 30.0,
        history_record_seconds: float = 30.0,
        oracle_scan_seconds: float = 60.0,
        diagnostics_seconds: float = 300.0,
        history_db_path: str = "qseries_v2/data/qseries_history.sqlite3",
        event_bus: Any = None,
    ):
        self.environment = environment
        self.cache_refresh_seconds = float(cache_refresh_seconds)
        self.history_record_seconds = float(history_record_seconds)
        self.oracle_scan_seconds = float(oracle_scan_seconds)
        self.diagnostics_seconds = float(diagnostics_seconds)
        self.history_db_path = history_db_path
        self.event_bus = event_bus

        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        self.boot_status = "created"

        self.ingestion = None
        self.market_cache = None
        self.historical_store = None
        self.historical_pipeline = None
        self.supervisor = None
        self.scheduler = None

    def boot(self) -> Dict[str, Any]:
        self.started_at = time.time()
        self.boot_status = "booting"

        try:
            from qseries_v2.adapters.live_kalshi_market_ingestion import build_live_kalshi_market_ingestion
            from qseries_v2.adapters.live_market_cache import build_live_market_cache
            from qseries_v2.ops.service_supervisor import build_service_supervisor
            from qseries_v2.ops.background_scheduler import build_background_scheduler
            from qseries_v2.ops.historical_data_store import build_historical_data_store
            from qseries_v2.ops.historical_recording_pipeline import build_historical_recording_pipeline

            self.ingestion = build_live_kalshi_market_ingestion(
                environment=self.environment,
                event_bus=self.event_bus,
            )

            self.market_cache = build_live_market_cache(
                ingestion=self.ingestion,
                event_bus=self.event_bus,
                refresh_interval_seconds=self.cache_refresh_seconds,
            )

            self.historical_store = build_historical_data_store(
                db_path=self.history_db_path,
                event_bus=self.event_bus,
            )

            self.historical_pipeline = build_historical_recording_pipeline(
                market_cache=self.market_cache,
                historical_store=self.historical_store,
                event_bus=self.event_bus,
                skip_duplicates=True,
                source="runtime.market_cache",
            )

            self.supervisor = build_service_supervisor(event_bus=self.event_bus)
            self.scheduler = build_background_scheduler(event_bus=self.event_bus)

            self.supervisor.register_service(
                name="ops.scheduler",
                start_callable=self.scheduler.start,
                stop_callable=self.scheduler.stop,
                health_callable=self.scheduler.diagnostics,
                restart_on_failure=True,
                metadata={"layer": "OPS", "build": "OPS-002"},
            )

            self.supervisor.register_service(
                name="adp.market_cache",
                start_callable=lambda: {"status": "managed_by_scheduler"},
                stop_callable=lambda: {"status": "managed_by_scheduler"},
                health_callable=self.market_cache.diagnostics,
                restart_on_failure=True,
                metadata={"layer": "ADP", "build": "ADP-013"},
            )

            self.supervisor.register_service(
                name="ops.history_store",
                start_callable=lambda: {"status": "ready", "db_path": self.history_db_path},
                stop_callable=lambda: {"status": "closed"},
                health_callable=self.historical_store.diagnostics,
                restart_on_failure=False,
                metadata={"layer": "OPS", "build": "OPS-003"},
            )

            self.supervisor.register_service(
                name="ops.history_pipeline",
                start_callable=lambda: {"status": "managed_by_scheduler"},
                stop_callable=lambda: {"status": "managed_by_scheduler"},
                health_callable=self.historical_pipeline.diagnostics,
                restart_on_failure=True,
                metadata={"layer": "OPS", "build": "OPS-004"},
            )

            self.scheduler.register_job(
                name="adp.market_cache.refresh",
                interval_seconds=self.cache_refresh_seconds,
                job_callable=lambda: self.market_cache.refresh(limit=1000, max_pages=3),
                run_immediately=True,
                metadata={"layer": "ADP", "purpose": "live market cache refresh"},
            )

            self.scheduler.register_job(
                name="ops.history.record_snapshot",
                interval_seconds=self.history_record_seconds,
                job_callable=lambda: self.historical_pipeline.record_current_snapshot(
                    metadata={"runtime": "OPS-002.2"}
                ),
                run_immediately=False,
                metadata={"layer": "OPS", "purpose": "record market cache to historical database"},
            )

            self.scheduler.register_job(
                name="oracle.scan.placeholder",
                interval_seconds=self.oracle_scan_seconds,
                job_callable=self._oracle_scan_placeholder,
                run_immediately=False,
                metadata={"layer": "OI", "purpose": "future Oracle live scan"},
            )

            self.scheduler.register_job(
                name="runtime.diagnostics.heartbeat",
                interval_seconds=self.diagnostics_seconds,
                job_callable=self._heartbeat,
                run_immediately=False,
                metadata={"layer": "OPS", "purpose": "runtime diagnostics"},
            )

            self.supervisor.start_service("ops.scheduler")
            self.supervisor.start_service("adp.market_cache")
            self.supervisor.start_service("ops.history_store")
            self.supervisor.start_service("ops.history_pipeline")

            self.boot_status = "running"

            return self.diagnostics()

        except Exception as exc:
            self.boot_status = "error"
            raise QSeriesRuntimeError(str(exc)) from exc

    def shutdown(self) -> Dict[str, Any]:
        self.stopped_at = time.time()

        results = {}
        if self.supervisor:
            results = self.supervisor.stop_all()

        self.boot_status = "stopped"

        return {
            "module": "ops_002_2_runtime_history_integration",
            "status": "stopped",
            "stopped_at": self.stopped_at,
            "results": results,
        }

    def _oracle_scan_placeholder(self) -> Dict[str, Any]:
        count = 0
        if self.market_cache:
            count = len(self.market_cache.get_all_markets())

        return {
            "status": "placeholder",
            "message": "Oracle live scan hook ready. Full Oracle scanner integration comes next.",
            "cached_markets": count,
            "timestamp": time.time(),
        }

    def _heartbeat(self) -> Dict[str, Any]:
        return self.diagnostics()

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "ops_002_2_runtime_history_integration",
            "status": self.boot_status,
            "environment": self.environment,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "uptime_seconds": time.time() - self.started_at if self.started_at else None,
            "cache_refresh_seconds": self.cache_refresh_seconds,
            "history_record_seconds": self.history_record_seconds,
            "oracle_scan_seconds": self.oracle_scan_seconds,
            "diagnostics_seconds": self.diagnostics_seconds,
            "history_db_path": self.history_db_path,
            "supervisor": self.supervisor.diagnostics() if self.supervisor else None,
            "scheduler": self.scheduler.diagnostics() if self.scheduler else None,
            "market_cache": self.market_cache.diagnostics() if self.market_cache else None,
            "historical_store": self.historical_store.diagnostics() if self.historical_store else None,
            "historical_pipeline": self.historical_pipeline.diagnostics() if self.historical_pipeline else None,
            "read_only": True,
        }


def build_qseries_runtime(
    environment: str = "production",
    cache_refresh_seconds: float = 30.0,
    history_record_seconds: float = 30.0,
    oracle_scan_seconds: float = 60.0,
    diagnostics_seconds: float = 300.0,
    history_db_path: str = "qseries_v2/data/qseries_history.sqlite3",
    event_bus: Any = None,
) -> QSeriesRuntime:
    return QSeriesRuntime(
        environment=environment,
        cache_refresh_seconds=cache_refresh_seconds,
        history_record_seconds=history_record_seconds,
        oracle_scan_seconds=oracle_scan_seconds,
        diagnostics_seconds=diagnostics_seconds,
        history_db_path=history_db_path,
        event_bus=event_bus,
    )


if __name__ == "__main__":
    runtime = build_qseries_runtime(environment="production")
    boot = runtime.boot()

    print("======================================")
    print(" Q SERIES V2.3 RUNTIME + HISTORY")
    print("======================================")
    print("Status:", boot["status"])
    print("Environment:", boot["environment"])
    print("Read Only:", boot["read_only"])
    print("History DB:", boot["history_db_path"])
    print("Scheduler:", boot["scheduler"]["status"])
    print("Market Cache:", boot["market_cache"]["status"])
    print("Historical Store:", boot["historical_store"]["status"])
    print("Historical Pipeline:", boot["historical_pipeline"]["status"])
    print("System Ready.")
    print()
    print("Press CTRL+C to stop.")

    try:
        while True:
            time.sleep(5)
            diag = runtime.diagnostics()
            cache = diag.get("market_cache") or {}
            store = diag.get("historical_store") or {}
            pipeline = diag.get("historical_pipeline") or {}
            print(
                "[heartbeat]",
                "runtime=", diag.get("status"),
                "markets=", cache.get("market_count"),
                "cache_refreshes=", cache.get("refresh_count"),
                "history_rows=", store.get("observation_count"),
                "snapshots=", store.get("snapshot_count"),
                "recorded=", pipeline.get("record_count"),
                "skipped=", pipeline.get("skipped_duplicates"),
                "errors=", pipeline.get("error_count"),
            )
    except KeyboardInterrupt:
        print()
        print(runtime.shutdown())
'''

test_code = r'''"""
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
'''

init_code = '''try:
    from .service_supervisor import (
        ServiceState,
        ManagedService,
        QSeriesServiceSupervisor,
        ServiceSupervisorError,
        build_service_supervisor,
    )
except Exception:
    pass

try:
    from .background_scheduler import (
        SchedulerJobState,
        ScheduledJob,
        QSeriesBackgroundScheduler,
        BackgroundSchedulerError,
        build_background_scheduler,
    )
except Exception:
    pass

try:
    from .qseries_runtime import (
        QSeriesRuntime,
        QSeriesRuntimeError,
        build_qseries_runtime,
    )
except Exception:
    pass

try:
    from .historical_data_store import (
        HistoricalDataStore,
        HistoricalDataStoreError,
        build_historical_data_store,
    )
except Exception:
    pass

try:
    from .historical_recording_pipeline import (
        HistoricalRecordingPipeline,
        HistoricalRecordingPipelineError,
        build_historical_recording_pipeline,
    )
except Exception:
    pass
'''

(OPS / "qseries_runtime.py").write_text(runtime_code, encoding="utf-8")
(OPS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_ops_002_2_runtime_history_integration.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" OPS-002.2 INSTALLER")
print(" Runtime Historical Pipeline Integration")
print("========================================")
print("[OK] Wrote qseries_v2\\ops\\qseries_runtime.py")
print("[OK] Wrote qseries_v2\\ops\\__init__.py")
print("[OK] Wrote test_ops_002_2_runtime_history_integration.py")
print()
print("[DONE] OPS-002.2 installed")
print()
print("Run:")
print("python test_ops_002_2_runtime_history_integration.py")
print()
print("Optional runtime launch:")
print("python -m qseries_v2.ops.qseries_runtime")