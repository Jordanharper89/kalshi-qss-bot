
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
