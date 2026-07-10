"""
CDM-006 Crypto Spot Discovery Pipeline Bridge

Read-only bridge from CDM-005 registry-ready crypto spot records into
pipeline-ready packets for the Opportunity Operating System lane.

No trading, swapping, sizing, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .crypto_spot_discovery_registry_bridge import (
    CryptoSpotDiscoveryRegistryBridge,
    CryptoSpotRegistryRecord,
)


SCHEMA_VERSION = "CDM-006"
BRIDGE_ID = "oracle.discovery.bridge.crypto_spot_pipeline"
BRIDGE_NAME = "Crypto Spot Discovery Pipeline Bridge"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class CryptoSpotPipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    symbol: str
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
            "symbol": self.symbol,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoSpotPipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[CryptoSpotPipelinePacket, ...]
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


class CryptoSpotDiscoveryPipelineBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    bridge_name = BRIDGE_NAME
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "bridge_name": self.bridge_name,
            "read_only": True,
            "accepts": "CDM-005 registry-ready crypto spot records",
            "emits": "pipeline-ready immutable crypto spot packets",
            "compatible_with": ["OOS-003 Opportunity Pipeline", "OOS-004 Validation"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
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

    def bridge_records(
        self,
        registry_records: Sequence[CryptoSpotRegistryRecord],
    ) -> CryptoSpotPipelineBridgeReport:
        started_at = _utc_now_iso()
        records = tuple(registry_records or ())

        packets = tuple(
            sorted(
                (self._packet_from_record(record) for record in records),
                key=lambda p: (p.registry_key, p.packet_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "records_seen": len(records),
                "packets_emitted": len(packets),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
            }
        )

        return CryptoSpotPipelineBridgeReport(
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
        source_name: str = "crypto_spot_pipeline_bridge_source",
        min_edge_percent: float = 0.01,
        min_liquidity: float = 1000.0,
    ) -> CryptoSpotPipelineBridgeReport:
        registry_bridge = CryptoSpotDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_records,
            source_name=source_name,
            min_edge_percent=min_edge_percent,
            min_liquidity=min_liquidity,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(self, record: CryptoSpotRegistryRecord) -> CryptoSpotPipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType(
            {
                "opportunity_id": record.opportunity_id,
                "symbol": record.symbol,
                "opportunity_type": record.opportunity_type,
                "source_engine_id": record.source_engine_id,
                "registry_key": record.registry_key,
                "registry_payload": _freeze(record.payload),
                "validation_required": True,
                "ranking_required": True,
                "registry_required": True,
                "execution_allowed": False,
                "swap_allowed": False,
                "order_allowed": False,
                "read_only": True,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "source_registry_schema_version": record.schema_version,
                "source_registry_bridge_id": record.bridge_id,
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "handoff_target": "OOS Opportunity Pipeline",
            }
        )

        return CryptoSpotPipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            symbol=record.symbol,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "CryptoSpotPipelinePacket",
    "CryptoSpotPipelineBridgeReport",
    "CryptoSpotDiscoveryPipelineBridge",
]
