"""
OI-066 Portfolio-Level Intelligence Manager

Purpose:
- Analyze all active Oracle research sessions as one portfolio.
- Identify concentration, consensus alignment, risk clusters, drift clusters, and top research priorities.
- Keep Oracle read-only while giving Q Series a better intelligence overview.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PortfolioLevelIntelligenceManager:
    module_name = "oi_066_portfolio_level_intelligence_manager"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "portfolio_level_research_intelligence",
        }

    def analyze_portfolio(self, portfolio_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        sessions = portfolio_snapshot.get("sessions", []) or []

        consensus = self._consensus_summary(sessions)
        risk = self._risk_summary(sessions)
        drift = self._drift_summary(sessions)
        clusters = self._clusters(sessions)
        priorities = self._top_priorities(sessions)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "active_count": len(sessions),
            "consensus_summary": consensus,
            "risk_summary": risk,
            "drift_summary": drift,
            "clusters": clusters,
            "top_research_priorities": priorities,
            "portfolio_state": self._portfolio_state(consensus, risk, drift, sessions),
        }

    def _consensus_summary(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        yes = 0
        no = 0
        unknown = 0
        scores = []
        confidences = []

        for session in sessions:
            snap = session.get("current_snapshot", {}) or {}
            side = str(snap.get("consensus_side") or "UNKNOWN").upper()

            if side == "YES":
                yes += 1
            elif side == "NO":
                no += 1
            else:
                unknown += 1

            if self._num(snap.get("consensus_score_pct")) is not None:
                scores.append(self._num(snap.get("consensus_score_pct")))

            if self._num(snap.get("adjusted_confidence")) is not None:
                confidences.append(self._num(snap.get("adjusted_confidence")))

        total = len(sessions)

        return {
            "total": total,
            "yes_count": yes,
            "no_count": no,
            "unknown_count": unknown,
            "yes_share": round(yes / total, 4) if total else None,
            "no_share": round(no / total, 4) if total else None,
            "avg_consensus_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_adjusted_confidence": round(sum(confidences) / len(confidences), 2) if confidences else None,
            "dominant_side": "YES" if yes > no else "NO" if no > yes else "BALANCED",
        }

    def _risk_summary(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_counts = {}
        tail_counts = {}
        stability_counts = {}

        for session in sessions:
            snap = session.get("current_snapshot", {}) or {}

            risk = str(snap.get("risk_level") or "unknown").lower()
            tail = str(snap.get("tail_risk_level") or "unknown").lower()
            stability = str(snap.get("research_stability") or "unknown").lower()

            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            tail_counts[tail] = tail_counts.get(tail, 0) + 1
            stability_counts[stability] = stability_counts.get(stability, 0) + 1

        high_risk = risk_counts.get("high", 0) + tail_counts.get("high", 0)
        unstable = stability_counts.get("low", 0)

        return {
            "risk_counts": risk_counts,
            "tail_risk_counts": tail_counts,
            "stability_counts": stability_counts,
            "high_risk_signals": high_risk,
            "unstable_research_count": unstable,
        }

    def _drift_summary(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        counts = {
            "none": 0,
            "minor": 0,
            "moderate": 0,
            "major": 0,
            "side_changed": 0,
            "grade_changed": 0,
            "stability_changed": 0,
        }

        total_consensus_drift = 0.0
        total_confidence_drift = 0.0

        for session in sessions:
            drift = session.get("drift", {}) or {}
            level = str(drift.get("drift_level") or "none").lower()
            if level not in {"none", "minor", "moderate", "major"}:
                level = "none"

            counts[level] += 1

            if drift.get("consensus_side_changed"):
                counts["side_changed"] += 1
            if drift.get("grade_changed"):
                counts["grade_changed"] += 1
            if drift.get("stability_changed"):
                counts["stability_changed"] += 1

            total_consensus_drift += abs(self._num(drift.get("consensus_score_drift"), 0.0))
            total_confidence_drift += abs(self._num(drift.get("confidence_drift"), 0.0))

        total = len(sessions)

        return {
            "counts": counts,
            "avg_abs_consensus_drift": round(total_consensus_drift / total, 2) if total else 0.0,
            "avg_abs_confidence_drift": round(total_confidence_drift / total, 2) if total else 0.0,
        }

    def _clusters(self, sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_grade = {}
        by_stability = {}
        by_priority = {}

        for session in sessions:
            snap = session.get("current_snapshot", {}) or {}
            opportunity = session.get("opportunity", {}) or {}

            grade = snap.get("final_research_grade") or "UNRATED"
            stability = snap.get("research_stability") or "unknown"
            priority = opportunity.get("priority") or "unknown"

            by_grade[grade] = by_grade.get(grade, 0) + 1
            by_stability[stability] = by_stability.get(stability, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "by_grade": by_grade,
            "by_stability": by_stability,
            "by_priority": by_priority,
        }

    def _top_priorities(self, sessions: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        rows = []

        for session in sessions:
            snap = session.get("current_snapshot", {}) or {}
            drift = session.get("drift", {}) or {}
            opportunity = session.get("opportunity", {}) or {}

            opportunity_score = self._num(opportunity.get("opportunity_score") or session.get("opportunity_score"), 0.0)
            consensus = self._num(snap.get("consensus_score_pct"), 0.0)
            confidence = self._num(snap.get("adjusted_confidence"), 0.0)
            drift_score = (
                abs(self._num(drift.get("consensus_score_drift"), 0.0))
                + abs(self._num(drift.get("confidence_drift"), 0.0))
            )

            priority_score = round((opportunity_score * 0.35) + (consensus * 0.25) + (confidence * 0.25) + (drift_score * 0.15), 2)

            rows.append({
                "ticker": session.get("ticker"),
                "priority_score": priority_score,
                "opportunity_score": opportunity_score,
                "consensus_side": snap.get("consensus_side"),
                "consensus_score_pct": consensus,
                "adjusted_confidence": confidence,
                "drift_level": drift.get("drift_level"),
                "status": session.get("status"),
            })

        rows.sort(key=lambda r: r["priority_score"], reverse=True)
        return rows[:limit]

    def _portfolio_state(
        self,
        consensus: Dict[str, Any],
        risk: Dict[str, Any],
        drift: Dict[str, Any],
        sessions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not sessions:
            return {
                "state": "empty",
                "headline": "No active Oracle research sessions.",
            }

        if drift["counts"].get("side_changed", 0) > 0 or risk.get("unstable_research_count", 0) > 0:
            return {
                "state": "unstable",
                "headline": "Portfolio contains meaningful research instability.",
            }

        if consensus.get("avg_consensus_score", 0) >= 85 and risk.get("high_risk_signals", 0) == 0:
            return {
                "state": "strong_alignment",
                "headline": "Portfolio research is strongly aligned with low high-risk signal count.",
            }

        if risk.get("high_risk_signals", 0) >= 2:
            return {
                "state": "risk_elevated",
                "headline": "Portfolio has elevated risk or tail-risk concentration.",
            }

        return {
            "state": "normal",
            "headline": "Portfolio research state is normal.",
        }

    def _num(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return default


portfolio_level_intelligence_manager = PortfolioLevelIntelligenceManager()
