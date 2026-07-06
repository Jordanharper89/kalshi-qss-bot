"""
OI-017 Event Bus Integration

Publishes Oracle Intelligence events onto the CORE Event Bus.
"""

from qseries_v2.core.event_bus import event_bus
from .oracle_intelligence_service import oracle_intelligence_service


class OracleEventBusIntegration:

    def analyze(self, ticker, market_yes_price, evidence):
        packet = oracle_intelligence_service.analyze(
            ticker=ticker,
            market_yes_price=market_yes_price,
            evidence=evidence,
        )

        event_bus.publish(
            "oracle.analysis.completed",
            {
                "ticker": packet["ticker"],
                "action": packet["action"],
                "confidence": packet["confidence"],
                "packet": packet,
            },
        )

        return packet

    def resolve(self, ticker, outcome):
        result = oracle_intelligence_service.resolve(ticker, outcome)

        event_bus.publish(
            "oracle.market.resolved",
            {
                "ticker": ticker,
                "outcome": outcome,
            },
        )

        return result


oracle_event_bus = OracleEventBusIntegration()
