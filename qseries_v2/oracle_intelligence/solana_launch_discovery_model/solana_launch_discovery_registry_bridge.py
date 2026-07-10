"""
SLD-005 Solana Launch Discovery Registry Bridge

Read-only bridge from SLD-003 Solana launch discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No signing, fund movement, swaps, sniping, routing, buying, selling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_contract import (
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from .solana_launch_discovery_engine import SolanaLaunchDiscoveryEngine


SCHEMA_VERSION = "SLD-005"
BRIDGE_ID = "oracle.discovery.bridge.solana_launch_registry"
BRIDGE_NAME = "Solana Launch Discovery Registry Bridge"


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
class SolanaLaunchRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    mint: str
    symbol: str
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
            "mint": self.mint,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[SolanaLaunchRegistryRecord, ...]
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


class SolanaLaunchDiscoveryRegistryBridge:
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
            "accepts": "SLD-003 SolanaLaunchDiscoveryResult",
            "emits": "registry-ready immutable Solana launch records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> SolanaLaunchRegistryBridgeReport:
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
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchRegistryBridgeReport(
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
        source_name: str = "solana_launch_registry_bridge_source",
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> SolanaLaunchRegistryBridgeReport:
        request = SolanaLaunchDiscoveryRequest(
            request_id="sld005.solana.launch.registry.bridge",
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = SolanaLaunchDiscoveryEngine(
            min_liquidity_usd=min_liquidity_usd,
            max_age_seconds=max_age_seconds,
            min_launch_score=min_launch_score,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> SolanaLaunchRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        mint = str(getattr(opportunity, "mint"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))

        registry_key = f"{source_engine_id}:{opportunity_type}:{symbol}:{mint}:{opportunity_id}"

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "mint": mint,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "launch_score": getattr(opportunity, "launch_score", None),
                "safety_score": getattr(opportunity, "safety_score", None),
                "liquidity_score": getattr(opportunity, "liquidity_score", None),
                "momentum_score": getattr(opportunity, "momentum_score", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity_usd": getattr(opportunity, "liquidity_usd", None),
                "age_seconds": getattr(opportunity, "age_seconds", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "SLD Solana launch discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            mint=mint,
            symbol=symbol,
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
    "BRIDGE_NAME",
    "SolanaLaunchRegistryRecord",
    "SolanaLaunchRegistryBridgeReport",
    "SolanaLaunchDiscoveryRegistryBridge",
]
