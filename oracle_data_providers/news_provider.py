
from .base_provider import BaseProvider, ProviderResult


class NewsProvider(BaseProvider):
    name = "news"
    categories = ["news", "catalyst", "headline"]

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="news",
            ticker=(market or {}).get("ticker"),
            data={
                "status": "placeholder",
                "query": query,
                "message": "News provider registered. RSS/API wiring next.",
            },
            confidence=55,
            freshness=65,
            relevance=65,
        ).to_dict()
