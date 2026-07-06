from pathlib import Path

ROOT = Path("qseries_v2")
OPS = ROOT / "ops"
OPS.mkdir(parents=True, exist_ok=True)

runtime_code = r'''"""
OPS-002.1 — Q Series Runtime Bootstrap

Master runtime for Q Series V2.3.

Starts:
- Event Bus placeholder if available later
- ADP-012 Live Kalshi Market Ingestion
- ADP-013 Live Market Cache
- OPS-001 Service Supervisor
- OPS-002 Background Scheduler

Read-only only.
Oracle does not execute trades.
Q Series execution remains separate.
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
        oracle_scan_seconds: float = 60.0,
        diagnostics_seconds: float = 300.0,
        event_bus: Any = None,
    ):
        self.environment = environment
        self.cache_refresh_seconds = float(cache_refresh_seconds)
        self.oracle_scan_seconds = float(oracle_scan_seconds)
        self.diagnostics_seconds = float(diagnostics_seconds)
        self.event_bus = event_bus

        self.started_at: Optional[float] = None
        self.stopped_at: Optional[float] = None
        self.boot_status = "created"

        self.ingestion = None
        self.market_cache = None
        self.supervisor = None
        self.scheduler = None

    def boot(self) -> Dict[str, Any]:
        self.started_at = time.time()
        self.boot_status = "booting"

        try:
            from qseries_v2.adapters.live_kalshi_market_ingestion import (
                build_live_kalshi_market_ingestion,
            )
            from qseries_v2.adapters.live_market_cache import build_live_market_cache
            from qseries_v2.ops.service_supervisor import build_service_supervisor
            from qseries_v2.ops.background_scheduler import build_background_scheduler

            self.ingestion = build_live_kalshi_market_ingestion(
                environment=self.environment,
                event_bus=self.event_bus,
            )

            self.market_cache = build_live_market_cache(
                ingestion=self.ingestion,
                event_bus=self.event_bus,
                refresh_interval_seconds=self.cache_refresh_seconds,
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

            self.scheduler.register_job(
                name="adp.market_cache.refresh",
                interval_seconds=self.cache_refresh_seconds,
                job_callable=lambda: self.market_cache.refresh(limit=1000, max_pages=3),
                run_immediately=True,
                metadata={"layer": "ADP", "purpose": "live market cache refresh"},
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

            self.boot_status = "running"

            return {
                "module": "ops_002_1_qseries_runtime",
                "status": "ok",
                "environment": self.environment,
                "started_at": self.started_at,
                "services": self.supervisor.diagnostics(),
                "scheduler": self.scheduler.diagnostics(),
                "market_cache": self.market_cache.diagnostics(),
                "read_only": True,
            }

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
            "module": "ops_002_1_qseries_runtime",
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
            "module": "ops_002_1_qseries_runtime",
            "status": self.boot_status,
            "environment": self.environment,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "uptime_seconds": time.time() - self.started_at if self.started_at else None,
            "cache_refresh_seconds": self.cache_refresh_seconds,
            "oracle_scan_seconds": self.oracle_scan_seconds,
            "diagnostics_seconds": self.diagnostics_seconds,
            "supervisor": self.supervisor.diagnostics() if self.supervisor else None,
            "scheduler": self.scheduler.diagnostics() if self.scheduler else None,
            "market_cache": self.market_cache.diagnostics() if self.market_cache else None,
            "read_only": True,
        }


def build_qseries_runtime(
    environment: str = "production",
    cache_refresh_seconds: float = 30.0,
    oracle_scan_seconds: float = 60.0,
    diagnostics_seconds: float = 300.0,
    event_bus: Any = None,
) -> QSeriesRuntime:
    return QSeriesRuntime(
        environment=environment,
        cache_refresh_seconds=cache_refresh_seconds,
        oracle_scan_seconds=oracle_scan_seconds,
        diagnostics_seconds=diagnostics_seconds,
        event_bus=event_bus,
    )


if __name__ == "__main__":
    runtime = build_qseries_runtime(environment="production")
    boot = runtime.boot()

    print("======================================")
    print(" Q SERIES V2.3 RUNTIME")
    print("======================================")
    print("Status:", boot["status"])
    print("Environment:", boot["environment"])
    print("Read Only:", boot["read_only"])
    print("Scheduler:", boot["scheduler"]["status"])
    print("Market Cache:", boot["market_cache"]["status"])
    print("System Ready.")
    print()
    print("Press CTRL+C to stop.")

    try:
        while True:
            time.sleep(5)
            diag = runtime.diagnostics()
            cache = diag.get("market_cache") or {}
            print(
                "[heartbeat]",
                "runtime=", diag.get("status"),
                "markets=", cache.get("market_count"),
                "refreshes=", cache.get("refresh_count"),
                "errors=", cache.get("error_count"),
            )
    except KeyboardInterrupt:
        print()
        print(runtime.shutdown())
'''

test_code = r'''"""
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
'''

(OPS / "qseries_runtime.py").write_text(runtime_code, encoding="utf-8")
(OPS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_ops_002_1_qseries_runtime.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" OPS-002.1 INSTALLER")
print(" Q Series Runtime Bootstrap")
print("========================================")
print("[OK] Wrote qseries_v2\\ops\\qseries_runtime.py")
print("[OK] Wrote qseries_v2\\ops\\__init__.py")
print("[OK] Wrote test_ops_002_1_qseries_runtime.py")
print()
print("[DONE] OPS-002.1 installed")
print()
print("Run:")
print("python test_ops_002_1_qseries_runtime.py")
print()
print("Optional runtime launch:")
print("python -m qseries_v2.ops.qseries_runtime")