"""
ADP-005 Kalshi Oracle Analysis Bridge

Takes raw Kalshi market data, converts it into Oracle Evidence,
then runs Oracle Intelligence analysis and returns a research packet.
"""

from .kalshi_adapter import kalshi_adapter
from .kalshi_oracle_bridge import kalshi_oracle_bridge
from qseries_v2.oi.oracle_api_integration import oracle_api_integration


class KalshiAnalysisBridge:

    def analyze_market(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)
        evidence = kalshi_oracle_bridge.market_to_evidence(raw_market)

        packet = oracle_api_integration.analyze(
            ticker=market.ticker,
            market_yes_price=market.yes_price or 0,
            evidence=[evidence],
        )

        return {
            "source": "kalshi",
            "market": market,
            "evidence": evidence,
            "packet": packet,
            "oracle_executes": False,
        }

    def analyze_markets(self, raw_markets):
        return [self.analyze_market(item) for item in raw_markets]


kalshi_analysis_bridge = KalshiAnalysisBridge()
