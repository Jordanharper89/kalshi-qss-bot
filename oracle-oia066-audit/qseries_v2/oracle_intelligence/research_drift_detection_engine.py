"""
OI-064 Research Drift Detection Engine

Purpose:
- Analyze Oracle active research drift.
- Classify consensus, confidence, probability, certainty, side, grade, and stability changes.
- Produce drift severity, reason codes, and notification priority.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ResearchDriftDetectionEngine:
    module_name = "oi_064_research_drift_detection_engine"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "research_drift_classification",
        }

    def detect_session_drift(self, session: Dict[str, Any]) -> Dict[str, Any]:
        ticker = session.get("ticker")
        drift = session.get("drift", {}) or {}
        current = session.get("current_snapshot", {}) or {}
        previous = session.get("previous_snapshot", {}) or {}

        signals = self._signals(drift, current, previous)
        severity = self._severity(signals)
        priority = self._notification_priority(severity, signals)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "drift_severity": severity,
            "notification_priority": priority,
            "reason_codes": signals,
            "summary": self._summary(ticker, severity, signals, drift, current, previous),
            "drift": drift,
            "current_snapshot": current,
            "previous_snapshot": previous,
        }

    def detect_portfolio_drift(self, portfolio_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        sessions = portfolio_snapshot.get("sessions", []) or []
        results = [self.detect_session_drift(s) for s in sessions]

        results.sort(
            key=lambda r: (
                self._severity_weight(r["drift_severity"]),
                self._priority_weight(r["notification_priority"]),
            ),
            reverse=True,
        )

        counts = {}
        for result in results:
            sev = result["drift_severity"]
            counts[sev] = counts.get(sev, 0) + 1

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "sessions_analyzed": len(results),
            "severity_counts": counts,
            "top_drifts": results,
        }

    def _signals(
        self,
        drift: Dict[str, Any],
        current: Dict[str, Any],
        previous: Dict[str, Any],
    ) -> List[str]:
        reasons = []

        consensus_drift = abs(self._num(drift.get("consensus_score_drift"), 0.0))
        confidence_drift = abs(self._num(drift.get("confidence_drift"), 0.0))
        probability_drift = abs(self._num(drift.get("probability_drift"), 0.0))
        certainty_drift = abs(self._num(drift.get("certainty_drift"), 0.0))

        if drift.get("consensus_side_changed"):
            reasons.append("consensus_side_flip")

        if drift.get("grade_changed"):
            reasons.append("research_grade_changed")

        if drift.get("stability_changed"):
            reasons.append("research_stability_changed")

        if consensus_drift >= 15:
            reasons.append("major_consensus_score_drift")
        elif consensus_drift >= 7:
            reasons.append("moderate_consensus_score_drift")
        elif consensus_drift >= 3:
            reasons.append("minor_consensus_score_drift")

        if confidence_drift >= 15:
            reasons.append("major_confidence_drift")
        elif confidence_drift >= 7:
            reasons.append("moderate_confidence_drift")
        elif confidence_drift >= 3:
            reasons.append("minor_confidence_drift")

        if probability_drift >= 0.15:
            reasons.append("major_probability_drift")
        elif probability_drift >= 0.07:
            reasons.append("moderate_probability_drift")
        elif probability_drift >= 0.03:
            reasons.append("minor_probability_drift")

        if certainty_drift >= 15:
            reasons.append("major_certainty_drift")
        elif certainty_drift >= 7:
            reasons.append("moderate_certainty_drift")
        elif certainty_drift >= 3:
            reasons.append("minor_certainty_drift")

        current_stability = str(current.get("research_stability") or "").lower()
        previous_stability = str(previous.get("research_stability") or "").lower()

        if previous_stability == "high" and current_stability == "low":
            reasons.append("stability_collapse")

        current_grade = current.get("final_research_grade")
        previous_grade = previous.get("final_research_grade")

        if previous_grade and current_grade:
            grade_move = self._grade_delta(previous_grade, current_grade)
            if grade_move <= -2:
                reasons.append("major_grade_downgrade")
            elif grade_move < 0:
                reasons.append("grade_downgrade")
            elif grade_move >= 2:
                reasons.append("major_grade_upgrade")
            elif grade_move > 0:
                reasons.append("grade_upgrade")

        if not reasons:
            reasons.append("no_material_drift")

        return reasons

    def _severity(self, reasons: List[str]) -> str:
        if "consensus_side_flip" in reasons:
            return "critical"

        critical_reasons = {
            "stability_collapse",
            "major_grade_downgrade",
        }

        if any(r in critical_reasons for r in reasons):
            return "critical"

        if any(r.startswith("major_") for r in reasons):
            return "major"

        if any(r.startswith("moderate_") for r in reasons) or "research_grade_changed" in reasons:
            return "moderate"

        if any(r.startswith("minor_") for r in reasons) or "grade_upgrade" in reasons or "grade_downgrade" in reasons:
            return "minor"

        return "none"

    def _notification_priority(self, severity: str, reasons: List[str]) -> str:
        if severity == "critical":
            return "immediate"

        if severity == "major":
            return "high"

        if severity == "moderate":
            return "normal"

        if severity == "minor":
            return "low"

        return "silent"

    def _summary(
        self,
        ticker: str,
        severity: str,
        reasons: List[str],
        drift: Dict[str, Any],
        current: Dict[str, Any],
        previous: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "ticker": ticker,
            "severity": severity,
            "headline": self._headline(ticker, severity, reasons),
            "consensus_side": current.get("consensus_side"),
            "previous_consensus_side": previous.get("consensus_side"),
            "consensus_score_drift": drift.get("consensus_score_drift", 0.0),
            "confidence_drift": drift.get("confidence_drift", 0.0),
            "probability_drift": drift.get("probability_drift", 0.0),
            "certainty_drift": drift.get("certainty_drift", 0.0),
            "current_grade": current.get("final_research_grade"),
            "previous_grade": previous.get("final_research_grade"),
            "current_stability": current.get("research_stability"),
            "previous_stability": previous.get("research_stability"),
        }

    def _headline(self, ticker: str, severity: str, reasons: List[str]) -> str:
        if severity == "critical":
            return f"{ticker}: CRITICAL research drift detected"

        if severity == "major":
            return f"{ticker}: Major Oracle research drift detected"

        if severity == "moderate":
            return f"{ticker}: Moderate research drift detected"

        if severity == "minor":
            return f"{ticker}: Minor research drift detected"

        return f"{ticker}: No material research drift"

    def _grade_delta(self, previous: str, current: str) -> int:
        order = ["WATCH", "B", "B+", "A-", "A", "A+"]
        p = str(previous).upper()
        c = str(current).upper()

        if p not in order or c not in order:
            return 0

        return order.index(c) - order.index(p)

    def _severity_weight(self, severity: str) -> int:
        return {
            "critical": 5,
            "major": 4,
            "moderate": 3,
            "minor": 2,
            "none": 1,
        }.get(severity, 0)

    def _priority_weight(self, priority: str) -> int:
        return {
            "immediate": 5,
            "high": 4,
            "normal": 3,
            "low": 2,
            "silent": 1,
        }.get(priority, 0)

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default


research_drift_detection_engine = ResearchDriftDetectionEngine()
