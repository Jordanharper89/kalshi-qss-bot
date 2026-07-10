from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "social_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FILE = MODULE_DIR / "social_intelligence_discovery_engine.py"
TEST_FILE = ROOT / "test_sid_003_social_intelligence_discovery_engine.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ENGINE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .social_intelligence_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    SocialIntelligenceDiscoveryCapability,
    SocialIntelligenceDiscoveryEngineContract,
    SocialIntelligenceFamily,
    SocialIntelligenceDiscoveryHealth,
    SocialIntelligenceDiscoveryRequest,
    SocialIntelligenceDiscoveryResult,
    SocialIntelligenceDiscoveryTelemetry,
)
from .social_intelligence_source_adapter import SocialSignalSnapshot, SocialIntelligenceSourceAdapter

SCHEMA_VERSION = "SID-003"
ENGINE_ID = "oracle.discovery.social_intelligence"


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
class SocialIntelligenceOpportunity:
    opportunity_id: str
    schema_version: str
    post_id: str
    topic: str
    platform: str
    opportunity_type: str
    source_engine_id: str
    social_score: float
    engagement_score: float
    velocity_score: float
    credibility_score: float
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
            "post_id": self.post_id,
            "topic": self.topic,
            "platform": self.platform,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "social_score": self.social_score,
            "engagement_score": self.engagement_score,
            "velocity_score": self.velocity_score,
            "credibility_score": self.credibility_score,
            "market_scope_score": self.market_scope_score,
            "confidence": self.confidence,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class SocialIntelligenceDiscoveryEngine(SocialIntelligenceDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[SocialSignalSnapshot]] = None,
        min_social_score: float = 0.55,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_social_score = float(min_social_score)

    def capabilities(self) -> SocialIntelligenceDiscoveryCapability:
        return SocialIntelligenceDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name="social_signal_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "produces": "UniversalOpportunity-shaped social intelligence opportunities",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
                "posting_allowed": False,
                "dm_allowed": False,
            },
        )

    def health(self) -> SocialIntelligenceDiscoveryHealth:
        return SocialIntelligenceDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"engine_schema_version": self.schema_version, "read_only": True},
        )

    def discover(self, request: SocialIntelligenceDiscoveryRequest | None = None) -> SocialIntelligenceDiscoveryResult:
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

        opportunities = tuple(sorted(opportunities, key=lambda o: (-o.social_score, -o.confidence, o.post_id)))
        request_id = request.request_id if request is not None else "social.intelligence.discovery.default"

        telemetry = SocialIntelligenceDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            posts_seen=len({s.post_id for s in snapshots}),
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_social_score": self.min_social_score,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
                "posting_allowed": False,
                "dm_allowed": False,
            },
            read_only=True,
        )

        return SocialIntelligenceDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(self, request: SocialIntelligenceDiscoveryRequest | None) -> Tuple[SocialSignalSnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "social_snapshots", "posts", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(r, SocialSignalSnapshot) for r in record_tuple):
            return record_tuple

        adapter = SocialIntelligenceSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _market_scope_score(self, snapshot: SocialSignalSnapshot) -> float:
        markets = set(snapshot.affected_markets)
        score = 0.10
        if "PREDICTION_MARKETS" in markets:
            score += 0.35
        if "RATES" in markets:
            score += 0.20
        if "CRYPTO" in markets:
            score += 0.15
        if "SPORTS" in markets:
            score += 0.10
        if snapshot.entities:
            score += 0.10
        return round(min(1.0, score), 6)

    def _to_universal_market(self, snapshot: SocialSignalSnapshot) -> Mapping[str, Any]:
        return _freeze({
            "schema_family": "UMM",
            "market_type": "social_intelligence",
            "post_id": snapshot.post_id,
            "platform": snapshot.platform,
            "author": snapshot.author,
            "topic": snapshot.topic,
            "sentiment": snapshot.sentiment,
            "posted_at": snapshot.posted_at,
            "affected_markets": snapshot.affected_markets,
            "entities": snapshot.entities,
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

    def _build_opportunity(self, snapshot: SocialSignalSnapshot) -> Optional[SocialIntelligenceOpportunity]:
        if not snapshot.post_id or not snapshot.text:
            return None

        market_scope_score = self._market_scope_score(snapshot)
        social_score = round(
            snapshot.engagement_score * 0.30
            + snapshot.velocity_score * 0.30
            + snapshot.credibility_score * 0.25
            + market_scope_score * 0.15,
            6,
        )

        if social_score < self.min_social_score:
            return None

        confidence = round(min(1.0, social_score * 0.70 + snapshot.credibility_score * 0.30), 6)

        identity = {
            "post_id": snapshot.post_id,
            "platform": snapshot.platform,
            "topic": snapshot.topic,
            "posted_at": snapshot.posted_at,
            "social_score": social_score,
        }

        explanation = MappingProxyType({
            "summary": "Social signal passed read-only engagement, velocity, credibility, and market-scope scoring.",
            "post_id": snapshot.post_id,
            "topic": snapshot.topic,
            "engagement_score": snapshot.engagement_score,
            "velocity_score": snapshot.velocity_score,
            "credibility_score": snapshot.credibility_score,
            "market_scope_score": market_scope_score,
            "social_score": social_score,
            "rules": [
                "read_only_scan",
                "engagement_score_guardrail",
                "velocity_score_guardrail",
                "credibility_score_guardrail",
                "market_scope_guardrail",
                "deterministic_opportunity_id",
                "no_execution_authority",
                "no_posting_authority",
            ],
        })

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "source_engine_id": self.engine_id,
            "post_id": snapshot.post_id,
            "created_at": _utc_now_iso(),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligenceOpportunity(
            opportunity_id=_stable_id("uop.social_intelligence", identity),
            schema_version="UOM-compatible/SID-003",
            post_id=snapshot.post_id,
            topic=snapshot.topic,
            platform=snapshot.platform,
            opportunity_type="social_intelligence_signal",
            source_engine_id=self.engine_id,
            social_score=social_score,
            engagement_score=snapshot.engagement_score,
            velocity_score=snapshot.velocity_score,
            credibility_score=snapshot.credibility_score,
            market_scope_score=market_scope_score,
            confidence=confidence,
            universal_market=self._to_universal_market(snapshot),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = ["SCHEMA_VERSION", "ENGINE_ID", "SocialIntelligenceOpportunity", "SocialIntelligenceDiscoveryEngine"]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_contract import (
    SocialIntelligenceDiscoveryRequest,
    SocialIntelligenceFamily,
)
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_engine import (
    SocialIntelligenceDiscoveryEngine,
)


def test_sid_003_social_intelligence_discovery_engine():
    raw = [
        {
            "post_id": "post_b",
            "platform": "X",
            "author": "macro_trader",
            "topic": "fed",
            "text": "Rate cut odds are collapsing after CPI reaction.",
            "posted_at": "2026-01-15T14:05:00Z",
            "sentiment": "bearish",
            "engagement_score": 0.88,
            "velocity_score": 0.82,
            "credibility_score": 0.80,
            "markets": "RATES, PREDICTION_MARKETS",
            "symbols": "FED, CPI",
        },
        {
            "id": "post_a",
            "network": "reddit",
            "username": "kalshi_watcher",
            "category": "prediction_market_social",
            "content": "Inflation markets are moving fast after the CPI headline.",
            "time": "2026-01-15T13:35:00Z",
            "sentiment": "bullish",
            "engagement": 0.91,
            "velocity": 0.87,
            "credibility": 0.76,
            "affected_markets": ["PREDICTION_MARKETS", "RATES"],
            "entities": ["CPI", "KALSHI"],
        },
        {
            "post_id": "post_minor",
            "platform": "x",
            "author": "small_account",
            "topic": "local",
            "text": "Random local market comment.",
            "posted_at": "2026-01-15T12:00:00Z",
            "sentiment": "neutral",
            "engagement_score": 0.10,
            "velocity_score": 0.10,
            "credibility_score": 0.20,
            "affected_markets": ["LOCAL"],
        },
    ]

    request = SocialIntelligenceDiscoveryRequest(
        request_id="sid003.test.request",
        family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
        source_name="sid_003_test_feed",
        metadata={"raw_records": raw},
    )

    engine = SocialIntelligenceDiscoveryEngine(min_social_score=0.55)
    caps = engine.capabilities()
    health = engine.health()
    report_a = engine.discover(request)
    report_b = engine.discover(request)

    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["posting_allowed"] is False
    assert caps.metadata["dm_allowed"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_a.schema_version == "SID-001"
    assert report_a.engine_id == "oracle.discovery.social_intelligence"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.opportunities) == 2
    assert [o.opportunity_id for o in report_a.opportunities] == [o.opportunity_id for o in report_b.opportunities]

    first = report_a.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "social_intelligence_signal"
    assert first.source_engine_id == "oracle.discovery.social_intelligence"
    assert first.social_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.universal_market["market_type"] == "social_intelligence"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["order_allowed"] is False
    assert first.universal_market["position_sizing_allowed"] is False
    assert first.universal_market["posting_allowed"] is False
    assert first.universal_market["dm_allowed"] is False

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["posts_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] SID-003 Social Intelligence Discovery Engine")
    print({
        "schema_version": "SID-003",
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_003_social_intelligence_discovery_engine()
'''

INIT_EXPORT = '''
try:
    from .social_intelligence_discovery_engine import (
        SocialIntelligenceDiscoveryEngine,
        SocialIntelligenceOpportunity,
    )
except Exception:
    pass
'''

ENGINE_FILE.write_text(ENGINE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SocialIntelligenceDiscoveryEngine" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SID-003 INSTALLER")
print(" Social Intelligence Discovery Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SID-003 installed")
print()
print("Run:")
print("py test_sid_003_social_intelligence_discovery_engine.py")