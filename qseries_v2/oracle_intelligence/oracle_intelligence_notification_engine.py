"""
OI-065 Oracle Intelligence Notification Engine

Purpose:
- Convert Oracle drift detections into notification-ready payloads.
- Suppress noisy repeat notifications.
- Support Telegram/API/runtime notification formats.
- Preserve Oracle read-only boundary.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class OracleIntelligenceNotificationEngine:
    module_name = "oi_065_oracle_intelligence_notification_engine"

    def __init__(self) -> None:
        self._sent: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "notifications_tracked": len(self._sent),
        }

    def build_notification(
        self,
        drift_result: Dict[str, Any],
        channel: str = "telegram",
        force: bool = False,
    ) -> Dict[str, Any]:
        ticker = drift_result.get("ticker")
        severity = drift_result.get("drift_severity", "none")
        priority = drift_result.get("notification_priority", "silent")

        should_send = force or self._should_send(drift_result)

        payload = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "ticker": ticker,
            "channel": channel,
            "should_send": should_send,
            "severity": severity,
            "priority": priority,
            "dedupe_key": self._dedupe_key(drift_result),
            "message": self._format_message(drift_result, channel),
            "payload": self._payload(drift_result),
            "created_at": self._now(),
        }

        if should_send:
            self._sent[payload["dedupe_key"]] = payload

        return payload

    def build_portfolio_notifications(
        self,
        portfolio_drift_result: Dict[str, Any],
        channel: str = "telegram",
        force: bool = False,
    ) -> Dict[str, Any]:
        notifications = []

        for drift in portfolio_drift_result.get("top_drifts", []) or []:
            notification = self.build_notification(
                drift_result=drift,
                channel=channel,
                force=force,
            )
            if notification["should_send"]:
                notifications.append(notification)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "channel": channel,
            "notifications": notifications,
            "notification_count": len(notifications),
        }

    def notification_history(self, limit: int = 50) -> Dict[str, Any]:
        rows = list(self._sent.values())
        rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return {
            "status": "ok",
            "read_only": True,
            "count": len(rows),
            "notifications": rows[:limit],
        }

    def _should_send(self, drift_result: Dict[str, Any]) -> bool:
        severity = drift_result.get("drift_severity", "none")
        priority = drift_result.get("notification_priority", "silent")

        if severity == "none" or priority == "silent":
            return False

        key = self._dedupe_key(drift_result)

        if key in self._sent:
            return False

        return severity in {"minor", "moderate", "major", "critical"}

    def _dedupe_key(self, drift_result: Dict[str, Any]) -> str:
        ticker = drift_result.get("ticker", "UNKNOWN")
        severity = drift_result.get("drift_severity", "none")
        reasons = ",".join(sorted(drift_result.get("reason_codes", []) or []))
        return f"{ticker}|{severity}|{reasons}"

    def _payload(self, drift_result: Dict[str, Any]) -> Dict[str, Any]:
        summary = drift_result.get("summary", {}) or {}

        return {
            "ticker": drift_result.get("ticker"),
            "severity": drift_result.get("drift_severity"),
            "priority": drift_result.get("notification_priority"),
            "headline": summary.get("headline"),
            "reason_codes": drift_result.get("reason_codes", []),
            "consensus_side": summary.get("consensus_side"),
            "previous_consensus_side": summary.get("previous_consensus_side"),
            "consensus_score_drift": summary.get("consensus_score_drift"),
            "confidence_drift": summary.get("confidence_drift"),
            "probability_drift": summary.get("probability_drift"),
            "certainty_drift": summary.get("certainty_drift"),
            "current_grade": summary.get("current_grade"),
            "previous_grade": summary.get("previous_grade"),
            "current_stability": summary.get("current_stability"),
            "previous_stability": summary.get("previous_stability"),
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

    def _format_message(self, drift_result: Dict[str, Any], channel: str) -> str:
        payload = self._payload(drift_result)

        if channel == "telegram":
            return self._telegram_message(payload)

        if channel == "api":
            return self._plain_message(payload)

        return self._terminal_message(payload)

    def _telegram_message(self, payload: Dict[str, Any]) -> str:
        lines = [
            "🧠 Oracle Research Drift Alert",
            "",
            f"*{payload.get('headline') or 'Oracle drift detected'}*",
            f"Severity: {str(payload.get('severity')).upper()}",
            f"Priority: {payload.get('priority')}",
            "",
            f"Consensus: {payload.get('previous_consensus_side')} → {payload.get('consensus_side')}",
            f"Consensus Drift: {payload.get('consensus_score_drift')}",
            f"Confidence Drift: {payload.get('confidence_drift')}",
            f"Grade: {payload.get('previous_grade')} → {payload.get('current_grade')}",
            "",
            "Reasons:",
        ]

        for reason in payload.get("reason_codes", []):
            lines.append(f"• {reason}")

        lines.append("")
        lines.append("_Read-only Oracle research. Q Series controls execution._")
        return "\n".join(lines)

    def _terminal_message(self, payload: Dict[str, Any]) -> str:
        lines = [
            "=" * 54,
            " ORACLE RESEARCH DRIFT ALERT",
            "=" * 54,
            f"Ticker: {payload.get('ticker')}",
            f"Severity: {payload.get('severity')}",
            f"Priority: {payload.get('priority')}",
            f"Headline: {payload.get('headline')}",
            f"Consensus: {payload.get('previous_consensus_side')} -> {payload.get('consensus_side')}",
            f"Consensus Drift: {payload.get('consensus_score_drift')}",
            f"Confidence Drift: {payload.get('confidence_drift')}",
            f"Grade: {payload.get('previous_grade')} -> {payload.get('current_grade')}",
            "Reasons:",
        ]

        for reason in payload.get("reason_codes", []):
            lines.append(f"- {reason}")

        lines.append("Read-only Oracle research. Q Series controls execution.")
        return "\n".join(lines)

    def _plain_message(self, payload: Dict[str, Any]) -> str:
        return (
            f"{payload.get('headline')} | "
            f"severity={payload.get('severity')} | "
            f"priority={payload.get('priority')} | "
            f"consensus={payload.get('previous_consensus_side')}->{payload.get('consensus_side')} | "
            f"confidence_drift={payload.get('confidence_drift')}"
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_intelligence_notification_engine = OracleIntelligenceNotificationEngine()
