"""
WDM-005 Wallet Intelligence Discovery Registry Bridge

Read-only bridge from WDM-003 wallet intelligence discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No signing, fund movement, swaps, trading, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .wallet_intelligence_discovery_contract import (
    WalletIntelligenceDiscoveryRequest,
    WalletIntelligenceFamily,
)
from .wallet_intelligence_discovery_engine import WalletIntelligenceDiscoveryEngine


SCHEMA_VERSION = "WDM-005"
BRIDGE_ID = "oracle.discovery.bridge.wallet_intelligence_registry"
BRIDGE_NAME = "Wallet Intelligence Discovery Registry Bridge"


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
class WalletIntelligenceRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    wallet: str
    chain: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    signal_type: str
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
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "signal_type": self.signal_type,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[WalletIntelligenceRegistryRecord, ...]
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


class WalletIntelligenceDiscoveryRegistryBridge:
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
            "accepts": "WDM-003 WalletIntelligenceDiscoveryResult",
            "emits": "registry-ready immutable wallet intelligence records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
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

    def bridge_report(self, discovery_report: Any) -> WalletIntelligenceRegistryBridgeReport:
        started_at = _utc_now_iso()
        opportunities = tuple(getattr(discovery_report, "opportunities", ()) or ())

        records = tuple(
            sorted(
                (self._record_from_opportunity(o) for o in opportunities),
                key=lambda r: (r.registry_key, r.opportunity_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "opportunities_seen": len(opportunities),
                "records_emitted": len(records),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return WalletIntelligenceRegistryBridgeReport(
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
        source_name: str = "wallet_intelligence_registry_bridge_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> WalletIntelligenceRegistryBridgeReport:
        request = WalletIntelligenceDiscoveryRequest(
            request_id="wdm005.wallet.intelligence.registry.bridge",
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = WalletIntelligenceDiscoveryEngine(
            min_wallet_score=min_wallet_score,
            min_usd_value=min_usd_value,
            min_signal_score=min_signal_score,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> WalletIntelligenceRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        wallet = str(getattr(opportunity, "wallet"))
        chain = str(getattr(opportunity, "chain"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))
        signal_type = str(getattr(opportunity, "signal_type"))

        registry_key = (
            f"{source_engine_id}:{opportunity_type}:{chain}:"
            f"{wallet}:{symbol}:{signal_type}:{opportunity_id}"
        )

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "wallet": wallet,
                "chain": chain,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "signal_type": signal_type,
                "signal_score": getattr(opportunity, "signal_score", None),
                "confidence": getattr(opportunity, "confidence", None),
                "usd_value": getattr(opportunity, "usd_value", None),
                "wallet_score": getattr(opportunity, "wallet_score", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "WDM wallet intelligence discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return WalletIntelligenceRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            wallet=wallet,
            chain=chain,
            symbol=symbol,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
            signal_type=signal_type,
            registry_status="registry_ready",
            registry_key=registry_key,
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "WalletIntelligenceRegistryRecord",
    "WalletIntelligenceRegistryBridgeReport",
    "WalletIntelligenceDiscoveryRegistryBridge",
]
