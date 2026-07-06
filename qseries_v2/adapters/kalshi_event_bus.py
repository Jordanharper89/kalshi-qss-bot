"""
ADP-003 Kalshi Event Bus Integration

Publishes normalized Kalshi markets to the CORE Event Bus.
"""

from qseries_v2.core.event_bus import event_bus
from .kalshi_adapter import kalshi_adapter


class KalshiEventBus:

    def publish_market(self, raw_market):
        market = kalshi_adapter.normalize_market(raw_market)

        payload = {
            "source": market.source,
            "ticker": market.ticker,
            "market": market,
            "evidence": market.as_evidence(),
        }

        event_bus.publish(
            "adapter.kalshi.market",
            payload,
        )

        return payload

    def publish_markets(self, raw_markets):
        return [self.publish_market(item) for item in raw_markets]


kalshi_event_bus = KalshiEventBus()
