from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "news_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "news_intelligence_discovery_contract.py"
TEST_FILE = ROOT / "test_nid_001_news_intelligence_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

SCHEMA_VERSION = "NID-001"
CONTRACT_ID = "oracle.discovery.contract.news_intelligence"


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


class NewsIntelligenceFamily(str, Enum):
    BREAKING_NEWS = "breaking_news"
    MARKET_MOVING_NEWS = "market_moving_news"
    REGULATORY_NEWS = "regulatory_news"
    EARNINGS_NEWS = "earnings_news"
    GEOPOLITICAL_NEWS = "geopolitical_news"
    SPORTS_NEWS = "sports_news"
    WEATHER_NEWS = "weather_news"
    PREDICTION_MARKET_NEWS = "prediction_market_news"


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryRequest:
    request_id: str
    family: NewsIntelligenceFamily
    source_name: str
    article_ids: Tuple[str, ...] = field(default_factory=tuple)
    topics: Tuple[str, ...] = field(default_factory=tuple)
    markets: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "article_ids", tuple(str(x) for x in self.article_ids))
        object.__setattr__(self, "topics", tuple(str(x).lower() for x in self.topics))
        object.__setattr__(self, "markets", tuple(str(x).upper() for x in self.markets))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "article_ids": list(self.article_ids),
            "topics": list(self.topics),
            "markets": list(self.markets),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    articles_seen: int
    opportunities_emitted: int
    rejected_records: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "records_seen": self.records_seen,
            "articles_seen": self.articles_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryHealth:
    schema_version: str
    engine_id: str
    status: str
    ready: bool
    details: Mapping[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=_utc_now_iso)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "details", _freeze(dict(self.details or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "ready": self.ready,
            "details": dict(self.details),
            "checked_at": self.checked_at,
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: NewsIntelligenceFamily
    source_name: str
    supports_replay: bool = True
    deterministic: bool = True
    telemetry: bool = True
    read_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "supports_replay": self.supports_replay,
            "deterministic": self.deterministic,
            "telemetry": self.telemetry,
            "read_only": self.read_only,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class NewsIntelligenceDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: NewsIntelligenceDiscoveryTelemetry
    health: NewsIntelligenceDiscoveryHealth
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "opportunities", tuple(self.opportunities or ()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "status": self.status,
            "opportunities": [
                o.to_dict() if hasattr(o, "to_dict") else dict(o)
                for o in self.opportunities
            ],
            "telemetry": self.telemetry.to_dict(),
            "health": self.health.to_dict(),
            "read_only": self.read_only,
        }


class NewsIntelligenceDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> NewsIntelligenceDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> NewsIntelligenceDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: NewsIntelligenceDiscoveryRequest) -> NewsIntelligenceDiscoveryResult:
        raise NotImplementedError


class EmptyNewsIntelligenceDiscoveryEngine(NewsIntelligenceDiscoveryEngineContract):
    engine_id = "oracle.discovery.news_intelligence.empty"

    def capabilities(self) -> NewsIntelligenceDiscoveryCapability:
        return NewsIntelligenceDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> NewsIntelligenceDiscoveryHealth:
        return NewsIntelligenceDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: NewsIntelligenceDiscoveryRequest) -> NewsIntelligenceDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = NewsIntelligenceDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            articles_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return NewsIntelligenceDiscoveryResult(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            status="empty",
            opportunities=(),
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "CONTRACT_ID",
    "NewsIntelligenceFamily",
    "NewsIntelligenceDiscoveryRequest",
    "NewsIntelligenceDiscoveryTelemetry",
    "NewsIntelligenceDiscoveryHealth",
    "NewsIntelligenceDiscoveryCapability",
    "NewsIntelligenceDiscoveryResult",
    "NewsIntelligenceDiscoveryEngineContract",
    "EmptyNewsIntelligenceDiscoveryEngine",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.news_intelligence_discovery_model.news_intelligence_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    NewsIntelligenceFamily,
    NewsIntelligenceDiscoveryRequest,
    EmptyNewsIntelligenceDiscoveryEngine,
)


def test_nid_001_news_intelligence_discovery_contract():
    request = NewsIntelligenceDiscoveryRequest(
        request_id="news.intelligence.discovery.test.request",
        family=NewsIntelligenceFamily.MARKET_MOVING_NEWS,
        source_name="test_source",
        article_ids=("article_a", "article_b"),
        topics=("Fed", "inflation"),
        markets=("rates", "prediction_markets"),
        metadata={"records": [{"article_id": "article_a", "topic": "fed"}]},
    )

    engine = EmptyNewsIntelligenceDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "NID-001"
    assert CONTRACT_ID == "oracle.discovery.contract.news_intelligence"

    assert request.read_only is True
    assert request.article_ids == ("article_a", "article_b")
    assert request.topics == ("fed", "inflation")
    assert request.markets == ("RATES", "PREDICTION_MARKETS")
    assert request.family == NewsIntelligenceFamily.MARKET_MOVING_NEWS

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["order_allowed"] is False
    assert caps.metadata["position_sizing_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "NID-001"
    assert result.engine_id == "oracle.discovery.news_intelligence.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.articles_seen == 0
    assert result.telemetry.opportunities_emitted == 0

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "NID-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] NID-001 News Intelligence Discovery Contract")
    print({
        "schema_version": d["schema_version"],
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_nid_001_news_intelligence_discovery_contract()
'''

INIT_CODE = '''
try:
    from .news_intelligence_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        NewsIntelligenceFamily,
        NewsIntelligenceDiscoveryRequest,
        NewsIntelligenceDiscoveryTelemetry,
        NewsIntelligenceDiscoveryHealth,
        NewsIntelligenceDiscoveryCapability,
        NewsIntelligenceDiscoveryResult,
        NewsIntelligenceDiscoveryEngineContract,
        EmptyNewsIntelligenceDiscoveryEngine,
    )
except Exception:
    pass
'''

CONTRACT_FILE.write_text(CONTRACT_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
INIT_FILE.write_text(INIT_CODE, encoding="utf-8")

existing_oracle_init = ORACLE_INIT.read_text(encoding="utf-8") if ORACLE_INIT.exists() else ""
ORACLE_EXPORT = '''
try:
    from .news_intelligence_discovery_model.news_intelligence_discovery_contract import (
        NewsIntelligenceFamily,
        NewsIntelligenceDiscoveryRequest,
        NewsIntelligenceDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "NewsIntelligenceDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" NID-001 INSTALLER")
print(" News Intelligence Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] NID-001 installed")
print()
print("Run:")
print("py test_nid_001_news_intelligence_discovery_contract.py")