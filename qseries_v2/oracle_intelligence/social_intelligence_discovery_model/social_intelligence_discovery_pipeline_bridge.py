
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
