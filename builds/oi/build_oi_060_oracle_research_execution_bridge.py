from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_research_execution_bridge.py"
TEST = ROOT / "test_oi_060_oracle_research_execution_bridge.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
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
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_opportunity_queue_manager import OracleOpportunityQueueManager
from qseries_v2.oracle_intelligence.oracle_research_scheduler import OracleResearchScheduler
from qseries_v2.oracle_intelligence.oracle_research_execution_bridge import OracleResearchExecutionBridge


class FakeConsensusReportComposer:
    def status(self):
        return {"status": "ok"}

    def compose_consensus_report(self, current_setup, limit=25, format="terminal"):
        return {
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": current_setup.get("ticker"),
            "report": f"Consensus report for {current_setup.get('ticker')}",
            "sections": [
                {"title": "Oracle Consensus Summary", "lines": ["Consensus Side: YES"]}
            ],
        }


def test_oi_060_oracle_research_execution_bridge():
    queue = OracleOpportunityQueueManager()
    scheduler = OracleResearchScheduler(queue)
    composer = FakeConsensusReportComposer()
    bridge = OracleResearchExecutionBridge(scheduler, composer)

    queue.ingest_discovery_result({
        "top_opportunities": [
            {
                "ticker": "EXEC-TEST-1",
                "opportunity_score": 92.0,
                "priority": "critical",
                "priority_weight": 5,
                "suggested_analysis_depth": "full_oracle_consensus",
                "reason_codes": ["rapid_volume_acceleration"],
                "market": {
                    "ticker": "EXEC-TEST-1",
                    "price": 52,
                    "volume": 10000,
                    "liquidity": 30000,
                    "spread": 2,
                },
            },
            {
                "ticker": "EXEC-TEST-2",
                "opportunity_score": 72.0,
                "priority": "medium",
                "priority_weight": 3,
                "suggested_analysis_depth": "standard_oracle_research",
                "reason_codes": ["historical_analog_support"],
                "market": {
                    "ticker": "EXEC-TEST-2",
                    "price": 48,
                    "volume": 8000,
                    "liquidity": 20000,
                    "spread": 3,
                },
            },
        ]
    })

    one = bridge.run_next_research(min_score=80)
    assert one["status"] == "ok"
    assert one["read_only"] is True
    assert one["research_only_execution"] is True
    assert one["ticker"] == "EXEC-TEST-1"
    assert "Consensus report for EXEC-TEST-1" in one["report"]["report"]

    batch = bridge.run_batch(min_score=55, max_jobs=3)
    assert batch["status"] == "ok"
    assert batch["completed_count"] == 1
    assert batch["results"][0]["ticker"] == "EXEC-TEST-2"

    hist = bridge.history()
    assert hist["count"] == 2

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["research_runs"] == 2

    print("[PASS] OI-060 Oracle Research Execution Bridge")
    print({
        "research_runs": status["research_runs"],
        "history_count": hist["count"],
        "queue_status": scheduler.status(),
    })


if __name__ == "__main__":
    test_oi_060_oracle_research_execution_bridge()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_research_execution_bridge import oracle_research_execution_bridge, OracleResearchExecutionBridge\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-060 INSTALLER")
print(" Oracle Research Execution Bridge")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-060 installed")
print()
print("Run:")
print("python test_oi_060_oracle_research_execution_bridge.py")