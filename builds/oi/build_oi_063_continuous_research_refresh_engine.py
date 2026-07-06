from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "continuous_research_refresh_engine.py"
TEST = ROOT / "test_oi_063_continuous_research_refresh_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-063 Continuous Research Refresh Engine

Purpose:
- Continuously evaluate active Oracle research sessions.
- Decide which sessions are due for refresh.
- Trigger read-only research refresh through OI-062 lifecycle bridge.
- Track refresh results, drift, and refresh cadence.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .active_research_lifecycle_bridge import (
    active_research_lifecycle_bridge,
    ActiveResearchLifecycleBridge,
)


REFRESH_INTERVAL_SECONDS = {
    "critical": 10,
    "high": 30,
    "medium": 60,
    "watch": 300,
    "low": 600,
}


class ContinuousResearchRefreshEngine:
    module_name = "oi_063_continuous_research_refresh_engine"

    def __init__(self, lifecycle_bridge: Optional[ActiveResearchLifecycleBridge] = None) -> None:
        self.lifecycle_bridge = lifecycle_bridge or active_research_lifecycle_bridge
        self._refresh_history: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        portfolio = self.lifecycle_bridge.portfolio_snapshot()

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "active_sessions": portfolio.get("active_count", 0),
            "refresh_history": len(self._refresh_history),
            "intervals": REFRESH_INTERVAL_SECONDS,
        }

    def evaluate_refresh_due(
        self,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        portfolio = self.lifecycle_bridge.portfolio_snapshot()
        sessions = portfolio.get("sessions", [])

        due = []
        not_due = []

        for session in sessions:
            eval_item = self._evaluate_session(session, now)

            if eval_item["due"]:
                due.append(eval_item)
            else:
                not_due.append(eval_item)

        due.sort(
            key=lambda x: (
                x["priority_weight"],
                x["opportunity_score"],
                x["seconds_overdue"],
            ),
            reverse=True,
        )

        return {
            "status": "ok",
            "read_only": True,
            "evaluated": len(sessions),
            "due_count": len(due),
            "not_due_count": len(not_due),
            "due": due,
            "not_due": not_due,
        }

    def refresh_due_sessions(
        self,
        max_refreshes: int = 5,
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        evaluation = self.evaluate_refresh_due()
        due = evaluation.get("due", [])[:max_refreshes]

        refreshed = []
        errors = []

        for item in due:
            ticker = item["ticker"]

            try:
                result = self._refresh_session(item, report_format=report_format)
                refreshed.append(result)
            except Exception as exc:
                error = {
                    "status": "error",
                    "read_only": True,
                    "ticker": ticker,
                    "error": str(exc),
                    "at": self._now(),
                }
                errors.append(error)
                self._refresh_history.append(error)

        return {
            "status": "ok",
            "read_only": True,
            "requested": len(due),
            "refreshed_count": len(refreshed),
            "error_count": len(errors),
            "refreshed": refreshed,
            "errors": errors,
        }

    def force_refresh(
        self,
        ticker: str,
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        portfolio = self.lifecycle_bridge.portfolio_snapshot()
        sessions = portfolio.get("sessions", [])

        session = None
        for item in sessions:
            if item.get("ticker") == ticker:
                session = item
                break

        if not session:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        eval_item = self._evaluate_session(session, datetime.now(timezone.utc))
        eval_item["due"] = True
        eval_item["forced"] = True

        return self._refresh_session(eval_item, report_format=report_format)

    def refresh_history(self, limit: int = 25) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "count": len(self._refresh_history),
            "history": self._refresh_history[-limit:],
        }

    def _refresh_session(
        self,
        evaluation_item: Dict[str, Any],
        report_format: str = "terminal",
    ) -> Dict[str, Any]:
        session = evaluation_item["session"]
        ticker = evaluation_item["ticker"]

        synthetic_result = self._synthetic_refresh_result(session, evaluation_item)

        tracked = self.lifecycle_bridge.track_external_result(
            research_result=synthetic_result,
            opportunity=session.get("opportunity", {}),
        )

        result = {
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "refreshed_at": self._now(),
            "evaluation": evaluation_item,
            "tracked": tracked,
            "drift": tracked.get("session", {}).get("drift", {}),
            "report_format": report_format,
        }

        self._refresh_history.append(result)
        return result

    def _synthetic_refresh_result(
        self,
        session: Dict[str, Any],
        evaluation_item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        OI-063 refreshes lifecycle state. Later OI builds will plug this into live
        market re-synthesis. This deterministic refresh payload keeps the module
        testable and read-only while preserving the contract.
        """
        ticker = session.get("ticker")
        snapshot = dict(session.get("current_snapshot", {}) or {})
        refresh_count = int(session.get("refresh_count", 0)) + 1

        base_consensus = float(snapshot.get("consensus_score_pct") or 50.0)
        base_confidence = float(snapshot.get("adjusted_confidence") or 50.0)

        priority = str(session.get("opportunity", {}).get("priority") or "watch").lower()

        drift_step = {
            "critical": 1.5,
            "high": 1.0,
            "medium": 0.6,
            "watch": 0.3,
            "low": 0.1,
        }.get(priority, 0.3)

        new_consensus = max(0.0, min(100.0, base_consensus + drift_step))
        new_confidence = max(0.0, min(100.0, base_confidence + drift_step))

        side = snapshot.get("consensus_side") or "YES"
        stability = snapshot.get("research_stability") or "medium"

        return {
            "status": "ok",
            "read_only": True,
            "research_only_execution": True,
            "ticker": ticker,
            "refresh_count": refresh_count,
            "report": {
                "packet": {
                    "summary": {
                        "market_ticker": ticker,
                        "expected_resolution": side,
                        "expected_probability": snapshot.get("expected_probability") or 0.5,
                        "adjusted_confidence": new_confidence,
                        "risk_level": snapshot.get("risk_level") or "unknown",
                        "tail_risk_level": snapshot.get("tail_risk_level") or "unknown",
                        "analog_count": snapshot.get("analog_count"),
                    },
                    "signals": {
                        "final_research_grade": snapshot.get("final_research_grade"),
                        "adjusted_confidence": new_confidence,
                    },
                    "consensus": {
                        "consensus_side": side,
                        "consensus_score_pct": new_consensus,
                        "agreement_pct": snapshot.get("agreement_pct") or 80,
                        "research_stability": stability,
                        "research_certainty_index": snapshot.get("research_certainty_index") or new_consensus,
                    },
                }
            },
            "job": {
                "ticker": ticker,
                "opportunity": session.get("opportunity", {}),
            },
        }

    def _evaluate_session(self, session: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        ticker = session.get("ticker")
        opportunity = session.get("opportunity", {}) or {}

        priority = str(opportunity.get("priority") or self._priority_from_score(opportunity.get("opportunity_score"))).lower()
        interval = REFRESH_INTERVAL_SECONDS.get(priority, REFRESH_INTERVAL_SECONDS["watch"])

        last_updated = self._parse_time(session.get("last_updated") or session.get("first_seen"))
        age_seconds = max((now - last_updated).total_seconds(), 0.0) if last_updated else 0.0
        seconds_overdue = max(age_seconds - interval, 0.0)

        due = age_seconds >= interval and session.get("status") in {"ACTIVE", "REFRESHING", "RESEARCHING"}

        return {
            "ticker": ticker,
            "read_only": True,
            "due": due,
            "priority": priority,
            "priority_weight": self._priority_weight(priority),
            "refresh_interval_sec": interval,
            "age_since_update_sec": round(age_seconds, 2),
            "seconds_overdue": round(seconds_overdue, 2),
            "opportunity_score": float(opportunity.get("opportunity_score") or session.get("opportunity_score") or 0),
            "refresh_count": session.get("refresh_count", 0),
            "session_status": session.get("status"),
            "session": session,
        }

    def _priority_from_score(self, score: Any) -> str:
        try:
            s = float(score or 0)
        except Exception:
            s = 0.0

        if s >= 90:
            return "critical"
        if s >= 80:
            return "high"
        if s >= 70:
            return "medium"
        if s >= 55:
            return "watch"
        return "low"

    def _priority_weight(self, priority: str) -> int:
        return {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "watch": 2,
            "low": 1,
        }.get(priority, 0)

    def _parse_time(self, value: Any) -> Optional[datetime]:
        if not value:
            return None

        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


continuous_research_refresh_engine = ContinuousResearchRefreshEngine()
'''

test_code = r'''from datetime import datetime, timezone, timedelta

from qseries_v2.oracle_intelligence.oracle_active_research_manager import OracleActiveResearchManager
from qseries_v2.oracle_intelligence.active_research_lifecycle_bridge import ActiveResearchLifecycleBridge
from qseries_v2.oracle_intelligence.continuous_research_refresh_engine import ContinuousResearchRefreshEngine


class FakeExecutionBridge:
    def status(self):
        return {"status": "ok"}


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


def test_oi_063_continuous_research_refresh_engine():
    manager = OracleActiveResearchManager()
    lifecycle = ActiveResearchLifecycleBridge(FakeExecutionBridge(), manager)
    refresh = ContinuousResearchRefreshEngine(lifecycle)

    lifecycle.track_external_result(
        fake_result("REFRESH-TEST", consensus=88, confidence=84),
        opportunity={
            "ticker": "REFRESH-TEST",
            "opportunity_score": 91,
            "priority": "critical",
        },
    )

    session = manager.get_session("REFRESH-TEST")
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=20)).isoformat()
    manager._sessions["REFRESH-TEST"]["last_updated"] = old_time

    due = refresh.evaluate_refresh_due()
    assert due["status"] == "ok"
    assert due["due_count"] == 1
    assert due["due"][0]["ticker"] == "REFRESH-TEST"

    result = refresh.refresh_due_sessions(max_refreshes=1)
    assert result["status"] == "ok"
    assert result["refreshed_count"] == 1
    assert result["refreshed"][0]["ticker"] == "REFRESH-TEST"

    refreshed_session = manager.get_session("REFRESH-TEST")
    assert refreshed_session["refresh_count"] == 1
    assert refreshed_session["drift"]["consensus_score_drift"] > 0

    forced = refresh.force_refresh("REFRESH-TEST")
    assert forced["status"] == "ok"
    assert forced["ticker"] == "REFRESH-TEST"

    history = refresh.refresh_history()
    assert history["count"] == 2

    status = refresh.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-063 Continuous Research Refresh Engine")
    print({
        "refresh_history": status["refresh_history"],
        "active_sessions": status["active_sessions"],
        "latest_drift": manager.get_session("REFRESH-TEST")["drift"],
    })


if __name__ == "__main__":
    test_oi_063_continuous_research_refresh_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .continuous_research_refresh_engine import continuous_research_refresh_engine, ContinuousResearchRefreshEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-063 INSTALLER")
print(" Continuous Research Refresh Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-063 installed")
print()
print("Run:")
print("python test_oi_063_continuous_research_refresh_engine.py")