"""
OI-060 Oracle Research Execution Bridge

Purpose:
- Execute Oracle research workflow for scheduled opportunities.
- Pull scheduled jobs from OI-059.
- Generate read-only consensus research reports through OI-056.
- Mark jobs complete in the scheduler/queue.

Important:
- "Execution" here means research execution only.
- No trade execution.
- No order placement.
- No order mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from .oracle_research_scheduler import (
    oracle_research_scheduler,
    OracleResearchScheduler,
)
from .oracle_consensus_report_composer import (
    oracle_consensus_report_composer,
    OracleConsensusReportComposer,
)


class OracleResearchExecutionBridge:
    module_name = "oi_060_oracle_research_execution_bridge"

    def __init__(
        self,
        scheduler: Optional[OracleResearchScheduler] = None,
        report_composer: Optional[OracleConsensusReportComposer] = None,
    ) -> None:
        self.scheduler = scheduler or oracle_research_scheduler
        self.report_composer = report_composer or oracle_consensus_report_composer
        self._history: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "research_only_execution": True,
            "scheduler": self._safe_status(self.scheduler),
            "report_composer": self._safe_status(self.report_composer),
            "research_runs": len(self._history),
        }

    def run_next_research(
        self,
        min_score: float = 55.0,
        report_format: str = "terminal",
        max_active_jobs: int = 3,
        current_active_jobs: int = 0,
    ) -> Optional[Dict[str, Any]]:
        job = self.scheduler.schedule_next(
            min_score=min_score,
            max_active_jobs=max_active_jobs,
            current_active_jobs=current_active_jobs,
        )

        if not job:
            return None

        if job.get("status") == "deferred":
            return job

        return self.run_scheduled_job(job, report_format=report_format)

    def run_scheduled_job(
        self,
        job: Dict[str, Any],
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        ticker = job.get("ticker")
        opportunity = job.get("opportunity", {}) or {}
        market = opportunity.get("market", {}) or {}

        current_setup = dict(market)
        current_setup.setdefault("ticker", ticker)
        current_setup.setdefault("market_ticker", ticker)

        for key in [
            "opportunity_score",
            "priority",
            "suggested_analysis_depth",
            "reason_codes",
            "components",
        ]:
            if key in opportunity:
                current_setup[key] = opportunity[key]

        try:
            report = self.report_composer.compose_consensus_report(
                current_setup=current_setup,
                limit=self._limit_from_depth(job.get("research_depth")),
                format=report_format,
            )

            result = {
                "status": "ok",
                "read_only": True,
                "research_only_execution": True,
                "ticker": ticker,
                "completed_at": self._now(),
                "job": job,
                "report": report,
            }

            self._history.append(result)
            self.scheduler.complete_job(ticker, result)

            return result

        except Exception as exc:
            error_result = {
                "status": "error",
                "read_only": True,
                "research_only_execution": True,
                "ticker": ticker,
                "error": str(exc),
                "failed_at": self._now(),
                "job": job,
            }

            self._history.append(error_result)
            self.scheduler.skip_job(ticker, f"research_error: {exc}")

            return error_result

    def run_batch(
        self,
        min_score: float = 55.0,
        max_jobs: int = 3,
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        batch = self.scheduler.schedule_batch(
            min_score=min_score,
            max_jobs=max_jobs,
            max_active_jobs=max_jobs,
            current_active_jobs=0,
        )

        results = []

        for job in batch.get("scheduled", []):
            results.append(self.run_scheduled_job(job, report_format=report_format))

        return {
            "status": "ok",
            "read_only": True,
            "research_only_execution": True,
            "scheduled_count": batch.get("scheduled_count", 0),
            "completed_count": len([r for r in results if r.get("status") == "ok"]),
            "error_count": len([r for r in results if r.get("status") == "error"]),
            "results": results,
        }

    def history(self, limit: int = 25) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "research_runs": self._history[-limit:],
            "count": len(self._history),
        }

    def _limit_from_depth(self, depth: Any) -> int:
        depth = str(depth or "").lower()

        if depth == "full_oracle_consensus":
            return 50
        if depth == "standard_oracle_research":
            return 25
        if depth == "light_watch_report":
            return 10

        return 15

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_research_execution_bridge = OracleResearchExecutionBridge()
