
from .base_provider import BaseProvider, ProviderResult


class EconomicsProvider(BaseProvider):
    name = "economics"
    categories = ["economics", "cpi", "jobs", "fed", "rates", "inflation", "oil"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="economics",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Economics provider registered. FRED/BLS/BEA/EIA wiring next.",
            },
            confidence=70,
            freshness=65,
            relevance=75,
        ).to_dict()
