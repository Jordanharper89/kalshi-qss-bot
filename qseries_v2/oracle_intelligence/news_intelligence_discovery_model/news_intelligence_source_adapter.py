
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
