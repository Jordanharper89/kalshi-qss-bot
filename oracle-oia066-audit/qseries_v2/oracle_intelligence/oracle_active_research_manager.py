"""
OI-061 Oracle Active Research Manager

Purpose:
- Maintain active Oracle research sessions.
- Track consensus, confidence, refreshes, drift, status, and research age.
- Convert one-time research reports into persistent active research sessions.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ACTIVE_STATES = {
    "DISCOVERED",
    "QUEUED",
    "RESEARCHING",
    "ACTIVE",
    "REFRESHING",
    "COMPLETED",
    "ARCHIVED",
}


class OracleActiveResearchManager:
    module_name = "oi_061_oracle_active_research_manager"

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._archive: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "active_sessions": len(self._sessions),
            "archived_sessions": len(self._archive),
            "states": sorted(ACTIVE_STATES),
        }

    def start_session(
        self,
        ticker: str,
        opportunity: Optional[Dict[str, Any]] = None,
        research_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = self._now()
        opportunity = opportunity or {}
        research_result = research_result or {}

        existing = self._sessions.get(ticker)

        if existing:
            return self.refresh_session(
                ticker=ticker,
                research_result=research_result,
                opportunity=opportunity,
            )

        snapshot = self._extract_research_snapshot(research_result)

        session = {
            "ticker": ticker,
            "status": "ACTIVE" if research_result else "DISCOVERED",
            "read_only": True,
            "first_seen": now,
            "last_updated": now,
            "refresh_count": 0,
            "opportunity": opportunity,
            "opportunity_score": opportunity.get("opportunity_score"),
            "current_research": research_result,
            "previous_research": None,
            "current_snapshot": snapshot,
            "previous_snapshot": None,
            "drift": self._empty_drift(),
            "history": [
                {
                    "event": "session_started",
                    "at": now,
                    "snapshot": snapshot,
                }
            ],
        }

        self._sessions[ticker] = session
        return dict(session)

    def refresh_session(
        self,
        ticker: str,
        research_result: Dict[str, Any],
        opportunity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if ticker not in self._sessions:
            return self.start_session(
                ticker=ticker,
                opportunity=opportunity or {},
                research_result=research_result,
            )

        now = self._now()
        session = self._sessions[ticker]

        previous_snapshot = session.get("current_snapshot")
        current_snapshot = self._extract_research_snapshot(research_result)
        drift = self._calculate_drift(previous_snapshot, current_snapshot)

        session["status"] = "ACTIVE"
        session["last_updated"] = now
        session["refresh_count"] = int(session.get("refresh_count", 0)) + 1
        session["previous_research"] = session.get("current_research")
        session["current_research"] = research_result
        session["previous_snapshot"] = previous_snapshot
        session["current_snapshot"] = current_snapshot
        session["drift"] = drift

        if opportunity:
            session["opportunity"] = opportunity
            session["opportunity_score"] = opportunity.get("opportunity_score", session.get("opportunity_score"))

        session.setdefault("history", []).append({
            "event": "session_refreshed",
            "at": now,
            "snapshot": current_snapshot,
            "drift": drift,
        })

        return dict(session)

    def mark_status(self, ticker: str, status: str) -> Dict[str, Any]:
        status = str(status).upper()

        if status not in ACTIVE_STATES:
            return {
                "status": "error",
                "read_only": True,
                "ticker": ticker,
                "error": f"invalid_status:{status}",
            }

        if ticker not in self._sessions:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        self._sessions[ticker]["status"] = status
        self._sessions[ticker]["last_updated"] = self._now()
        self._sessions[ticker].setdefault("history", []).append({
            "event": "status_changed",
            "at": self._now(),
            "status": status,
        })

        return dict(self._sessions[ticker])

    def complete_session(self, ticker: str, final_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if ticker not in self._sessions:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        if final_result:
            self.refresh_session(ticker, final_result)

        self._sessions[ticker]["status"] = "COMPLETED"
        self._sessions[ticker]["completed_at"] = self._now()
        self._sessions[ticker].setdefault("history", []).append({
            "event": "session_completed",
            "at": self._now(),
        })

        return dict(self._sessions[ticker])

    def archive_session(self, ticker: str) -> Dict[str, Any]:
        if ticker not in self._sessions:
            return {
                "status": "not_found",
                "read_only": True,
                "ticker": ticker,
            }

        session = self._sessions.pop(ticker)
        session["status"] = "ARCHIVED"
        session["archived_at"] = self._now()
        session.setdefault("history", []).append({
            "event": "session_archived",
            "at": self._now(),
        })

        self._archive[ticker] = session

        return {
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "active_sessions": len(self._sessions),
            "archived_sessions": len(self._archive),
            "session": session,
        }

    def get_session(self, ticker: str) -> Optional[Dict[str, Any]]:
        if ticker in self._sessions:
            return dict(self._sessions[ticker])

        if ticker in self._archive:
            return dict(self._archive[ticker])

        return None

    def active_sessions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = list(self._sessions.values())

        if status:
            rows = [r for r in rows if r.get("status") == str(status).upper()]

        rows.sort(
            key=lambda r: (
                float(r.get("opportunity_score") or 0),
                str(r.get("last_updated") or ""),
            ),
            reverse=True,
        )

        return [dict(r) for r in rows]

    def portfolio_snapshot(self) -> Dict[str, Any]:
        sessions = self.active_sessions()
        drift_counts = {
            "meaningful_consensus_drift": 0,
            "meaningful_confidence_drift": 0,
            "side_changed": 0,
        }

        for session in sessions:
            drift = session.get("drift", {})
            if abs(float(drift.get("consensus_score_drift", 0) or 0)) >= 5:
                drift_counts["meaningful_consensus_drift"] += 1
            if abs(float(drift.get("confidence_drift", 0) or 0)) >= 5:
                drift_counts["meaningful_confidence_drift"] += 1
            if drift.get("consensus_side_changed"):
                drift_counts["side_changed"] += 1

        return {
            "status": "ok",
            "read_only": True,
            "active_count": len(self._sessions),
            "archived_count": len(self._archive),
            "drift_counts": drift_counts,
            "sessions": sessions,
        }

    def _extract_research_snapshot(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        if not research_result:
            return {}

        report = research_result.get("report", {}) if isinstance(research_result.get("report"), dict) else {}
        packet = report.get("packet", {}) if isinstance(report.get("packet"), dict) else {}

        summary = (
            packet.get("summary")
            or research_result.get("summary")
            or report.get("summary")
            or {}
        )

        consensus = (
            packet.get("consensus")
            or research_result.get("consensus")
            or {}
        )

        signals = (
            packet.get("signals")
            or research_result.get("signals")
            or {}
        )

        return {
            "consensus_side": consensus.get("consensus_side") or summary.get("consensus_side") or summary.get("expected_resolution"),
            "consensus_score_pct": self._num(consensus.get("consensus_score_pct") or summary.get("consensus_score_pct")),
            "agreement_pct": self._num(consensus.get("agreement_pct") or summary.get("agreement_pct")),
            "research_stability": consensus.get("research_stability") or summary.get("research_stability"),
            "research_certainty_index": self._num(consensus.get("research_certainty_index") or summary.get("research_certainty_index")),
            "expected_probability": self._num(summary.get("expected_probability") or signals.get("expected_probability")),
            "adjusted_confidence": self._num(summary.get("adjusted_confidence") or signals.get("adjusted_confidence")),
            "final_research_grade": signals.get("final_research_grade") or signals.get("research_grade"),
            "risk_level": summary.get("risk_level") or signals.get("risk_level"),
            "tail_risk_level": summary.get("tail_risk_level") or signals.get("tail_risk_level"),
            "top_analog": summary.get("top_analog"),
            "analog_count": summary.get("analog_count"),
        }

    def _calculate_drift(
        self,
        previous: Optional[Dict[str, Any]],
        current: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not previous:
            return self._empty_drift()

        previous = previous or {}
        current = current or {}

        consensus_score_drift = self._delta(
            current.get("consensus_score_pct"),
            previous.get("consensus_score_pct"),
        )
        confidence_drift = self._delta(
            current.get("adjusted_confidence"),
            previous.get("adjusted_confidence"),
        )
        probability_drift = self._delta(
            current.get("expected_probability"),
            previous.get("expected_probability"),
        )
        certainty_drift = self._delta(
            current.get("research_certainty_index"),
            previous.get("research_certainty_index"),
        )

        return {
            "consensus_score_drift": consensus_score_drift,
            "confidence_drift": confidence_drift,
            "probability_drift": probability_drift,
            "certainty_drift": certainty_drift,
            "consensus_side_changed": bool(
                previous.get("consensus_side")
                and current.get("consensus_side")
                and previous.get("consensus_side") != current.get("consensus_side")
            ),
            "stability_changed": bool(
                previous.get("research_stability")
                and current.get("research_stability")
                and previous.get("research_stability") != current.get("research_stability")
            ),
            "grade_changed": bool(
                previous.get("final_research_grade")
                and current.get("final_research_grade")
                and previous.get("final_research_grade") != current.get("final_research_grade")
            ),
            "drift_level": self._drift_level(consensus_score_drift, confidence_drift, probability_drift),
        }

    def _empty_drift(self) -> Dict[str, Any]:
        return {
            "consensus_score_drift": 0.0,
            "confidence_drift": 0.0,
            "probability_drift": 0.0,
            "certainty_drift": 0.0,
            "consensus_side_changed": False,
            "stability_changed": False,
            "grade_changed": False,
            "drift_level": "none",
        }

    def _drift_level(self, *values: float) -> str:
        max_abs = max(abs(float(v or 0)) for v in values)

        if max_abs >= 15:
            return "major"
        if max_abs >= 7:
            return "moderate"
        if max_abs >= 3:
            return "minor"
        return "none"

    def _delta(self, current: Any, previous: Any) -> float:
        c = self._num(current)
        p = self._num(previous)

        if c is None or p is None:
            return 0.0

        return round(c - p, 4)

    def _num(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_active_research_manager = OracleActiveResearchManager()
