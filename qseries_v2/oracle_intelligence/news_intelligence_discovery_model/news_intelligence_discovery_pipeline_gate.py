
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .news_intelligence_discovery_contract import NewsIntelligenceDiscoveryRequest, NewsIntelligenceFamily
from .news_intelligence_source_adapter import NewsIntelligenceSourceAdapter
from .news_intelligence_discovery_engine import NewsIntelligenceDiscoveryEngine

SCHEMA_VERSION = "NID-004"
GATE_ID = "oracle.discovery.gate.news_intelligence_pipeline"


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


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryGateReport:
    schema_version: str
    gate_id: str
    status: str
    passed_checks: int
    failed_checks: int
    warning_count: int
    checks: Mapping[str, bool]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": self.status,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "checks": dict(self.checks),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class NewsIntelligenceDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    read_only = True

    def __init__(self, source_name: str = "news_intelligence_gate_source", min_news_score: float = 0.55) -> None:
        self.source_name = str(source_name)
        self.min_news_score = float(min_news_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "read_only": True,
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def run(self, raw_records: Sequence[Any] | None = None) -> NewsIntelligenceDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = NewsIntelligenceSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = NewsIntelligenceDiscoveryRequest(
            request_id="nid004.pipeline.gate.a",
            family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
            source_name=self.source_name,
            article_ids=tuple(sorted({s.article_id for s in batch_a.snapshots})),
            topics=tuple(sorted({s.topic for s in batch_a.snapshots})),
            markets=tuple(sorted({m for s in batch_a.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = NewsIntelligenceDiscoveryRequest(
            request_id="nid004.pipeline.gate.b",
            family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
            source_name=self.source_name,
            article_ids=tuple(sorted({s.article_id for s in batch_b.snapshots})),
            topics=tuple(sorted({s.topic for s in batch_b.snapshots})),
            markets=tuple(sorted({m for s in batch_b.snapshots for m in s.affected_markets})),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = NewsIntelligenceDiscoveryEngine(min_news_score=self.min_news_score)
        report_a = engine.discover(request_a)
        report_b = engine.discover(request_b)

        ids_a = tuple(o.opportunity_id for o in report_a.opportunities)
        ids_b = tuple(o.opportunity_id for o in report_b.opportunities)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "batch_is_read_only": batch_a.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "discovery_report_is_read_only": report_a.read_only is True,
            "adapter_schema_ok": batch_a.schema_version == "NID-002",
            "engine_contract_schema_ok": report_a.schema_version == "NID-001",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "articles_seen": batch_a.telemetry.get("articles_seen") == 3,
            "adapter_deterministic_order": tuple(s.article_id for s in batch_a.snapshots) == tuple(s.article_id for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) == 2,
            "engine_replay_deterministic": ids_a == ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_article_id": all(bool(o.article_id) for o in report_a.opportunities),
            "all_opportunities_have_title": all(bool(o.title) for o in report_a.opportunities),
            "all_opportunities_have_score": all(o.news_score >= self.min_news_score for o in report_a.opportunities),
            "all_opportunities_have_confidence": all(0.0 <= o.confidence <= 1.0 for o in report_a.opportunities),
            "all_opportunities_have_explanation": all(bool(o.explanation) for o in report_a.opportunities),
            "all_opportunities_have_telemetry": all(bool(o.telemetry) for o in report_a.opportunities),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "news_intelligence"
                and o.universal_market.get("read_only") is True
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("order_allowed") is False
                and o.universal_market.get("position_sizing_allowed") is False
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.news_intelligence"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                and not hasattr(o, "route_id")
                for o in report_a.opportunities
            ),
            "immutable_universal_market": self._check_immutable_market(report_a),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "raw_records_seen": len(raw),
            "snapshots_emitted": len(batch_a.snapshots),
            "articles_seen": batch_a.telemetry.get("articles_seen"),
            "opportunities_emitted": len(report_a.opportunities),
            "passed_checks": passed,
            "failed_checks": failed,
            "warning_count": 0,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "deterministic_replay": ids_a == ids_b,
        })

        return NewsIntelligenceDiscoveryGateReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=_freeze(checks),
            telemetry=telemetry,
            read_only=True,
        )

    def _check_immutable_market(self, report: Any) -> bool:
        if not report.opportunities:
            return False
        try:
            report.opportunities[0].universal_market["execution_allowed"] = True
            return False
        except TypeError:
            return True

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
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
            },
            {
                "article_id": "article_minor",
                "title": "Local market commentary",
                "source": "SmallWire",
                "published_at": "2026-01-15T12:00:00Z",
                "topic": "local",
                "impact": "low",
                "relevance_score": 0.20,
                "affected_markets": ["LOCAL"],
            },
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "NewsIntelligenceDiscoveryGateReport",
    "NewsIntelligenceDiscoveryPipelineGate",
]
