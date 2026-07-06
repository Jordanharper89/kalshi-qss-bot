"""
OI-015 Oracle Intelligence Service

High-level service wrapper for Oracle Intelligence.
This is the main entry point for research packets.

Oracle:
- researches
- scores
- explains
- learns

Oracle never executes trades.
"""

from .calibrated_pipeline import calibrated_decision_pipeline
from .research_packet import research_packet_engine
from .learning_ledger import learning_ledger
from .learning_loop import oracle_learning_loop


class OracleIntelligenceService:

    service_id = "oracle.intelligence"
    name = "Oracle Intelligence Service"
    category = "OI"
    version = "0.15.0"

    def analyze(self, ticker, market_yes_price, evidence):
        decision = calibrated_decision_pipeline.run(
            ticker=ticker,
            market_yes_price=market_yes_price,
            evidence=evidence,
        )

        packet = research_packet_engine.create(decision, evidence)

        if packet.get("action") != "PASS":
            learning_ledger.record_recommendation(packet["recommendation"])

        return packet

    def resolve(self, ticker, outcome):
        return learning_ledger.resolve(ticker, outcome)

    def review(self):
        return oracle_learning_loop.run(learning_ledger.records)

    def health(self):
        return {
            "status": "ready",
            "service_id": self.service_id,
            "version": self.version,
            "oracle_executes": False,
            "records": len(learning_ledger.records),
        }


oracle_intelligence_service = OracleIntelligenceService()
