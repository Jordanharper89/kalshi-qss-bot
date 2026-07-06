"""
ADP-004 Kalshi to Oracle Evidence Bridge

Converts normalized Kalshi market payloads into Oracle Evidence objects.
"""

from qseries_v2.oi.evidence_engine import Evidence, evidence_engine
from .kalshi_adapter import kalshi_adapter


class KalshiOracleBridge:

    def market_to_evidence(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)
        evidence_data = market.as_evidence()

        return Evidence(
            source=evidence_data["source"],
            category=evidence_data["category"],
            value=evidence_data["value"],
        )

    def ingest_market(self, raw_market):
        evidence = self.market_to_evidence(raw_market)
        evidence_engine.add(evidence)
        return evidence

    def ingest_markets(self, raw_markets):
        return [self.ingest_market(item) for item in raw_markets]


kalshi_oracle_bridge = KalshiOracleBridge()
