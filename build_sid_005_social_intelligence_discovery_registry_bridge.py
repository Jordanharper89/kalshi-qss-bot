from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "social_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "social_intelligence_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_sid_005_social_intelligence_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_contract import SocialIntelligenceDiscoveryRequest, SocialIntelligenceFamily
from .social_intelligence_discovery_engine import SocialIntelligenceDiscoveryEngine

SCHEMA_VERSION = "SID-005"
BRIDGE_ID = "oracle.discovery.bridge.social_intelligence_registry"


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
class SocialIntelligenceRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    post_id: str
    topic: str
    platform: str
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
            "post_id": self.post_id,
            "topic": self.topic,
            "platform": self.platform,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligenceRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[SocialIntelligenceRegistryRecord, ...]
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


class SocialIntelligenceDiscoveryRegistryBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "SID-003 SocialIntelligenceDiscoveryResult",
            "emits": "registry-ready immutable social intelligence records",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> SocialIntelligenceRegistryBridgeReport:
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
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligenceRegistryBridgeReport(
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
        source_name: str = "social_intelligence_registry_bridge_source",
        min_social_score: float = 0.55,
    ) -> SocialIntelligenceRegistryBridgeReport:
        request = SocialIntelligenceDiscoveryRequest(
            request_id="sid005.social.intelligence.registry.bridge",
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )
        report = SocialIntelligenceDiscoveryEngine(min_social_score=min_social_score).discover(request)
        return self.bridge_report(report)

    def _record_from_opportunity(self, o: Any) -> SocialIntelligenceRegistryRecord:
        opportunity_id = str(getattr(o, "opportunity_id"))
        post_id = str(getattr(o, "post_id"))
        topic = str(getattr(o, "topic"))
        platform = str(getattr(o, "platform"))
        opportunity_type = str(getattr(o, "opportunity_type"))
        source_engine_id = str(getattr(o, "source_engine_id"))
        registry_key = f"{source_engine_id}:{opportunity_type}:{platform}:{post_id}:{opportunity_id}"

        payload = MappingProxyType({
            "opportunity_id": opportunity_id,
            "post_id": post_id,
            "topic": topic,
            "platform": platform,
            "opportunity_type": opportunity_type,
            "source_engine_id": source_engine_id,
            "social_score": getattr(o, "social_score", None),
            "engagement_score": getattr(o, "engagement_score", None),
            "velocity_score": getattr(o, "velocity_score", None),
            "credibility_score": getattr(o, "credibility_score", None),
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
            "posting_allowed": False,
            "dm_allowed": False,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "registered_from": "SID social intelligence discovery",
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "social_action_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligenceRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            post_id=post_id,
            topic=topic,
            platform=platform,
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
    "SocialIntelligenceRegistryRecord",
    "SocialIntelligenceRegistryBridgeReport",
    "SocialIntelligenceDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_registry_bridge import (
    SocialIntelligenceDiscoveryRegistryBridge,
)


def test_sid_005_social_intelligence_discovery_registry_bridge():
    raw = [
        {"post_id": "post_b", "platform": "X", "author": "macro_trader", "topic": "fed", "text": "Rate cut odds are collapsing after CPI reaction.", "posted_at": "2026-01-15T14:05:00Z", "sentiment": "bearish", "engagement_score": 0.88, "velocity_score": 0.82, "credibility_score": 0.80, "markets": "RATES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "post_a", "network": "reddit", "username": "kalshi_watcher", "category": "prediction_market_social", "content": "Inflation markets are moving fast after the CPI headline.", "time": "2026-01-15T13:35:00Z", "sentiment": "bullish", "engagement": 0.91, "velocity": 0.87, "credibility": 0.76, "affected_markets": ["PREDICTION_MARKETS", "RATES"], "entities": ["CPI", "KALSHI"]},
        {"post_id": "post_minor", "platform": "x", "author": "small_account", "topic": "local", "text": "Random local market comment.", "posted_at": "2026-01-15T12:00:00Z", "sentiment": "neutral", "engagement_score": 0.10, "velocity_score": 0.10, "credibility_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    bridge = SocialIntelligenceDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()
    report_a = bridge.discover_and_bridge(raw, source_name="sid_005_test_source", min_social_score=0.55)
    report_b = bridge.discover_and_bridge(list(reversed(raw)), source_name="sid_005_test_source", min_social_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "SID-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.social_intelligence_registry"
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
    assert first.payload["posting_allowed"] is False
    assert first.payload["dm_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["social_action_fields_present"] is False
    assert first.payload["universal_market"]["market_type"] == "social_intelligence"

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
    assert d["telemetry"]["posting_allowed"] is False

    print("[PASS] SID-005 Social Intelligence Discovery Registry Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "records": len(d["records"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_005_social_intelligence_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .social_intelligence_discovery_registry_bridge import (
        SocialIntelligenceDiscoveryRegistryBridge,
        SocialIntelligenceRegistryBridgeReport,
        SocialIntelligenceRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SocialIntelligenceDiscoveryRegistryBridge" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SID-005 INSTALLER")
print(" Social Intelligence Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SID-005 installed")
print()
print("Run:")
print("py test_sid_005_social_intelligence_discovery_registry_bridge.py")