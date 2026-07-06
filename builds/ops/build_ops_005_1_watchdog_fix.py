from pathlib import Path

ROOT = Path("qseries_v2")
OPS = ROOT / "ops"
OPS.mkdir(parents=True, exist_ok=True)

watchdog_code = r'''"""
OPS-005.1 — Watchdog & Auto-Recovery Fix

Fixes OPS-005 state compatibility.
Handles both enum service states and raw string states safely.
"""

import time
from typing import Any, Dict, Optional


class WatchdogError(Exception):
    pass


class QSeriesWatchdog:
    def __init__(
        self,
        supervisor: Any,
        scheduler: Any = None,
        market_cache: Any = None,
        historical_pipeline: Any = None,
        event_bus: Any = None,
        max_cache_error_count: int = 3,
        max_pipeline_error_count: int = 3,
    ):
        if supervisor is None:
            raise WatchdogError("supervisor is required.")

        self.supervisor = supervisor
        self.scheduler = scheduler
        self.market_cache = market_cache
        self.historical_pipeline = historical_pipeline
        self.event_bus = event_bus
        self.max_cache_error_count = int(max_cache_error_count)
        self.max_pipeline_error_count = int(max_pipeline_error_count)

        self.started_at = time.time()
        self.check_count = 0
        self.recovery_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_check_at: Optional[float] = None
        self.last_result: Optional[Dict[str, Any]] = None

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return
        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _state_value(self, value):
        if hasattr(value, "value"):
            return value.value
        return str(value)

    def _safe_supervisor_diagnostics(self):
        try:
            return self.supervisor.diagnostics()
        except Exception:
            services = {}
            raw_services = getattr(self.supervisor, "_services", {})
            for name, service in raw_services.items():
                state = self._state_value(getattr(service, "state", "UNKNOWN"))
                services[name] = {
                    "name": name,
                    "state": state,
                    "restart_on_failure": getattr(service, "restart_on_failure", False),
                    "last_error": getattr(service, "last_error", None),
                }
            return {
                "module": "ops_001_service_supervisor",
                "status": "warning",
                "service_count": len(services),
                "services": services,
            }

    def check_once(self) -> Dict[str, Any]:
        self.check_count += 1
        self.last_check_at = time.time()

        issues = []
        recoveries = []

        try:
            supervisor_diag = self._safe_supervisor_diagnostics()

            for service_name, service in supervisor_diag.get("services", {}).items():
                state = self._state_value(service.get("state"))
                restart_on_failure = bool(service.get("restart_on_failure"))

                if state == "ERROR":
                    issues.append({
                        "kind": "service_error",
                        "service": service_name,
                        "last_error": service.get("last_error"),
                    })

                    if restart_on_failure:
                        recovery = self.supervisor.restart_service(service_name)
                        recoveries.append({
                            "service": service_name,
                            "action": "restart",
                            "result": recovery,
                        })
                        self.recovery_count += 1

            if self.scheduler is not None:
                scheduler_diag = self.scheduler.diagnostics()

                if not scheduler_diag.get("scheduler_running"):
                    issues.append({"kind": "scheduler_not_running"})
                    recovery = self.scheduler.start()
                    recoveries.append({
                        "service": "ops.scheduler",
                        "action": "start",
                        "result": recovery,
                    })
                    self.recovery_count += 1

                for job_name, job in scheduler_diag.get("jobs", {}).items():
                    job_state = self._state_value(job.get("state"))
                    if job.get("error_count", 0) > 0 and job_state == "ERROR":
                        issues.append({
                            "kind": "scheduler_job_error",
                            "job": job_name,
                            "error_count": job.get("error_count"),
                            "last_error": job.get("last_error"),
                        })

            if self.market_cache is not None:
                cache_diag = self.market_cache.diagnostics()
                if cache_diag.get("error_count", 0) >= self.max_cache_error_count:
                    issues.append({
                        "kind": "market_cache_error_threshold",
                        "error_count": cache_diag.get("error_count"),
                        "last_error": cache_diag.get("last_error"),
                    })

            if self.historical_pipeline is not None:
                pipe_diag = self.historical_pipeline.diagnostics()
                if pipe_diag.get("error_count", 0) >= self.max_pipeline_error_count:
                    issues.append({
                        "kind": "history_pipeline_error_threshold",
                        "error_count": pipe_diag.get("error_count"),
                        "last_error": pipe_diag.get("last_error"),
                    })

            result = {
                "module": "ops_005_1_watchdog_auto_recovery",
                "status": "ok" if not issues else "warning",
                "check_count": self.check_count,
                "issues": issues,
                "recoveries": recoveries,
                "recovery_count": self.recovery_count,
                "timestamp": self.last_check_at,
            }

            self.last_result = result
            self.last_error = None
            self._emit("ops.watchdog.checked", result)
            return result

        except Exception as exc:
            self.error_count += 1
            self.last_error = str(exc)

            result = {
                "module": "ops_005_1_watchdog_auto_recovery",
                "status": "error",
                "error": str(exc),
                "error_count": self.error_count,
                "timestamp": time.time(),
            }

            self.last_result = result
            self._emit("ops.watchdog.error", result)
            return result

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "ops_005_1_watchdog_auto_recovery",
            "status": "ok" if self.error_count == 0 else "warning",
            "started_at": self.started_at,
            "check_count": self.check_count,
            "recovery_count": self.recovery_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_check_at": self.last_check_at,
            "last_result": self.last_result,
            "read_only_trading": True,
        }


def build_watchdog(
    supervisor: Any,
    scheduler: Any = None,
    market_cache: Any = None,
    historical_pipeline: Any = None,
    event_bus: Any = None,
) -> QSeriesWatchdog:
    return QSeriesWatchdog(
        supervisor=supervisor,
        scheduler=scheduler,
        market_cache=market_cache,
        historical_pipeline=historical_pipeline,
        event_bus=event_bus,
    )


if __name__ == "__main__":
    print("OPS-005.1 Watchdog fix installed.")
'''

test_code = r'''"""
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
'''

init_code = '''try:
    from .service_supervisor import *
except Exception:
    pass

try:
    from .background_scheduler import *
except Exception:
    pass

try:
    from .qseries_runtime import *
except Exception:
    pass

try:
    from .historical_data_store import *
except Exception:
    pass

try:
    from .historical_recording_pipeline import *
except Exception:
    pass

try:
    from .watchdog import (
        QSeriesWatchdog,
        WatchdogError,
        build_watchdog,
    )
except Exception:
    pass
'''

(OPS / "watchdog.py").write_text(watchdog_code, encoding="utf-8")
(OPS / "__init__.py").write_text(init_code, encoding="utf-8")
Path("test_ops_005_1_watchdog_auto_recovery.py").write_text(test_code, encoding="utf-8")

print("========================================")
print(" OPS-005.1 INSTALLER")
print(" Watchdog Auto-Recovery Fix")
print("========================================")
print("[OK] Wrote qseries_v2\\ops\\watchdog.py")
print("[OK] Wrote qseries_v2\\ops\\__init__.py")
print("[OK] Wrote test_ops_005_1_watchdog_auto_recovery.py")
print()
print("[DONE] OPS-005.1 installed")
print()
print("Run:")
print("python test_ops_005_1_watchdog_auto_recovery.py")