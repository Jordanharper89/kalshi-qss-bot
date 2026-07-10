from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "news_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ADAPTER_FILE = MODULE_DIR / "news_intelligence_source_adapter.py"
TEST_FILE = ROOT / "test_nid_002_news_intelligence_source_adapter.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ADAPTER_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

SCHEMA_VERSION = "NID-002"
ADAPTER_ID = "oracle.discovery.source.news_intelligence"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


def _read(raw: Any, key: str, default: Any = None) -> Any:
    return raw.get(key, default) if isinstance(raw, Mapping) else getattr(raw, key, default)


def _float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _stable_text(v: Any) -> str:
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(x)}" for k, x in sorted(v.items())) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return prefix + "." + sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class NewsArticleSnapshot:
    article_id: str
    title: str
    source: str
    url: str
    published_at: str
    topic: str
    sentiment: str
    impact: str
    relevance_score: float
    affected_markets: Tuple[str, ...] = field(default_factory=tuple)
    entities: Tuple[str, ...] = field(default_factory=tuple)
    summary: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "article_id", str(self.article_id))
        object.__setattr__(self, "title", str(self.title))
        object.__setattr__(self, "source", str(self.source).lower())
        object.__setattr__(self, "url", str(self.url))
        object.__setattr__(self, "published_at", str(self.published_at))
        object.__setattr__(self, "topic", str(self.topic).lower())
        object.__setattr__(self, "sentiment", str(self.sentiment).lower())
        object.__setattr__(self, "impact", str(self.impact).lower())
        object.__setattr__(self, "relevance_score", max(0.0, min(1.0, _float(self.relevance_score))))
        object.__setattr__(self, "affected_markets", tuple(str(m).upper() for m in self.affected_markets))
        object.__setattr__(self, "entities", tuple(str(e).upper() for e in self.entities))
        object.__setattr__(self, "summary", str(self.summary or ""))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "article_id": self.article_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at,
            "topic": self.topic,
            "sentiment": self.sentiment,
            "impact": self.impact,
            "relevance_score": self.relevance_score,
            "affected_markets": list(self.affected_markets),
            "entities": list(self.entities),
            "summary": self.summary,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceSourceBatch:
    schema_version: str
    adapter_id: str
    source_name: str
    snapshots: Tuple[NewsArticleSnapshot, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class NewsIntelligenceSourceAdapter:
    schema_version = SCHEMA_VERSION
    adapter_id = ADAPTER_ID
    read_only = True

    def __init__(self, source_name: str = "generic_news_intelligence") -> None:
        self.source_name = str(source_name)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "read_only": True,
            "normalizes_to": "NewsArticleSnapshot",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def normalize_batch(self, raw_records: Sequence[Any]) -> NewsIntelligenceSourceBatch:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or ())
        snapshots = tuple(sorted((self.normalize_record(r) for r in raw), key=lambda s: (s.published_at, s.source, s.article_id)))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "source_name": self.source_name,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(snapshots),
            "articles_seen": len({s.article_id for s in snapshots}),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return NewsIntelligenceSourceBatch(
            schema_version=self.schema_version,
            adapter_id=self.adapter_id,
            source_name=self.source_name,
            snapshots=snapshots,
            telemetry=telemetry,
            read_only=True,
        )

    def normalize_record(self, raw: Any) -> NewsArticleSnapshot:
        title = str(_read(raw, "title", _read(raw, "headline", "Untitled News Article")))
        source = str(_read(raw, "source", _read(raw, "publisher", self.source_name)))
        url = str(_read(raw, "url", _read(raw, "link", "")))
        published_at = str(_read(raw, "published_at", _read(raw, "time", _read(raw, "timestamp", ""))))
        topic = str(_read(raw, "topic", _read(raw, "category", "market_moving_news")))
        sentiment = str(_read(raw, "sentiment", "neutral"))
        impact = str(_read(raw, "impact", _read(raw, "importance", "medium")))
        relevance_score = _float(_read(raw, "relevance_score", _read(raw, "relevance", 0.5)))

        article_id = str(_read(raw, "article_id", _read(raw, "id", ""))) or _stable_id("news.article", {
            "title": title,
            "source": source,
            "url": url,
            "published_at": published_at,
            "topic": topic,
        })

        markets = _read(raw, "affected_markets", _read(raw, "markets", ()))
        if isinstance(markets, str):
            markets = tuple(x.strip() for x in markets.split(",") if x.strip())

        entities = _read(raw, "entities", _read(raw, "symbols", ()))
        if isinstance(entities, str):
            entities = tuple(x.strip() for x in entities.split(",") if x.strip())

        meta = dict(_read(raw, "metadata", {}) or {})
        meta["source_name"] = self.source_name
        meta["adapter_id"] = self.adapter_id

        return NewsArticleSnapshot(
            article_id=article_id,
            title=title,
            source=source,
            url=url,
            published_at=published_at,
            topic=topic,
            sentiment=sentiment,
            impact=impact,
            relevance_score=relevance_score,
            affected_markets=tuple(markets or ()),
            entities=tuple(entities or ()),
            summary=str(_read(raw, "summary", _read(raw, "description", ""))),
            metadata=meta,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ADAPTER_ID",
    "NewsArticleSnapshot",
    "NewsIntelligenceSourceBatch",
    "NewsIntelligenceSourceAdapter",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_source_adapter import (
    NewsIntelligenceSourceAdapter,
)


def test_nid_002_news_intelligence_source_adapter():
    raw = [
        {
            "article_id": "article_b",
            "headline": "Fed signals slower cuts after inflation surprise",
            "publisher": "MarketWire",
            "link": "https://example.test/fed",
            "time": "2026-01-15T14:00:00Z",
            "category": "fed",
            "sentiment": "hawkish",
            "importance": "high",
            "relevance": 0.91,
            "markets": "RATES, EQUITIES, PREDICTION_MARKETS",
            "symbols": "FED, CPI",
            "description": "Fed commentary reprices rate-cut expectations.",
        },
        {
            "id": "article_a",
            "title": "CPI comes in hotter than expected",
            "source": "EconomicDesk",
            "url": "https://example.test/cpi",
            "published_at": "2026-01-15T13:30:00Z",
            "topic": "inflation",
            "sentiment": "negative",
            "impact": "high",
            "relevance_score": 0.95,
            "affected_markets": ["RATES", "PREDICTION_MARKETS"],
            "entities": ["CPI", "USD"],
            "summary": "Inflation data surprised above consensus.",
        },
    ]

    adapter = NewsIntelligenceSourceAdapter(source_name="nid_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()
    batch_a = adapter.normalize_batch(raw)
    batch_b = adapter.normalize_batch(list(reversed(raw)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_a.schema_version == "NID-002"
    assert batch_a.adapter_id == "oracle.discovery.source.news_intelligence"
    assert batch_a.read_only is True
    assert len(batch_a.snapshots) == 2

    order_a = [s.article_id for s in batch_a.snapshots]
    order_b = [s.article_id for s in batch_b.snapshots]
    assert order_a == order_b
    assert order_a == ["article_a", "article_b"]

    first = batch_a.snapshots[0]
    assert first.article_id == "article_a"
    assert first.title == "CPI comes in hotter than expected"
    assert first.source == "economicdesk"
    assert first.topic == "inflation"
    assert first.sentiment == "negative"
    assert first.impact == "high"
    assert first.relevance_score == 0.95
    assert first.affected_markets == ("RATES", "PREDICTION_MARKETS")
    assert first.entities == ("CPI", "USD")
    assert first.read_only is True

    try:
        first.metadata["x"] = "mutation"
        raise AssertionError("metadata should be immutable")
    except TypeError:
        pass

    d = batch_a.to_dict()
    assert d["schema_version"] == "NID-002"
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["articles_seen"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] NID-002 News Intelligence Source Adapter")
    print({
        "schema_version": d["schema_version"],
        "adapter_id": d["adapter_id"],
        "snapshots": len(d["snapshots"]),
        "articles_seen": d["telemetry"]["articles_seen"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_002_news_intelligence_source_adapter()
'''

INIT_EXPORT = '''
try:
    from .news_intelligence_source_adapter import (
        NewsArticleSnapshot,
        NewsIntelligenceSourceBatch,
        NewsIntelligenceSourceAdapter,
    )
except Exception:
    pass
'''

ADAPTER_FILE.write_text(ADAPTER_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "NewsIntelligenceSourceAdapter" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" NID-002 INSTALLER")
print(" News Intelligence Source Adapter")
print("========================================")
print(f"[OK] Wrote {ADAPTER_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] NID-002 installed")
print()
print("Run:")
print("py test_nid_002_news_intelligence_source_adapter.py")