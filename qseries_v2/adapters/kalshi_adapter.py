"""
ADP-001 Kalshi Adapter

Converts Kalshi-style market data into Oracle's UniversalMarket format.
This adapter does NOT execute trades.
"""

from .universal_market_schema import universal_market_schema


class KalshiAdapter:

    source = "kalshi"
    adapter_id = "adp.kalshi"
    version = "0.1.0"

    def normalize_market(self, raw):
        market_id = raw.get("id") or raw.get("market_id") or raw.get("ticker")
        ticker = raw.get("ticker") or raw.get("market_ticker") or market_id
        title = raw.get("title") or raw.get("subtitle") or raw.get("name") or ticker

        yes_price = (
            raw.get("yes_price")
            or raw.get("yes_bid")
            or raw.get("last_price")
            or raw.get("yes_ask")
        )

        no_price = (
            raw.get("no_price")
            or raw.get("no_bid")
            or raw.get("no_ask")
        )

        return universal_market_schema.create(
            source=self.source,
            market_id=market_id,
            ticker=ticker,
            title=title,
            category=raw.get("category", "unknown"),
            status=raw.get("status", "unknown"),
            yes_price=yes_price,
            no_price=no_price,
            last_price=raw.get("last_price"),
            volume=raw.get("volume"),
            liquidity=raw.get("liquidity"),
            open_interest=raw.get("open_interest"),
            close_time=raw.get("close_time", ""),
            event_ticker=raw.get("event_ticker", ""),
            raw=raw,
        )

    def normalize_markets(self, raw_markets):
        return [self.normalize_market(item) for item in raw_markets]

    def health(self):
        return {
            "status": "ready",
            "adapter_id": self.adapter_id,
            "source": self.source,
            "version": self.version,
            "executes_trades": False,
        }


kalshi_adapter = KalshiAdapter()
