from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_research_scheduler.py"
TEST = ROOT / "test_oi_059_oracle_research_scheduler.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-059 Oracle Research Scheduler

Purpose:
- Schedule queued Oracle opportunities for research.
- Decide what runs now, waits, watches, or gets skipped.
- Bridge OI-058 Opportunity Queue to Oracle research/reporting layers.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .oracle_opportunity_queue_manager import (
    oracle_opportunity_queue_manager,
    OracleOpportunityQueueManager,
)


class OracleResearchScheduler:
    module_name = "oi_059_oracle_research_scheduler"

    def __init__(self, queue_manager: Optional[OracleOpportunityQueueManager] = None) -> None:
        self.queue_manager = queue_manager or oracle_opportunity_queue_manager
        self._scheduled_jobs: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        queue_status = self.queue_manager.status()
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "queued": queue_status.get("queued", 0),
            "processed": queue_status.get("processed", 0),
            "scheduled_jobs": len(self._scheduled_jobs),
        }

    def schedule_next(
        self,
        min_score: float = 55.0,
        max_active_jobs: int = 3,
        current_active_jobs: int = 0,
    ) -> Optional[Dict[str, Any]]:
        if current_active_jobs >= max_active_jobs:
            return {
                "status": "deferred",
                "read_only": True,
                "reason": "max_active_jobs_reached",
                "current_active_jobs": current_active_jobs,
                "max_active_jobs": max_active_jobs,
            }

        item = self.queue_manager.next_opportunity(
            min_score=min_score,
            allowed_priorities=None,
            mark_reserved=True,
        )

        if not item:
            return None

        scheduled = self._build_schedule_item(item)
        self._scheduled_jobs[scheduled["ticker"]] = scheduled

        return scheduled

    def schedule_batch(
        self,
        min_score: float = 55.0,
        max_jobs: int = 5,
        max_active_jobs: int = 5,
        current_active_jobs: int = 0,
    ) -> Dict[str, Any]:
        scheduled = []
        available_slots = max(0, min(max_jobs, max_active_jobs - current_active_jobs))

        for _ in range(available_slots):
            job = self.schedule_next(
                min_score=min_score,
                max_active_jobs=max_active_jobs,
                current_active_jobs=current_active_jobs + len(scheduled),
            )

            if not job or job.get("status") == "deferred":
                break

            scheduled.append(job)

        return {
            "status": "ok",
            "read_only": True,
            "scheduled_count": len(scheduled),
            "scheduled": scheduled,
            "active_after_schedule": current_active_jobs + len(scheduled),
        }

    def evaluate_queue(
        self,
        limit: int = 25,
        min_score: float = 0.0,
    ) -> Dict[str, Any]:
        items = self.queue_manager.peek(limit=limit, min_score=min_score)

        evaluations = []

        for item in items:
            evaluations.append(self._evaluate_item(item))

        return {
            "status": "ok",
            "read_only": True,
            "evaluated": len(evaluations),
            "items": evaluations,
        }

    def complete_job(
        self,
        ticker: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        job = self._scheduled_jobs.pop(ticker, None)

        processed = self.queue_manager.mark_processed(
            ticker=ticker,
            result={
                "scheduler_status": "completed",
                "job": job or {},
                "result": result or {},
            },
        )

        return {
            "status": processed.get("status"),
            "read_only": True,
            "ticker": ticker,
            "scheduled_removed": job is not None,
            "queue_result": processed,
        }

    def skip_job(
        self,
        ticker: str,
        reason: str = "scheduler_skip",
    ) -> Dict[str, Any]:
        self._scheduled_jobs.pop(ticker, None)
        skipped = self.queue_manager.mark_skipped(ticker, reason)

        return {
            "status": skipped.get("status"),
            "read_only": True,
            "ticker": ticker,
            "reason": reason,
            "queue_result": skipped,
        }

    def scheduled_jobs(self) -> List[Dict[str, Any]]:
        jobs = list(self._scheduled_jobs.values())
        jobs.sort(key=lambda x: (x.get("priority_weight", 0), x.get("opportunity_score", 0)), reverse=True)
        return jobs

    def _build_schedule_item(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        evaluation = self._evaluate_item(opportunity)

        return {
            "status": "scheduled",
            "read_only": True,
            "ticker": opportunity.get("ticker"),
            "scheduled_at": self._now(),
            "run_mode": evaluation["run_mode"],
            "research_priority": evaluation["research_priority"],
            "research_depth": evaluation["research_depth"],
            "estimated_runtime_sec": evaluation["estimated_runtime_sec"],
            "reason": evaluation["reason"],
            "queue_rank": opportunity.get("queue_rank"),
            "opportunity_score": opportunity.get("opportunity_score"),
            "priority": opportunity.get("priority"),
            "priority_weight": opportunity.get("priority_weight"),
            "opportunity": opportunity,
        }

    def _evaluate_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        score = float(item.get("opportunity_score", 0.0))
        priority = str(item.get("priority") or "low").lower()
        reasons = item.get("reason_codes", []) or []
        depth = item.get("suggested_analysis_depth") or self._depth_from_score(score)

        if score >= 90 or priority == "critical":
            run_mode = "immediate"
            research_priority = "CRITICAL"
            estimated = 5.0
        elif score >= 80 or priority == "high":
            run_mode = "near_immediate"
            research_priority = "HIGH"
            estimated = 4.0
        elif score >= 70 or priority == "medium":
            run_mode = "scheduled"
            research_priority = "MEDIUM"
            estimated = 3.0
        elif score >= 55 or priority == "watch":
            run_mode = "watch"
            research_priority = "WATCH"
            estimated = 1.5
            depth = "light_watch_report"
        else:
            run_mode = "ignore"
            research_priority = "IGNORE"
            estimated = 0.0
            depth = "no_deep_analysis"

        return {
            "ticker": item.get("ticker"),
            "read_only": True,
            "research_priority": research_priority,
            "run_mode": run_mode,
            "research_depth": depth,
            "estimated_runtime_sec": estimated,
            "opportunity_score": score,
            "priority": priority,
            "queue_rank": item.get("queue_rank"),
            "reason": self._reason_text(score, priority, reasons, depth),
            "reason_codes": reasons,
        }

    def _depth_from_score(self, score: float) -> str:
        if score >= 85:
            return "full_oracle_consensus"
        if score >= 70:
            return "standard_oracle_research"
        if score >= 55:
            return "light_watch_report"
        return "no_deep_analysis"

    def _reason_text(
        self,
        score: float,
        priority: str,
        reasons: List[str],
        depth: str,
    ) -> str:
        parts = [
            f"Opportunity score {round(score, 2)}",
            f"priority {priority}",
            f"research depth {depth}",
        ]

        if reasons:
            parts.append("signals: " + ", ".join(reasons[:5]))

        return "; ".join(parts)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_research_scheduler = OracleResearchScheduler()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_opportunity_queue_manager import OracleOpportunityQueueManager
from qseries_v2.oracle_intelligence.oracle_research_scheduler import OracleResearchScheduler


def test_oi_059_oracle_research_scheduler():
    queue = OracleOpportunityQueueManager()
    scheduler = OracleResearchScheduler(queue)

    discovery = {
        "top_opportunities": [
            {
                "ticker": "SCH-CRITICAL",
                "opportunity_score": 94.0,
                "priority": "critical",
                "priority_weight": 5,
                "suggested_analysis_depth": "full_oracle_consensus",
                "reason_codes": ["rapid_volume_acceleration", "cross_market_divergence_detected"],
            },
            {
                "ticker": "SCH-WATCH",
                "opportunity_score": 58.0,
                "priority": "watch",
                "priority_weight": 2,
                "suggested_analysis_depth": "light_watch_report",
                "reason_codes": ["low_signal_watch_only"],
            },
        ]
    }

    ingest = queue.ingest_discovery_result(discovery)
    assert ingest["added"] == 2

    evaluation = scheduler.evaluate_queue()
    assert evaluation["status"] == "ok"
    assert evaluation["evaluated"] == 2
    assert evaluation["items"][0]["ticker"] == "SCH-CRITICAL"
    assert evaluation["items"][0]["research_priority"] == "CRITICAL"

    job = scheduler.schedule_next(min_score=55)
    assert job["status"] == "scheduled"
    assert job["ticker"] == "SCH-CRITICAL"
    assert job["research_depth"] == "full_oracle_consensus"

    batch = scheduler.schedule_batch(min_score=55, max_jobs=2)
    assert batch["status"] == "ok"
    assert batch["scheduled_count"] == 1
    assert batch["scheduled"][0]["ticker"] == "SCH-WATCH"

    jobs = scheduler.scheduled_jobs()
    assert len(jobs) == 2

    completed = scheduler.complete_job("SCH-CRITICAL", {"report": "done"})
    assert completed["status"] == "ok"

    skipped = scheduler.skip_job("SCH-WATCH", "watch_only")
    assert skipped["status"] == "ok"

    status = scheduler.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["scheduled_jobs"] == 0

    print("[PASS] OI-059 Oracle Research Scheduler")
    print(status)


if __name__ == "__main__":
    test_oi_059_oracle_research_scheduler()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_research_scheduler import oracle_research_scheduler, OracleResearchScheduler\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-059 INSTALLER")
print(" Oracle Research Scheduler")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-059 installed")
print()
print("Run:")
print("python test_oi_059_oracle_research_scheduler.py")