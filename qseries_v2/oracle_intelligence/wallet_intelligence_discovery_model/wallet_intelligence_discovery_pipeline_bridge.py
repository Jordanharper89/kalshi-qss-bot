"""
WDM-006 Wallet Intelligence Discovery Pipeline Bridge

Read-only bridge from WDM-005 registry-ready wallet intelligence records into
pipeline-ready packets for the Opportunity Operating System lane.

No signing, fund movement, swaps, trading, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .wallet_intelligence_discovery_registry_bridge import (
    WalletIntelligenceDiscoveryRegistryBridge,
    WalletIntelligenceRegistryRecord,
)


SCHEMA_VERSION = "WDM-006"
BRIDGE_ID = "oracle.discovery.bridge.wallet_intelligence_pipeline"
BRIDGE_NAME = "Wallet Intelligence Discovery Pipeline Bridge"


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
class WalletIntelligencePipelinePacket:
    schema_version: str
    bridge_id: str
    packet_id: str
    registry_key: str
    opportunity_id: str
    wallet: str
    chain: str
    symbol: str
    signal_type: str
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
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "pipeline_status": self.pipeline_status,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligencePipelineBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    packets: Tuple[WalletIntelligencePipelinePacket, ...]
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


class WalletIntelligenceDiscoveryPipelineBridge:
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
            "accepts": "WDM-005 registry-ready wallet intelligence records",
            "emits": "pipeline-ready immutable wallet intelligence packets",
            "compatible_with": ["OOS-003 Opportunity Pipeline", "OOS-004 Validation"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
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
        registry_records: Sequence[WalletIntelligenceRegistryRecord],
    ) -> WalletIntelligencePipelineBridgeReport:
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
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return WalletIntelligencePipelineBridgeReport(
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
        source_name: str = "wallet_intelligence_pipeline_bridge_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> WalletIntelligencePipelineBridgeReport:
        registry_bridge = WalletIntelligenceDiscoveryRegistryBridge()
        registry_report = registry_bridge.discover_and_bridge(
            raw_records,
            source_name=source_name,
            min_wallet_score=min_wallet_score,
            min_usd_value=min_usd_value,
            min_signal_score=min_signal_score,
        )
        return self.bridge_records(registry_report.records)

    def _packet_from_record(
        self,
        record: WalletIntelligenceRegistryRecord,
    ) -> WalletIntelligencePipelinePacket:
        packet_id = f"pipeline.packet:{record.registry_key}"

        payload = MappingProxyType(
            {
                "opportunity_id": record.opportunity_id,
                "wallet": record.wallet,
                "chain": record.chain,
                "symbol": record.symbol,
                "opportunity_type": record.opportunity_type,
                "source_engine_id": record.source_engine_id,
                "signal_type": record.signal_type,
                "registry_key": record.registry_key,
                "registry_payload": _freeze(record.payload),
                "validation_required": True,
                "ranking_required": True,
                "registry_required": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
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
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "handoff_target": "OOS Opportunity Pipeline",
            }
        )

        return WalletIntelligencePipelinePacket(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            packet_id=packet_id,
            registry_key=record.registry_key,
            opportunity_id=record.opportunity_id,
            wallet=record.wallet,
            chain=record.chain,
            symbol=record.symbol,
            signal_type=record.signal_type,
            pipeline_status="pipeline_ready",
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "WalletIntelligencePipelinePacket",
    "WalletIntelligencePipelineBridgeReport",
    "WalletIntelligenceDiscoveryPipelineBridge",
]
