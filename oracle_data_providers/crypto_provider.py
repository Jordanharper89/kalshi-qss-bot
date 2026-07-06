
from .base_provider import BaseProvider, ProviderResult


class CryptoProvider(BaseProvider):
    name = "crypto"
    categories = ["crypto", "btc", "eth", "sol", "price", "volatility"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="crypto",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Crypto provider registered. Price feed wiring next.",
            },
            confidence=70,
            freshness=80,
            relevance=80,
        ).to_dict()
