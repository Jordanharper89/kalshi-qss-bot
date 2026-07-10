from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "news_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "news_intelligence_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_nid_005_news_intelligence_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .news_intelligence_discovery_contract import NewsIntelligenceDiscoveryRequest, NewsIntelligenceFamily
from .news_intelligence_discovery_engine import NewsIntelligenceDiscoveryEngine

SCHEMA_VERSION = "NID-005"
BRIDGE_ID = "oracle.discovery.bridge.news_intelligence_registry"


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
class NewsIntelligenceRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    article_id: str
    title: str
    opportunity_type: str
    source_engine_id: str
    registry_status: str
    registry_key: str
    payload: Mapping[str, Any]
    audit: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "opportunity_id": self.opportunity_id,
            "article_id": self.article_id,
            "title": self.title,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[NewsIntelligenceRegistryRecord, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": self.status,
            "records": [r.to_dict() for r in self.records],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class NewsIntelligenceDiscoveryRegistryBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "NID-003.1 NewsIntelligenceDiscoveryResult",
            "emits": "registry-ready immutable news intelligence records",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def bridge_report(self, discovery_report: Any) -> NewsIntelligenceRegistryBridgeReport:
        started_at = _utc_now_iso()
        opportunities = tuple(getattr(discovery_report, "opportunities", ()) or ())
        records = tuple(sorted((self._record_from_opportunity(o) for o in opportunities), key=lambda r: r.registry_key))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "opportunities_seen": len(opportunities),
            "records_emitted": len(records),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return NewsIntelligenceRegistryBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if records else "empty",
            records=records,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_and_bridge(
        self,
        raw_records: Sequence[Any],
        source_name: str = "news_intelligence_registry_bridge_source",
        min_news_score: float = 0.55,
    ) -> NewsIntelligenceRegistryBridgeReport:
        request = NewsIntelligenceDiscoveryRequest(
            request_id="nid005.news.intelligence.registry.bridge",
            family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )
        report = NewsIntelligenceDiscoveryEngine(min_news_score=min_news_score).discover(request)
        return self.bridge_report(report)

    def _record_from_opportunity(self, o: Any) -> NewsIntelligenceRegistryRecord:
        opportunity_id = str(getattr(o, "opportunity_id"))
        article_id = str(getattr(o, "article_id"))
        title = str(getattr(o, "title"))
        opportunity_type = str(getattr(o, "opportunity_type"))
        source_engine_id = str(getattr(o, "source_engine_id"))
        registry_key = f"{source_engine_id}:{opportunity_type}:{article_id}:{opportunity_id}"

        payload = MappingProxyType({
            "opportunity_id": opportunity_id,
            "article_id": article_id,
            "title": title,
            "topic": getattr(o, "topic", None),
            "opportunity_type": opportunity_type,
            "source_engine_id": source_engine_id,
            "news_score": getattr(o, "news_score", None),
            "impact_score": getattr(o, "impact_score", None),
            "relevance_score": getattr(o, "relevance_score", None),
            "market_scope_score": getattr(o, "market_scope_score", None),
            "confidence": getattr(o, "confidence", None),
            "status": getattr(o, "status", None),
            "universal_market": _freeze(getattr(o, "universal_market", {})),
            "explanation": _freeze(getattr(o, "explanation", {})),
            "telemetry": _freeze(getattr(o, "telemetry", {})),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "registered_from": "NID news intelligence discovery",
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return NewsIntelligenceRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            article_id=article_id,
            title=title,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
            registry_status="registry_ready",
            registry_key=registry_key,
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "NewsIntelligenceRegistryRecord",
    "NewsIntelligenceRegistryBridgeReport",
    "NewsIntelligenceDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_registry_bridge import (
    NewsIntelligenceDiscoveryRegistryBridge,
)


def test_nid_005_news_intelligence_discovery_registry_bridge():
    raw = [
        {"article_id": "article_b", "headline": "Fed signals slower cuts after inflation surprise", "publisher": "MarketWire", "link": "https://example.test/fed", "time": "2026-01-15T14:00:00Z", "category": "fed", "sentiment": "hawkish", "importance": "high", "relevance": 0.91, "markets": "RATES, EQUITIES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "article_a", "title": "CPI comes in hotter than expected", "source": "EconomicDesk", "url": "https://example.test/cpi", "published_at": "2026-01-15T13:30:00Z", "topic": "inflation", "sentiment": "negative", "impact": "high", "relevance_score": 0.95, "affected_markets": ["RATES", "PREDICTION_MARKETS"], "entities": ["CPI", "USD"]},
        {"article_id": "article_minor", "title": "Local market commentary", "source": "SmallWire", "published_at": "2026-01-15T12:00:00Z", "topic": "local", "impact": "low", "relevance_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    bridge = NewsIntelligenceDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="nid_005_test_source", min_news_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="nid_005_test_source", min_news_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "NID-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.news_intelligence_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    assert [r.registry_key for r in report_a.records] == [r.registry_key for r in report_b.records]

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "news_intelligence"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] NID-005 News Intelligence Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_005_news_intelligence_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .news_intelligence_discovery_registry_bridge import (
        NewsIntelligenceDiscoveryRegistryBridge,
        NewsIntelligenceRegistryBridgeReport,
        NewsIntelligenceRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "NewsIntelligenceDiscoveryRegistryBridge" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" NID-005 INSTALLER")
print(" News Intelligence Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] NID-005 installed")
print()
print("Run:")
print("py test_nid_005_news_intelligence_discovery_registry_bridge.py")