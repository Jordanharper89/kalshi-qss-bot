from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "active_research_lifecycle_bridge.py"
TEST = ROOT / "test_oi_062_active_research_lifecycle_bridge.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-062 Active Research Lifecycle Bridge

Purpose:
- Connect OI-060 Research Execution Bridge to OI-061 Active Research Manager.
- Automatically start, refresh, complete, and archive active research sessions.
- Convert research runs into managed live research lifecycle events.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, List

from .oracle_research_execution_bridge import (
    oracle_research_execution_bridge,
    OracleResearchExecutionBridge,
)
from .oracle_active_research_manager import (
    oracle_active_research_manager,
    OracleActiveResearchManager,
)


class ActiveResearchLifecycleBridge:
    module_name = "oi_062_active_research_lifecycle_bridge"

    def __init__(
        self,
        execution_bridge: Optional[OracleResearchExecutionBridge] = None,
        active_manager: Optional[OracleActiveResearchManager] = None,
    ) -> None:
        self.execution_bridge = execution_bridge or oracle_research_execution_bridge
        self.active_manager = active_manager or oracle_active_research_manager

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "execution_bridge": self._safe_status(self.execution_bridge),
            "active_manager": self._safe_status(self.active_manager),
            "active_sessions": self.active_manager.status().get("active_sessions", 0),
        }

    def run_next_and_track(
        self,
        min_score: float = 55.0,
        report_format: str = "terminal",
    ) -> Optional[Dict[str, Any]]:
        result = self.execution_bridge.run_next_research(
            min_score=min_score,
            report_format=report_format,
        )

        if not result:
            return None

        if result.get("status") != "ok":
            return {
                "status": result.get("status"),
                "read_only": True,
                "research_result": result,
                "session": None,
            }

        session = self._track_result(result)

        return {
            "status": "ok",
            "read_only": True,
            "ticker": result.get("ticker"),
            "research_result": result,
            "session": session,
        }

    def run_batch_and_track(
        self,
        min_score: float = 55.0,
        max_jobs: int = 3,
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        batch = self.execution_bridge.run_batch(
            min_score=min_score,
            max_jobs=max_jobs,
            report_format=report_format,
        )

        tracked = []

        for result in batch.get("results", []):
            if result.get("status") == "ok":
                tracked.append(self._track_result(result))

        return {
            "status": "ok",
            "read_only": True,
            "research_only_execution": True,
            "completed_count": batch.get("completed_count", 0),
            "error_count": batch.get("error_count", 0),
            "tracked_sessions": len(tracked),
            "sessions": tracked,
            "batch": batch,
        }

    def track_external_result(
        self,
        research_result: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ticker = self._ticker_from_result(research_result, opportunity)

        if not ticker:
            return {
                "status": "error",
                "read_only": True,
                "error": "missing_ticker",
            }

        existing = self.active_manager.get_session(ticker)

        if existing and existing.get("status") != "ARCHIVED":
            session = self.active_manager.refresh_session(
                ticker=ticker,
                research_result=research_result,
                opportunity=opportunity,
            )
            action = "refreshed"
        else:
            session = self.active_manager.start_session(
                ticker=ticker,
                opportunity=opportunity,
                research_result=research_result,
            )
            action = "started"

        return {
            "status": "ok",
            "read_only": True,
            "action": action,
            "ticker": ticker,
            "session": session,
        }

    def complete_and_archive(
        self,
        ticker: str,
        final_result: Optional[Dict[str, Any]] = None,
        archive: bool = True,
    ) -> Dict[str, Any]:
        completed = self.active_manager.complete_session(ticker, final_result)

        archived = None
        if completed.get("status") == "COMPLETED" and archive:
            archived = self.active_manager.archive_session(ticker)

        return {
            "status": "ok" if completed.get("status") == "COMPLETED" else completed.get("status"),
            "read_only": True,
            "ticker": ticker,
            "completed": completed,
            "archived": archived,
        }

    def portfolio_snapshot(self) -> Dict[str, Any]:
        return self.active_manager.portfolio_snapshot()

    def _track_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        job = result.get("job", {}) or {}
        opportunity = job.get("opportunity", {}) or {}
        tracked = self.track_external_result(result, opportunity=opportunity)
        return tracked.get("session", tracked)

    def _ticker_from_result(
        self,
        research_result: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        opportunity = opportunity or {}

        return (
            research_result.get("ticker")
            or research_result.get("market_ticker")
            or opportunity.get("ticker")
            or opportunity.get("market_ticker")
            or opportunity.get("market", {}).get("ticker")
            or opportunity.get("market", {}).get("market_ticker")
        )

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


active_research_lifecycle_bridge = ActiveResearchLifecycleBridge()
'''

test_code = r'''from qseries_v2.oracle_intelligence.active_research_lifecycle_bridge import ActiveResearchLifecycleBridge
from qseries_v2.oracle_intelligence.oracle_active_research_manager import OracleActiveResearchManager


class FakeExecutionBridge:
    def __init__(self):
        self.calls = 0

    def status(self):
        return {"status": "ok"}

    def run_next_research(self, min_score=55.0, report_format="terminal"):
        self.calls += 1
        return fake_result("LIFE-TEST", consensus=88 + self.calls, confidence=84 + self.calls)

    def run_batch(self, min_score=55.0, max_jobs=3, report_format="terminal"):
        return {
            "status": "ok",
            "read_only": True,
            "completed_count": 2,
            "error_count": 0,
            "results": [
                fake_result("LIFE-BATCH-1", consensus=86, confidence=82),
                fake_result("LIFE-BATCH-2", consensus=90, confidence=87),
            ],
        }


def fake_result(ticker, consensus=88, confidence=84):
    return {
        "status": "ok",
        "read_only": True,
        "research_only_execution": True,
        "ticker": ticker,
        "job": {
            "ticker": ticker,
            "opportunity": {
                "ticker": ticker,
                "opportunity_score": 91,
                "priority": "critical",
            },
        },
        "report": {
            "packet": {
                "summary": {
                    "market_ticker": ticker,
                    "expected_resolution": "YES",
                    "expected_probability": 0.82,
                    "adjusted_confidence": confidence,
                    "risk_level": "low",
                    "tail_risk_level": "low",
                    "analog_count": 12,
                },
                "signals": {
                    "final_research_grade": "A",
                    "adjusted_confidence": confidence,
                },
                "consensus": {
                    "consensus_side": "YES",
                    "consensus_score_pct": consensus,
                    "agreement_pct": 92,
                    "research_stability": "high",
                    "research_certainty_index": 90,
                },
            }
        },
    }


def test_oi_062_active_research_lifecycle_bridge():
    execution = FakeExecutionBridge()
    manager = OracleActiveResearchManager()
    bridge = ActiveResearchLifecycleBridge(execution, manager)

    first = bridge.run_next_and_track(min_score=80)
    assert first["status"] == "ok"
    assert first["session"]["ticker"] == "LIFE-TEST"
    assert first["session"]["refresh_count"] == 0

    second = bridge.run_next_and_track(min_score=80)
    assert second["status"] == "ok"
    assert second["session"]["ticker"] == "LIFE-TEST"
    assert second["session"]["refresh_count"] == 1
    assert second["session"]["drift"]["consensus_score_drift"] == 1.0

    batch = bridge.run_batch_and_track(min_score=70, max_jobs=2)
    assert batch["status"] == "ok"
    assert batch["tracked_sessions"] == 2

    portfolio = bridge.portfolio_snapshot()
    assert portfolio["active_count"] == 3

    closed = bridge.complete_and_archive("LIFE-TEST")
    assert closed["status"] == "ok"
    assert closed["archived"]["status"] == "ok"

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-062 Active Research Lifecycle Bridge")
    print({
        "active_sessions": status["active_sessions"],
        "portfolio_active": bridge.portfolio_snapshot()["active_count"],
    })


if __name__ == "__main__":
    test_oi_062_active_research_lifecycle_bridge()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .active_research_lifecycle_bridge import active_research_lifecycle_bridge, ActiveResearchLifecycleBridge\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-062 INSTALLER")
print(" Active Research Lifecycle Bridge")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-062 installed")
print()
print("Run:")
print("python test_oi_062_active_research_lifecycle_bridge.py")