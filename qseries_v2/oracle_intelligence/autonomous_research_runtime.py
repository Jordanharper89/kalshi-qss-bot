"""
OI-067 Autonomous Research Runtime

Purpose:
- Coordinate Oracle's autonomous read-only research loop.
- Run discovery, queueing, scheduling, research execution, refresh, drift detection,
  notifications, and portfolio intelligence as one runtime service.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import time

from .oracle_opportunity_discovery_engine import oracle_opportunity_discovery_engine
from .oracle_opportunity_queue_manager import oracle_opportunity_queue_manager
from .oracle_research_scheduler import oracle_research_scheduler
from .active_research_lifecycle_bridge import active_research_lifecycle_bridge
from .continuous_research_refresh_engine import continuous_research_refresh_engine
from .research_drift_detection_engine import research_drift_detection_engine
from .oracle_intelligence_notification_engine import oracle_intelligence_notification_engine
from .portfolio_level_intelligence_manager import portfolio_level_intelligence_manager


class AutonomousResearchRuntime:
    module_name = "oi_067_autonomous_research_runtime"

    def __init__(
        self,
        discovery_engine=None,
        queue_manager=None,
        scheduler=None,
        lifecycle_bridge=None,
        refresh_engine=None,
        drift_engine=None,
        notification_engine=None,
        portfolio_manager=None,
    ) -> None:
        self.discovery_engine = discovery_engine or oracle_opportunity_discovery_engine
        self.queue_manager = queue_manager or oracle_opportunity_queue_manager
        self.scheduler = scheduler or oracle_research_scheduler
        self.lifecycle_bridge = lifecycle_bridge or active_research_lifecycle_bridge
        self.refresh_engine = refresh_engine or continuous_research_refresh_engine
        self.drift_engine = drift_engine or research_drift_detection_engine
        self.notification_engine = notification_engine or oracle_intelligence_notification_engine
        self.portfolio_manager = portfolio_manager or portfolio_level_intelligence_manager

        self._running = False
        self._started_at = None
        self._last_cycle_at = None
        self._cycles = 0
        self._metrics = {
            "markets_scanned": 0,
            "opportunities_found": 0,
            "queued_added": 0,
            "research_runs": 0,
            "refreshes": 0,
            "drift_checks": 0,
            "notifications": 0,
            "portfolio_updates": 0,
            "errors": 0,
        }
        self._last_outputs = {}

    def start(self) -> Dict[str, Any]:
        if not self._running:
            self._running = True
            self._started_at = self._now()

        return self.status()

    def stop(self) -> Dict[str, Any]:
        self._running = False
        return self.status()

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "running" if self._running else "stopped",
            "read_only": True,
            "uptime_seconds": self._uptime_seconds(),
            "cycles": self._cycles,
            "last_cycle_at": self._last_cycle_at,
            "metrics": dict(self._metrics),
            "queue": self._safe_call(self.queue_manager.status),
            "scheduler": self._safe_call(self.scheduler.status),
            "refresh": self._safe_call(self.refresh_engine.status),
            "health": self._health(),
        }

    def run_cycle(
        self,
        markets: Optional[List[Dict[str, Any]]] = None,
        max_research_jobs: int = 3,
        max_refreshes: int = 3,
        min_opportunity_score: float = 55.0,
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        self._cycles += 1
        self._last_cycle_at = self._now()

        outputs = {
            "cycle": self._cycles,
            "started_at": self._last_cycle_at,
            "read_only": True,
        }

        try:
            discovery = self._run_discovery(markets or [], min_opportunity_score)
            outputs["discovery"] = discovery

            queue = self._run_queue(discovery)
            outputs["queue"] = queue

            research = self._run_research(max_research_jobs, min_opportunity_score, report_format)
            outputs["research"] = research

            refresh = self._run_refresh(max_refreshes, report_format)
            outputs["refresh"] = refresh

            drift = self._run_drift_detection()
            outputs["drift"] = drift

            notifications = self._run_notifications(drift)
            outputs["notifications"] = notifications

            portfolio = self._run_portfolio()
            outputs["portfolio"] = portfolio

            outputs["status"] = "ok"

        except Exception as exc:
            self._metrics["errors"] += 1
            outputs["status"] = "error"
            outputs["error"] = str(exc)

        outputs["completed_at"] = self._now()
        self._last_outputs = outputs
        return outputs

    def run_once(
        self,
        markets: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if not self._running:
            self.start()

        return self.run_cycle(markets=markets, **kwargs)

    def last_outputs(self) -> Dict[str, Any]:
        return dict(self._last_outputs)

    def _run_discovery(self, markets: List[Dict[str, Any]], min_score: float) -> Dict[str, Any]:
        result = self.discovery_engine.discover(
            markets=markets,
            min_score=min_score,
            limit=100,
        )

        self._metrics["markets_scanned"] += result.get("markets_scanned", 0)
        self._metrics["opportunities_found"] += result.get("opportunities_found", 0)

        return result

    def _run_queue(self, discovery: Dict[str, Any]) -> Dict[str, Any]:
        result = self.queue_manager.ingest_discovery_result(discovery)
        self._metrics["queued_added"] += result.get("added", 0)
        return result

    def _run_research(
        self,
        max_jobs: int,
        min_score: float,
        report_format: str,
    ) -> Dict[str, Any]:
        result = self.lifecycle_bridge.run_batch_and_track(
            min_score=min_score,
            max_jobs=max_jobs,
            report_format=report_format,
        )

        self._metrics["research_runs"] += result.get("tracked_sessions", 0)
        return result

    def _run_refresh(self, max_refreshes: int, report_format: str) -> Dict[str, Any]:
        result = self.refresh_engine.refresh_due_sessions(
            max_refreshes=max_refreshes,
            report_format=report_format,
        )

        self._metrics["refreshes"] += result.get("refreshed_count", 0)
        return result

    def _run_drift_detection(self) -> Dict[str, Any]:
        portfolio = self.lifecycle_bridge.portfolio_snapshot()
        result = self.drift_engine.detect_portfolio_drift(portfolio)

        self._metrics["drift_checks"] += result.get("sessions_analyzed", 0)
        return result

    def _run_notifications(self, drift_result: Dict[str, Any]) -> Dict[str, Any]:
        result = self.notification_engine.build_portfolio_notifications(
            drift_result,
            channel="telegram",
            force=False,
        )

        self._metrics["notifications"] += result.get("notification_count", 0)
        return result

    def _run_portfolio(self) -> Dict[str, Any]:
        portfolio = self.lifecycle_bridge.portfolio_snapshot()
        result = self.portfolio_manager.analyze_portfolio(portfolio)

        self._metrics["portfolio_updates"] += 1
        return result

    def _health(self) -> str:
        if self._metrics.get("errors", 0) >= 3:
            return "degraded"
        return "healthy"

    def _safe_call(self, fn):
        try:
            return fn()
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def _uptime_seconds(self) -> float:
        if not self._started_at:
            return 0.0

        try:
            started = datetime.fromisoformat(self._started_at.replace("Z", "+00:00"))
            return round((datetime.now(timezone.utc) - started).total_seconds(), 2)
        except Exception:
            return 0.0

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


autonomous_research_runtime = AutonomousResearchRuntime()
