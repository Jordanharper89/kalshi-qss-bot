
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .news_intelligence_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    NewsIntelligenceDiscoveryCapability,
    NewsIntelligenceDiscoveryEngineContract,
    NewsIntelligenceFamily,
    NewsIntelligenceDiscoveryHealth,
    NewsIntelligenceDiscoveryRequest,
    NewsIntelligenceDiscoveryResult,
    NewsIntelligenceDiscoveryTelemetry,
)
from .news_intelligence_source_adapter import NewsArticleSnapshot, NewsIntelligenceSourceAdapter

SCHEMA_VERSION = "NID-003.1"
ENGINE_ID = "oracle.discovery.news_intelligence"


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


def _stable_text(v: Any) -> str:
    if isinstance(v, Mapping):
        return "{" + ",".join(f"{k}:{_stable_text(x)}" for k, x in sorted(v.items())) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(_stable_text(x) for x in v) + "]"
    return repr(v)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return prefix + "." + sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class NewsIntelligenceOpportunity:
    opportunity_id: str
    schema_version: str
    article_id: str
    title: str
    topic: str
    opportunity_type: str
    source_engine_id: str
    news_score: float
    impact_score: float
    relevance_score: float
    market_scope_score: float
    confidence: float
    universal_market: Mapping[str, Any]
    status: str
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "schema_version": self.schema_version,
            "article_id": self.article_id,
            "title": self.title,
            "topic": self.topic,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "news_score": self.news_score,
            "impact_score": self.impact_score,
            "relevance_score": self.relevance_score,
            "market_scope_score": self.market_scope_score,
            "confidence": self.confidence,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class NewsIntelligenceDiscoveryEngine(NewsIntelligenceDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[NewsArticleSnapshot]] = None,
        min_news_score: float = 0.55,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_news_score = float(min_news_score)

    def capabilities(self) -> NewsIntelligenceDiscoveryCapability:
        return NewsIntelligenceDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
            source_name="news_article_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "produces": "UniversalOpportunity-shaped news intelligence opportunities",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> NewsIntelligenceDiscoveryHealth:
        return NewsIntelligenceDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"engine_schema_version": self.schema_version, "read_only": True},
        )

    def discover(self, request: NewsIntelligenceDiscoveryRequest | None = None) -> NewsIntelligenceDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)

        opportunities = []
        rejected = 0
        for snapshot in snapshots:
            opp = self._build_opportunity(snapshot)
            if opp is None:
                rejected += 1
                continue
            opportunities.append(opp)

        opportunities = tuple(sorted(opportunities, key=lambda o: (-o.news_score, -o.confidence, o.article_id)))
        request_id = request.request_id if request is not None else "news.intelligence.discovery.default"

        telemetry = NewsIntelligenceDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            articles_seen=len({s.article_id for s in snapshots}),
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_news_score": self.min_news_score,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
            read_only=True,
        )

        return NewsIntelligenceDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(self, request: NewsIntelligenceDiscoveryRequest | None) -> Tuple[NewsArticleSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "news_snapshots", "articles", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(r, NewsArticleSnapshot) for r in record_tuple):
            return record_tuple

        adapter = NewsIntelligenceSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _impact_score(self, impact: str) -> float:
        return {"low": 0.25, "medium": 0.55, "high": 0.90, "critical": 1.0}.get(str(impact).lower(), 0.50)

    def _market_scope_score(self, snapshot: NewsArticleSnapshot) -> float:
        markets = set(snapshot.affected_markets)
        score = 0.10
        if "PREDICTION_MARKETS" in markets:
            score += 0.35
        if "RATES" in markets:
            score += 0.20
        if "EQUITIES" in markets:
            score += 0.15
        if "CRYPTO" in markets:
            score += 0.10
        if snapshot.entities:
            score += 0.10
        return round(min(1.0, score), 6)

    def _to_universal_market(self, snapshot: NewsArticleSnapshot) -> Mapping[str, Any]:
        return _freeze({
            "schema_family": "UMM",
            "market_type": "news_intelligence",
            "article_id": snapshot.article_id,
            "title": snapshot.title,
            "source": snapshot.source,
            "topic": snapshot.topic,
            "sentiment": snapshot.sentiment,
            "impact": snapshot.impact,
            "published_at": snapshot.published_at,
            "affected_markets": snapshot.affected_markets,
            "entities": snapshot.entities,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

    def _build_opportunity(self, snapshot: NewsArticleSnapshot) -> Optional[NewsIntelligenceOpportunity]:
        if not snapshot.article_id or not snapshot.title:
            return None

        impact_score = self._impact_score(snapshot.impact)
        relevance_score = snapshot.relevance_score
        market_scope_score = self._market_scope_score(snapshot)
        news_score = round(impact_score * 0.40 + relevance_score * 0.35 + market_scope_score * 0.25, 6)

        if news_score < self.min_news_score:
            return None

        confidence = round(min(1.0, news_score * 0.75 + relevance_score * 0.25), 6)

        identity = {
            "article_id": snapshot.article_id,
            "title": snapshot.title,
            "topic": snapshot.topic,
            "published_at": snapshot.published_at,
            "news_score": news_score,
        }

        explanation = MappingProxyType({
            "summary": "News article passed read-only impact, relevance, and market-scope scoring.",
            "article_id": snapshot.article_id,
            "title": snapshot.title,
            "impact_score": impact_score,
            "relevance_score": relevance_score,
            "market_scope_score": market_scope_score,
            "news_score": news_score,
            "rules": [
                "read_only_scan",
                "impact_score_guardrail",
                "relevance_score_guardrail",
                "market_scope_guardrail",
                "deterministic_opportunity_id",
                "no_execution_authority",
            ],
        })

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "source_engine_id": self.engine_id,
            "article_id": snapshot.article_id,
            "created_at": _utc_now_iso(),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return NewsIntelligenceOpportunity(
            opportunity_id=_stable_id("uop.news_intelligence", identity),
            schema_version="UOM-compatible/NID-003.1",
            article_id=snapshot.article_id,
            title=snapshot.title,
            topic=snapshot.topic,
            opportunity_type="news_intelligence_signal",
            source_engine_id=self.engine_id,
            news_score=news_score,
            impact_score=impact_score,
            relevance_score=relevance_score,
            market_scope_score=market_scope_score,
            confidence=confidence,
            universal_market=self._to_universal_market(snapshot),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = ["SCHEMA_VERSION", "ENGINE_ID", "NewsIntelligenceOpportunity", "NewsIntelligenceDiscoveryEngine"]
