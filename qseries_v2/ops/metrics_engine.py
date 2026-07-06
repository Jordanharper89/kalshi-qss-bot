"""
OPS-006 — Metrics & Performance Engine

Purpose:
- Collect runtime performance metrics.
- Track scheduler, supervisor, cache, history, pipeline, and watchdog health.
- Produce compact system scorecards for dashboards and Telegram.
- No trading logic.
"""

import time
from typing import Any, Dict, Optional


class MetricsEngineError(Exception):
    pass


class QSeriesMetricsEngine:
    def __init__(
        self,
        supervisor: Any = None,
        scheduler: Any = None,
        market_cache: Any = None,
        historical_store: Any = None,
        historical_pipeline: Any = None,
        watchdog: Any = None,
        event_bus: Any = None,
    ):
        self.supervisor = supervisor
        self.scheduler = scheduler
        self.market_cache = market_cache
        self.historical_store = historical_store
        self.historical_pipeline = historical_pipeline
        self.watchdog = watchdog
        self.event_bus = event_bus

        self.started_at = time.time()
        self.sample_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.last_sample_at: Optional[float] = None
        self.last_metrics: Optional[Dict[str, Any]] = None

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

    def collect(self) -> Dict[str, Any]:
        started = time.time()

        try:
            supervisor_diag = self.supervisor.diagnostics() if self.supervisor else {}
            scheduler_diag = self.scheduler.diagnostics() if self.scheduler else {}
            cache_diag = self.market_cache.diagnostics() if self.market_cache else {}
            store_diag = self.historical_store.diagnostics() if self.historical_store else {}
            pipeline_diag = self.historical_pipeline.diagnostics() if self.historical_pipeline else {}
            watchdog_diag = self.watchdog.diagnostics() if self.watchdog else {}

            metrics = {
                "module": "ops_006_metrics_performance_engine",
                "status": "ok",
                "timestamp": time.time(),
                "sample_count": self.sample_count + 1,
                "runtime": {
                    "uptime_seconds": time.time() - self.started_at,
                },
                "supervisor": {
                    "service_count": supervisor_diag.get("service_count", 0),
                    "running_count": supervisor_diag.get("running_count", 0),
                    "error_count": supervisor_diag.get("error_count", 0),
                    "status": supervisor_diag.get("status"),
                },
                "scheduler": {
                    "running": scheduler_diag.get("scheduler_running", False),
                    "job_count": scheduler_diag.get("job_count", 0),
                    "running_jobs": scheduler_diag.get("running_jobs", 0),
                    "error_jobs": scheduler_diag.get("error_jobs", 0),
                    "status": scheduler_diag.get("status"),
                },
                "market_cache": {
                    "market_count": cache_diag.get("market_count", 0),
                    "refresh_count": cache_diag.get("refresh_count", 0),
                    "error_count": cache_diag.get("error_count", 0),
                    "last_refresh_duration_seconds": cache_diag.get("last_refresh_duration_seconds"),
                    "background_running": cache_diag.get("background_running", False),
                    "status": cache_diag.get("status"),
                },
                "history": {
                    "observation_count": store_diag.get("observation_count", 0),
                    "snapshot_count": store_diag.get("snapshot_count", 0),
                    "status": store_diag.get("status"),
                },
                "pipeline": {
                    "record_count": pipeline_diag.get("record_count", 0),
                    "market_rows_recorded": pipeline_diag.get("market_rows_recorded", 0),
                    "skipped_duplicates": pipeline_diag.get("skipped_duplicates", 0),
                    "error_count": pipeline_diag.get("error_count", 0),
                    "last_duration_seconds": pipeline_diag.get("last_duration_seconds"),
                    "status": pipeline_diag.get("status"),
                },
                "watchdog": {
                    "check_count": watchdog_diag.get("check_count", 0),
                    "recovery_count": watchdog_diag.get("recovery_count", 0),
                    "error_count": watchdog_diag.get("error_count", 0),
                    "status": watchdog_diag.get("status"),
                },
            }

            metrics["health_score"] = self._health_score(metrics)
            metrics["duration_seconds"] = round(time.time() - started, 4)

            self.sample_count += 1
            self.last_sample_at = metrics["timestamp"]
            self.last_metrics = metrics
            self.last_error = None

            self._emit("ops.metrics.collected", metrics)
            return metrics

        except Exception as exc:
            self.error_count += 1
            self.last_error = str(exc)

            result = {
                "module": "ops_006_metrics_performance_engine",
                "status": "error",
                "error": str(exc),
                "error_count": self.error_count,
                "timestamp": time.time(),
            }

            self.last_metrics = result
            self._emit("ops.metrics.error", result)
            return result

    def _health_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        score = 100
        issues = []

        if metrics["supervisor"]["error_count"] > 0:
            score -= 20
            issues.append("Supervisor has service errors.")

        if not metrics["scheduler"]["running"]:
            score -= 25
            issues.append("Scheduler is not running.")

        if metrics["scheduler"]["error_jobs"] > 0:
            score -= 15
            issues.append("Scheduler has errored jobs.")

        if metrics["market_cache"]["error_count"] > 0:
            score -= 15
            issues.append("Market cache has errors.")

        if metrics["pipeline"]["error_count"] > 0:
            score -= 15
            issues.append("Historical pipeline has errors.")

        if metrics["watchdog"]["error_count"] > 0:
            score -= 10
            issues.append("Watchdog has errors.")

        score = max(0, min(100, score))

        if score >= 90:
            label = "excellent"
        elif score >= 75:
            label = "good"
        elif score >= 50:
            label = "warning"
        else:
            label = "critical"

        return {
            "score": score,
            "label": label,
            "issues": issues,
        }

    def scorecard(self) -> Dict[str, Any]:
        metrics = self.last_metrics or self.collect()

        return {
            "module": "ops_006_metrics_scorecard",
            "status": metrics.get("status"),
            "health_score": metrics.get("health_score"),
            "markets_cached": metrics.get("market_cache", {}).get("market_count"),
            "cache_refreshes": metrics.get("market_cache", {}).get("refresh_count"),
            "history_rows": metrics.get("history", {}).get("observation_count"),
            "history_snapshots": metrics.get("history", {}).get("snapshot_count"),
            "pipeline_records": metrics.get("pipeline", {}).get("record_count"),
            "watchdog_checks": metrics.get("watchdog", {}).get("check_count"),
            "watchdog_recoveries": metrics.get("watchdog", {}).get("recovery_count"),
            "scheduler_jobs": metrics.get("scheduler", {}).get("job_count"),
            "services": metrics.get("supervisor", {}).get("service_count"),
            "timestamp": metrics.get("timestamp"),
        }

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "ops_006_metrics_performance_engine",
            "status": "ok" if self.error_count == 0 else "warning",
            "started_at": self.started_at,
            "sample_count": self.sample_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_sample_at": self.last_sample_at,
            "last_metrics": self.last_metrics,
            "read_only_trading": True,
        }


def build_metrics_engine(
    supervisor: Any = None,
    scheduler: Any = None,
    market_cache: Any = None,
    historical_store: Any = None,
    historical_pipeline: Any = None,
    watchdog: Any = None,
    event_bus: Any = None,
) -> QSeriesMetricsEngine:
    return QSeriesMetricsEngine(
        supervisor=supervisor,
        scheduler=scheduler,
        market_cache=market_cache,
        historical_store=historical_store,
        historical_pipeline=historical_pipeline,
        watchdog=watchdog,
        event_bus=event_bus,
    )


if __name__ == "__main__":
    engine = build_metrics_engine()
    print(engine.collect())
