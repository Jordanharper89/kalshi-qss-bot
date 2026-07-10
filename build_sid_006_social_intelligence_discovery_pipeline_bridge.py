from pathlib import Path

ROOT = Path.cwd()
MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "social_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "social_intelligence_discovery_pipeline_bridge.py"
TEST_FILE = ROOT / "test_sid_006_social_intelligence_discovery_pipeline_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .social_intelligence_discovery_registry_bridge import (
    SocialIntelligenceDiscoveryRegistryBridge,
    SocialIntelligenceRegistryRecord,
)

SCHEMA_VERSION = "SID-006"
BRIDGE_ID = "oracle.discovery.bridge.social_intelligence_pipeline"


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
class SocialIntelligencePipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    post_id: str
    topic: str
    platform: str
    pipeline_status: str
    payload: Mapping[str, Any]
    audit: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "packet_id": self.packet_id,
            "registry_key": self.registry_key,
            "opportunity_id": self.opportunity_id,
            "post_id": self.post_id,
            "topic": self.topic,
            "platform": self.platform,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligencePipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[SocialIntelligencePipelinePacket, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": self.status,
            "packets": [p.to_dict() for p in self.packets],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class SocialIntelligenceDiscoveryPipelineBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "SID-005 registry-ready social intelligence records",
            "emits": "pipeline-ready immutable social intelligence packets",
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

    def bridge_records(self, registry_records: Sequence[SocialIntelligenceRegistryRecord]) -> SocialIntelligencePipelineBridgeReport:
        started_at = _utc_now_iso()
        records = tuple(registry_records or ())
        packets = tuple(sorted((self._packet_from_record(r) for r in records), key=lambda p: p.packet_id))

        telemetry = MappingProxyType({
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "records_seen": len(records),
            "packets_emitted": len(packets),
            "read_only": True,
            "deterministic_sort": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
        })

        return SocialIntelligencePipelineBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if packets else "empty",
            packets=packets,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_registry_and_bridge(
        self,
        raw_records: Sequence[Any],
        source_name: str = "social_intelligence_pipeline_bridge_source",
        min_social_score: float = 0.55,
    ) -> SocialIntelligencePipelineBridgeReport:
        registry_bridge = SocialIntelligenceDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_records,
            source_name=source_name,
            min_social_score=min_social_score,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(self, record: SocialIntelligenceRegistryRecord) -> SocialIntelligencePipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType({
            "opportunity_id": record.opportunity_id,
            "post_id": record.post_id,
            "topic": record.topic,
            "platform": record.platform,
            "opportunity_type": record.opportunity_type,
            "source_engine_id": record.source_engine_id,
            "registry_key": record.registry_key,
            "registry_payload": _freeze(record.payload),
            "validation_required": True,
            "ranking_required": True,
            "registry_required": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
            "read_only": True,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "source_registry_schema_version": record.schema_version,
            "source_registry_bridge_id": record.bridge_id,
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "social_action_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
            "posting_allowed": False,
            "dm_allowed": False,
            "handoff_target": "OOS Opportunity Pipeline",
        })

        return SocialIntelligencePipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            post_id=record.post_id,
            topic=record.topic,
            platform=record.platform,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "SocialIntelligencePipelinePacket",
    "SocialIntelligencePipelineBridgeReport",
    "SocialIntelligenceDiscoveryPipelineBridge",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_discovery_pipeline_bridge import (
    SocialIntelligenceDiscoveryPipelineBridge,
)


def test_sid_006_social_intelligence_discovery_pipeline_bridge():
    raw = [
        {"post_id": "post_b", "platform": "X", "author": "macro_trader", "topic": "fed", "text": "Rate cut odds are collapsing after CPI reaction.", "posted_at": "2026-01-15T14:05:00Z", "sentiment": "bearish", "engagement_score": 0.88, "velocity_score": 0.82, "credibility_score": 0.80, "markets": "RATES, PREDICTION_MARKETS", "symbols": "FED, CPI"},
        {"id": "post_a", "network": "reddit", "username": "kalshi_watcher", "category": "prediction_market_social", "content": "Inflation markets are moving fast after the CPI headline.", "time": "2026-01-15T13:35:00Z", "sentiment": "bullish", "engagement": 0.91, "velocity": 0.87, "credibility": 0.76, "affected_markets": ["PREDICTION_MARKETS", "RATES"], "entities": ["CPI", "KALSHI"]},
        {"post_id": "post_minor", "platform": "x", "author": "small_account", "topic": "local", "text": "Random local market comment.", "posted_at": "2026-01-15T12:00:00Z", "sentiment": "neutral", "engagement_score": 0.10, "velocity_score": 0.10, "credibility_score": 0.20, "affected_markets": ["LOCAL"]},
    ]

    bridge = SocialIntelligenceDiscoveryPipelineBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_registry_and_bridge(raw, source_name="sid_006_test_source", min_social_score=0.55)
    report_b = bridge.discover_registry_and_bridge(list(reversed(raw)), source_name="sid_006_test_source", min_social_score=0.55)

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "SID-006"
    assert report_a.bridge_id == "oracle.discovery.bridge.social_intelligence_pipeline"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.packets) == 2

    assert [p.packet_id for p in report_a.packets] == [p.packet_id for p in report_b.packets]

    first = report_a.packets[0]
    assert first.read_only is True
    assert first.pipeline_status == "pipeline_ready"
    assert first.payload["read_only"] is True
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["order_allowed"] is False
    assert first.payload["position_sizing_allowed"] is False
    assert first.payload["posting_allowed"] is False
    assert first.payload["dm_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["social_action_fields_present"] is False
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"
    assert first.payload["registry_payload"]["universal_market"]["market_type"] == "social_intelligence"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("pipeline payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "SID-006"
    assert d["telemetry"]["records_seen"] == 2
    assert d["telemetry"]["packets_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["posting_allowed"] is False
    assert d["telemetry"]["dm_allowed"] is False

    print("[PASS] SID-006 Social Intelligence Discovery Pipeline Bridge")
    print({
        "schema_version": d["schema_version"],
        "bridge_id": d["bridge_id"],
        "status": d["status"],
        "packets": len(d["packets"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_006_social_intelligence_discovery_pipeline_bridge()
'''

INIT_EXPORT = '''
try:
    from .social_intelligence_discovery_pipeline_bridge import (
        SocialIntelligenceDiscoveryPipelineBridge,
        SocialIntelligencePipelineBridgeReport,
        SocialIntelligencePipelinePacket,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SocialIntelligenceDiscoveryPipelineBridge" not in existing:
    INIT_FILE.write_text(existing.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SID-006 INSTALLER")
print(" Social Intelligence Discovery Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SID-006 installed")
print()
print("Run:")
print("py test_sid_006_social_intelligence_discovery_pipeline_bridge.py")