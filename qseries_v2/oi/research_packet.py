"""
OI-014 Research Packet Engine

Creates a structured packet containing the full Oracle decision output:
decision, recommendation, explanation, report, evidence, and metadata.
"""

from datetime import datetime
from .research_report import research_report_engine


class ResearchPacketEngine:

    def create(self, decision, evidence=None):
        evidence = evidence or []
        recommendation = decision.get("recommendation", {})
        report = research_report_engine.generate(decision)

        packet = {
            "packet_type": "oracle_research_packet",
            "created_at": datetime.utcnow().isoformat(),
            "ticker": decision.get("ticker"),
            "action": recommendation.get("action"),
            "confidence": recommendation.get("confidence"),
            "fair_yes_price": recommendation.get("fair_yes_price"),
            "market_yes_price": recommendation.get("market_yes_price"),
            "edge": recommendation.get("edge"),
            "reason": recommendation.get("reason"),
            "decision": decision,
            "recommendation": recommendation,
            "explanation": decision.get("explanation"),
            "report": report,
            "evidence_count": len(evidence),
            "evidence": [
                {
                    "source": getattr(item, "source", "unknown"),
                    "category": getattr(item, "category", "unknown"),
                    "value": getattr(item, "value", {}),
                    "timestamp": getattr(item, "timestamp", ""),
                }
                for item in evidence
            ],
            "oracle_executes": False,
        }

        return packet


research_packet_engine = ResearchPacketEngine()
