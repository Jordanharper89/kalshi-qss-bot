
from .base_provider import BaseProvider, ProviderResult


class SportsProvider(BaseProvider):
    name = "sports"
    categories = ["sports", "injury", "schedule", "odds", "props"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="sports",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Sports provider registered. Odds/injury wiring next.",
            },
            confidence=60,
            freshness=70,
            relevance=75,
        ).to_dict()
