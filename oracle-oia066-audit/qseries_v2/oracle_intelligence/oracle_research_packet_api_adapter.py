"""
OI-053 Oracle Research Packet API Adapter

Purpose:
- Provide a stable API-style adapter for Oracle research packets.
- Wrap OI-051 synthesis and OI-052 report composer.
- Give Telegram, Oracle Terminal, and future web/API routes one clean entry point.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .oracle_intelligence_synthesis_engine import (
    oracle_intelligence_synthesis_engine,
    OracleIntelligenceSynthesisEngine,
)
from .oracle_research_report_composer import (
    oracle_research_report_composer,
    OracleResearchReportComposer,
)


class OracleResearchPacketAPIAdapter:
    module_name = "oi_053_oracle_research_packet_api_adapter"

    def __init__(
        self,
        synthesis_engine: Optional[OracleIntelligenceSynthesisEngine] = None,
        report_composer: Optional[OracleResearchReportComposer] = None,
    ) -> None:
        self.synthesis_engine = synthesis_engine or oracle_intelligence_synthesis_engine
        self.report_composer = report_composer or oracle_research_report_composer

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "synthesis_engine": self._safe_status(self.synthesis_engine),
            "report_composer": self._safe_status(self.report_composer),
        }

    def build_packet(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        report_format: str = "terminal",
        include_raw: bool = True,
    ) -> Dict[str, Any]:
        synthesis = self.synthesis_engine.synthesize(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            include_graph=True,
        )

        report = self.report_composer.compose_from_synthesis(
            synthesis=synthesis,
            format=report_format,
        )

        summary = synthesis.get("summary", {})

        packet = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "packet_type": "oracle_research_packet",
            "market_ticker": summary.get("market_ticker"),
            "summary": summary,
            "report_format": report_format,
            "report": report.get("report"),
            "sections": report.get("sections", []),
            "signals": self._signals(summary),
            "api": {
                "version": "oi-053",
                "stable": True,
                "execution_enabled": False,
            },
        }

        if include_raw:
            packet["raw"] = {
                "synthesis": synthesis,
                "report": report,
            }

        return packet

    def build_terminal_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="terminal",
            include_raw=True,
        )

    def build_telegram_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="telegram",
            include_raw=False,
        )

    def build_api_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="api",
            include_raw=True,
        )

    def _signals(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        confidence = summary.get("adjusted_confidence")
        probability = summary.get("expected_probability")
        risk = summary.get("risk_level")
        tail = summary.get("tail_risk_level")

        research_grade = self._research_grade(confidence, probability, risk, tail)

        return {
            "expected_resolution": summary.get("expected_resolution"),
            "expected_probability": probability,
            "adjusted_confidence": confidence,
            "confidence_delta": summary.get("confidence_delta"),
            "risk_level": risk,
            "tail_risk_level": tail,
            "research_grade": research_grade,
            "actionable": False,
            "execution_owner": "Q Series",
        }

    def _research_grade(
        self,
        confidence: Any,
        probability: Any,
        risk: Any,
        tail: Any,
    ) -> str:
        try:
            c = float(confidence or 0)
            p = float(probability or 0)
            if p <= 1:
                p *= 100
        except Exception:
            return "UNRATED"

        risk = str(risk or "").lower()
        tail = str(tail or "").lower()

        penalty = 0
        if risk == "high":
            penalty += 10
        elif risk == "medium":
            penalty += 4

        if tail == "high":
            penalty += 10
        elif tail == "medium":
            penalty += 4

        score = (c * 0.60) + (p * 0.40) - penalty

        if score >= 90:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 80:
            return "A-"
        if score >= 75:
            return "B+"
        if score >= 70:
            return "B"
        return "WATCH"

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


oracle_research_packet_api_adapter = OracleResearchPacketAPIAdapter()
