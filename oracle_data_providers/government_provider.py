
from .base_provider import BaseProvider, ProviderResult


class GovernmentProvider(BaseProvider):
    name = "government"
    categories = ["government", "official_data", "release", "filing"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="government",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Government provider registered. Official data wiring next.",
            },
            confidence=80,
            freshness=60,
            relevance=75,
        ).to_dict()
