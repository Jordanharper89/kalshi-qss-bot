from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "oracle_data_providers"
PKG.mkdir(exist_ok=True)

(PKG / "__init__.py").write_text("", encoding="utf-8")

(PKG / "base_provider.py").write_text(r'''
"""
ORACLE-039 — Universal Data Provider Base
"""

import time


def now():
    return time.time()


class ProviderResult:
    def __init__(self, source, category, ticker=None, data=None, confidence=50, freshness=50, relevance=50):
        self.source = source
        self.category = category
        self.ticker = ticker
        self.data = data or {}
        self.confidence = confidence
        self.freshness = freshness
        self.relevance = relevance
        self.timestamp = now()

    def to_dict(self):
        return {
            "source": self.source,
            "category": self.category,
            "ticker": self.ticker,
            "data": self.data,
            "confidence": self.confidence,
            "freshness": self.freshness,
            "relevance": self.relevance,
            "timestamp": self.timestamp,
        }


class BaseProvider:
    name = "base"
    categories = []

    def enabled(self):
        return True

    def health(self):
        return {
            "provider": self.name,
            "enabled": self.enabled(),
            "categories": self.categories,
            "status": "ok",
        }

    def fetch(self, market=None, query=None):
        return ProviderResult(
            source=self.name,
            category="unknown",
            ticker=(market or {}).get("ticker"),
            data={"message": "base provider placeholder"},
        ).to_dict()
''', encoding="utf-8")

(PKG / "kalshi_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "polymarket_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "news_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "weather_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "economics_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "sports_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "crypto_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "government_provider.py").write_text(r'''
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
''', encoding="utf-8")

(PKG / "provider_registry.py").write_text(r'''
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
''', encoding="utf-8")

Path("oracle_data_provider_registry.py").write_text(r'''
"""
Compatibility wrapper for ORACLE-039 provider registry.
"""

from oracle_data_providers.provider_registry import (
    oracle_data_provider_registry,
    OracleProviderRegistry,
    diagnostics,
)

if __name__ == "__main__":
    print(oracle_data_provider_registry.diagnostics_text())
''', encoding="utf-8")

print("===================================")
print(" ORACLE-039 INSTALLED")
print(" Universal Data Provider Layer")
print("===================================")
print()
print("Created:")
print(" oracle_data_providers/")
print(" oracle_data_provider_registry.py")
print()
print("Test:")
print(" python oracle_data_provider_registry.py")