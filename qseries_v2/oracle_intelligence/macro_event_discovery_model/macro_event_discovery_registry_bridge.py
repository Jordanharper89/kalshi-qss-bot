
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .macro_event_discovery_contract import MacroEventDiscoveryFamily, MacroEventDiscoveryRequest
from .macro_event_discovery_engine import MacroEventDiscoveryEngine

SCHEMA_VERSION = "MED-005"
BRIDGE_ID = "oracle.discovery.bridge.macro_event_registry"


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
class MacroEventRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    event_id: str
    title: str
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
            "event_id": self.event_id,
            "title": self.title,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[MacroEventRegistryRecord, ...]
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


class MacroEventDiscoveryRegistryBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "read_only": True,
            "accepts": "MED-003 MacroEventDiscoveryResult",
            "emits": "registry-ready immutable macro event records",
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> MacroEventRegistryBridgeReport:
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
        })

        return MacroEventRegistryBridgeReport(
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
        source_name: str = "macro_event_registry_bridge_source",
        min_event_score: float = 0.55,
    ) -> MacroEventRegistryBridgeReport:
        request = MacroEventDiscoveryRequest(
            request_id="med005.macro.event.registry.bridge",
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )
        report = MacroEventDiscoveryEngine(min_event_score=min_event_score).discover(request)
        return self.bridge_report(report)

    def _record_from_opportunity(self, o: Any) -> MacroEventRegistryRecord:
        opportunity_id = str(getattr(o, "opportunity_id"))
        event_id = str(getattr(o, "event_id"))
        title = str(getattr(o, "title"))
        opportunity_type = str(getattr(o, "opportunity_type"))
        source_engine_id = str(getattr(o, "source_engine_id"))
        registry_key = f"{source_engine_id}:{opportunity_type}:{event_id}:{opportunity_id}"

        payload = MappingProxyType({
            "opportunity_id": opportunity_id,
            "event_id": event_id,
            "title": title,
            "family": getattr(o, "family", None),
            "region": getattr(o, "region", None),
            "currency": getattr(o, "currency", None),
            "opportunity_type": opportunity_type,
            "source_engine_id": source_engine_id,
            "event_score": getattr(o, "event_score", None),
            "impact_score": getattr(o, "impact_score", None),
            "market_relevance_score": getattr(o, "market_relevance_score", None),
            "surprise_potential_score": getattr(o, "surprise_potential_score", None),
            "confidence": getattr(o, "confidence", None),
            "status": getattr(o, "status", None),
            "universal_market": _freeze(getattr(o, "universal_market", {})),
            "explanation": _freeze(getattr(o, "explanation", {})),
            "telemetry": _freeze(getattr(o, "telemetry", {})),
            "read_only": True,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        audit = MappingProxyType({
            "bridge_schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "registered_from": "MED macro event discovery",
            "created_at": _utc_now_iso(),
            "oracle_read_only": True,
            "execution_fields_present": False,
            "execution_allowed": False,
            "order_allowed": False,
            "position_sizing_allowed": False,
        })

        return MacroEventRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            event_id=event_id,
            title=title,
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
    "MacroEventRegistryRecord",
    "MacroEventRegistryBridgeReport",
    "MacroEventDiscoveryRegistryBridge",
]
