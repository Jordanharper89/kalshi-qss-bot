
from .base_provider import BaseProvider, ProviderResult


class KalshiProvider(BaseProvider):
    name = "kalshi"
    categories = ["market", "orderbook", "price", "volume", "liquidity"]

    def fetch(self, market=None, query=None):
        market = market or {}
        return ProviderResult(
            source=self.name,
            category="market",
            ticker=market.get("ticker"),
            data={
                "status": "placeholder",
                "message": "Kalshi provider registered. Wire API calls next.",
                "market": market,
            },
            confidence=75,
            freshness=75,
            relevance=90,
        ).to_dict()
