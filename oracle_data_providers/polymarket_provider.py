
from .base_provider import BaseProvider, ProviderResult


class PolymarketProvider(BaseProvider):
    name = "polymarket"
    categories = ["comparison", "arbitrage", "prediction_market"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="comparison",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Polymarket comparison provider registered.",
            },
            confidence=60,
            freshness=60,
            relevance=70,
        ).to_dict()
