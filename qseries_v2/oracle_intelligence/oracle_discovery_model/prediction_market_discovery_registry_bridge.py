"""
ODM-005 Prediction Market Discovery Registry Bridge

Read-only bridge between ODM prediction-market discovery output and the
Opportunity Operating System registry lane.

This bridge does NOT execute trades. It only prepares immutable registry-ready
records from discovered opportunities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .prediction_market_source_adapter import PredictionMarketSourceAdapter


SCHEMA_VERSION = "ODM-005"
BRIDGE_ID = "oracle.discovery.bridge.prediction_market_registry"
BRIDGE_NAME = "Prediction Market Discovery Registry Bridge"


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
class PredictionMarketRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    market_id: str
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
            "market_id": self.market_id,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class PredictionMarketRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[PredictionMarketRegistryRecord, ...]
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


class PredictionMarketDiscoveryRegistryBridge:
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
            "accepts": "ODM-002 PredictionMarketDiscoveryReport",
            "emits": "registry-ready immutable records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
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

    def bridge_report(self, discovery_report: Any) -> PredictionMarketRegistryBridgeReport:
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
            }
        )

        return PredictionMarketRegistryBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if records else "empty",
            records=records,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_and_bridge(
        self,
        raw_markets: Sequence[Any],
        source_name: str = "prediction_market_registry_bridge_source",
        min_edge: float = 0.02,
        min_liquidity: float = 100.0,
    ) -> PredictionMarketRegistryBridgeReport:
        adapter = PredictionMarketSourceAdapter(source_name=source_name)
        discovery_report = adapter.discover(
            raw_markets,
            min_edge=min_edge,
            min_liquidity=min_liquidity,
        )
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> PredictionMarketRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        market_id = str(getattr(opportunity, "market_id"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))

        registry_key = f"{source_engine_id}:{opportunity_type}:{market_id}:{opportunity_id}"

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "market_id": market_id,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "side": getattr(opportunity, "side", None),
                "edge": getattr(opportunity, "edge", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity": getattr(opportunity, "liquidity", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "ODM prediction market discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
            }
        )

        return PredictionMarketRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            market_id=market_id,
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
    "PredictionMarketRegistryRecord",
    "PredictionMarketRegistryBridgeReport",
    "PredictionMarketDiscoveryRegistryBridge",
]
