"""
MED-001 Macro Event Discovery Contract

Canonical read-only contract for Oracle Macro Event Discovery.

Oracle discovers, normalizes, explains, and ranks macro event intelligence.
Oracle does not execute trades, size positions, route orders, or manage exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "MED-001"
CONTRACT_ID = "oracle.discovery.contract.macro_event"


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


class MacroEventDiscoveryFamily(str, Enum):
    ECONOMIC_RELEASE = "economic_release"
    FED_EVENT = "fed_event"
    INFLATION_EVENT = "inflation_event"
    JOBS_EVENT = "jobs_event"
    GEOPOLITICAL_EVENT = "geopolitical_event"
    ELECTION_EVENT = "election_event"
    WEATHER_EVENT = "weather_event"
    NEWS_SHOCK = "news_shock"
    CROSS_MARKET_EVENT = "cross_market_event"


@dataclass(frozen=True)
class MacroEventDiscoveryRequest:
    request_id: str
    family: MacroEventDiscoveryFamily
    source_name: str
    event_ids: Tuple[str, ...] = field(default_factory=tuple)
    regions: Tuple[str, ...] = field(default_factory=tuple)
    markets: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "event_ids", tuple(str(e) for e in self.event_ids))
        object.__setattr__(self, "regions", tuple(str(r).upper() for r in self.regions))
        object.__setattr__(self, "markets", tuple(str(m).upper() for m in self.markets))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "event_ids": list(self.event_ids),
            "regions": list(self.regions),
            "markets": list(self.markets),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    events_seen: int
    opportunities_emitted: int
    rejected_records: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "records_seen": self.records_seen,
            "events_seen": self.events_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventDiscoveryHealth:
    schema_version: str
    engine_id: str
    status: str
    ready: bool
    details: Mapping[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=_utc_now_iso)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "details", _freeze(dict(self.details or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "ready": self.ready,
            "details": dict(self.details),
            "checked_at": self.checked_at,
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: MacroEventDiscoveryFamily
    source_name: str
    supports_replay: bool = True
    deterministic: bool = True
    telemetry: bool = True
    read_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "supports_replay": self.supports_replay,
            "deterministic": self.deterministic,
            "telemetry": self.telemetry,
            "read_only": self.read_only,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class MacroEventDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: MacroEventDiscoveryTelemetry
    health: MacroEventDiscoveryHealth
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "opportunities", tuple(self.opportunities or ()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "status": self.status,
            "opportunities": [
                o.to_dict() if hasattr(o, "to_dict") else dict(o)
                for o in self.opportunities
            ],
            "telemetry": self.telemetry.to_dict(),
            "health": self.health.to_dict(),
            "read_only": self.read_only,
        }


class MacroEventDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> MacroEventDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> MacroEventDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: MacroEventDiscoveryRequest) -> MacroEventDiscoveryResult:
        raise NotImplementedError


class EmptyMacroEventDiscoveryEngine(MacroEventDiscoveryEngineContract):
    engine_id = "oracle.discovery.macro_event.empty"

    def capabilities(self) -> MacroEventDiscoveryCapability:
        return MacroEventDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> MacroEventDiscoveryHealth:
        return MacroEventDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: MacroEventDiscoveryRequest) -> MacroEventDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = MacroEventDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            events_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return MacroEventDiscoveryResult(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            status="empty",
            opportunities=(),
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "CONTRACT_ID",
    "MacroEventDiscoveryFamily",
    "MacroEventDiscoveryRequest",
    "MacroEventDiscoveryTelemetry",
    "MacroEventDiscoveryHealth",
    "MacroEventDiscoveryCapability",
    "MacroEventDiscoveryResult",
    "MacroEventDiscoveryEngineContract",
    "EmptyMacroEventDiscoveryEngine",
]
