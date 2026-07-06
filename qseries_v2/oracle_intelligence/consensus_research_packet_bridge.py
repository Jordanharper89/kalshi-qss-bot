"""
OI-055 Consensus Research Packet Bridge

Purpose:
- Combine OI-053 research packets with OI-054 consensus intelligence.
- Produce final Oracle research packet enriched with consensus validation.
- Preserve read-only Oracle / Q Series execution separation.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .oracle_research_packet_api_adapter import (
    oracle_research_packet_api_adapter,
    OracleResearchPacketAPIAdapter,
)
from .oracle_consensus_intelligence_engine import (
    oracle_consensus_intelligence_engine,
    OracleConsensusIntelligenceEngine,
)


class ConsensusResearchPacketBridge:
    module_name = "oi_055_consensus_research_packet_bridge"

    def __init__(
        self,
        packet_adapter: Optional[OracleResearchPacketAPIAdapter] = None,
        consensus_engine: Optional[OracleConsensusIntelligenceEngine] = None,
    ) -> None:
        self.packet_adapter = packet_adapter or oracle_research_packet_api_adapter
        self.consensus_engine = consensus_engine or oracle_consensus_intelligence_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "packet_adapter": self._safe_status(self.packet_adapter),
            "consensus_engine": self._safe_status(self.consensus_engine),
        }

    def build_consensus_packet(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        report_format: str = "terminal",
        include_raw: bool = True,
    ) -> Dict[str, Any]:
        base_packet = self.packet_adapter.build_packet(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            report_format=report_format,
            include_raw=include_raw,
        )

        synthesis = None

        if include_raw:
            synthesis = (
                base_packet
                .get("raw", {})
                .get("synthesis")
            )

        if synthesis:
            consensus = self.consensus_engine.build_consensus_from_synthesis(synthesis)
        else:
            consensus = self.consensus_engine.build_consensus(
                current_setup=current_setup,
                memory_type=memory_type,
                market_ticker=market_ticker,
                limit=limit,
            )

        enriched_summary = self._enrich_summary(
            base_packet.get("summary", {}),
            consensus.get("consensus", {}),
        )

        enriched_signals = self._enrich_signals(
            base_packet.get("signals", {}),
            consensus.get("consensus", {}),
        )

        packet = dict(base_packet)
        packet["module"] = self.module_name
        packet["packet_type"] = "oracle_consensus_research_packet"
        packet["summary"] = enriched_summary
        packet["signals"] = enriched_signals
        packet["consensus"] = consensus.get("consensus", {})
        packet["consensus_votes"] = consensus.get("votes", [])
        packet["consensus_explanation"] = consensus.get("explanation", [])
        packet["api"] = dict(packet.get("api", {}))
        packet["api"]["version"] = "oi-055"
        packet["api"]["consensus_enabled"] = True
        packet["api"]["execution_enabled"] = False

        if include_raw:
            packet.setdefault("raw", {})
            packet["raw"]["consensus"] = consensus

        return packet

    def build_terminal_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_consensus_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="terminal",
            include_raw=True,
        )

    def build_telegram_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_consensus_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="telegram",
            include_raw=False,
        )

    def build_api_packet(self, current_setup: Dict[str, Any], limit: int = 25) -> Dict[str, Any]:
        return self.build_consensus_packet(
            current_setup=current_setup,
            limit=limit,
            report_format="api",
            include_raw=True,
        )

    def _enrich_summary(self, summary: Dict[str, Any], consensus: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(summary)

        enriched.update({
            "consensus_side": consensus.get("consensus_side"),
            "consensus_score_pct": consensus.get("consensus_score_pct"),
            "agreement_pct": consensus.get("agreement_pct"),
            "disagreement_pct": consensus.get("disagreement_pct"),
            "research_stability": consensus.get("research_stability"),
            "research_certainty_index": consensus.get("research_certainty_index"),
            "outlier_engines": consensus.get("outlier_engines", []),
            "consensus_validated": consensus.get("consensus_side") not in {None, "UNKNOWN"},
        })

        return enriched

    def _enrich_signals(self, signals: Dict[str, Any], consensus: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(signals)

        enriched.update({
            "consensus_side": consensus.get("consensus_side"),
            "consensus_score_pct": consensus.get("consensus_score_pct"),
            "agreement_pct": consensus.get("agreement_pct"),
            "research_stability": consensus.get("research_stability"),
            "research_certainty_index": consensus.get("research_certainty_index"),
            "final_research_grade": self._final_grade(signals, consensus),
            "actionable": False,
            "execution_owner": "Q Series",
        })

        return enriched

    def _final_grade(self, signals: Dict[str, Any], consensus: Dict[str, Any]) -> str:
        base = signals.get("research_grade", "UNRATED")
        certainty = consensus.get("research_certainty_index")
        stability = str(consensus.get("research_stability") or "").lower()
        agreement = consensus.get("agreement_pct")

        if certainty is None or agreement is None:
            return base

        try:
            certainty = float(certainty)
            agreement = float(agreement)
        except Exception:
            return base

        if stability == "high" and certainty >= 85 and agreement >= 85:
            return self._upgrade(base)

        if stability == "low" or certainty < 60 or agreement < 60:
            return self._downgrade(base)

        return base

    def _upgrade(self, grade: str) -> str:
        order = ["WATCH", "B", "B+", "A-", "A", "A+"]
        if grade not in order:
            return grade
        return order[min(order.index(grade) + 1, len(order) - 1)]

    def _downgrade(self, grade: str) -> str:
        order = ["WATCH", "B", "B+", "A-", "A", "A+"]
        if grade not in order:
            return grade
        return order[max(order.index(grade) - 1, 0)]

    def _safe_status(self, obj: Any) -> str:
        try:
            return obj.status().get("status", "unknown")
        except Exception:
            return "error"


consensus_research_packet_bridge = ConsensusResearchPacketBridge()
