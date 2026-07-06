
"""
ORACLE-039 — Provider Registry
"""

from .kalshi_provider import KalshiProvider
from .polymarket_provider import PolymarketProvider
from .news_provider import NewsProvider
from .weather_provider import WeatherProvider
from .economics_provider import EconomicsProvider
from .sports_provider import SportsProvider
from .crypto_provider import CryptoProvider
from .government_provider import GovernmentProvider


class OracleProviderRegistry:
    def __init__(self):
        self.providers = {}
        self.register_defaults()

    def register(self, provider):
        self.providers[provider.name] = provider

    def register_defaults(self):
        for provider in [
            KalshiProvider(),
            PolymarketProvider(),
            NewsProvider(),
            WeatherProvider(),
            EconomicsProvider(),
            SportsProvider(),
            CryptoProvider(),
            GovernmentProvider(),
        ]:
            self.register(provider)

    def list_providers(self):
        return sorted(self.providers.keys())

    def health(self):
        return {
            name: provider.health()
            for name, provider in self.providers.items()
        }

    def fetch_all(self, market=None, query=None, categories=None):
        results = []
        categories = set(categories or [])

        for provider in self.providers.values():
            if categories:
                if not set(provider.categories).intersection(categories):
                    continue

            try:
                results.append(provider.fetch(market=market, query=query))
            except Exception as e:
                results.append({
                    "source": provider.name,
                    "category": "error",
                    "ticker": (market or {}).get("ticker"),
                    "data": {"error": str(e)},
                    "confidence": 0,
                    "freshness": 0,
                    "relevance": 0,
                })

        return results

    def diagnostics_text(self):
        lines = []
        lines.append("🧠 ORACLE DATA PROVIDERS")
        lines.append("")
        lines.append(f"Providers Registered: {len(self.providers)}")
        lines.append("")

        for name in self.list_providers():
            provider = self.providers[name]
            lines.append(f"- {name}: {', '.join(provider.categories)}")

        return "\n".join(lines)


oracle_data_provider_registry = OracleProviderRegistry()


def diagnostics():
    return {
        "module": "oracle_data_providers.provider_registry",
        "status": "ok",
        "providers": oracle_data_provider_registry.list_providers(),
    }


if __name__ == "__main__":
    print(oracle_data_provider_registry.diagnostics_text())
