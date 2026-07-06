
from .base_provider import BaseProvider, ProviderResult


class WeatherProvider(BaseProvider):
    name = "weather"
    categories = ["weather", "temperature", "rain", "storm", "climate"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="weather",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "message": "Weather provider registered. API key wiring next.",
            },
            confidence=65,
            freshness=70,
            relevance=70,
        ).to_dict()
