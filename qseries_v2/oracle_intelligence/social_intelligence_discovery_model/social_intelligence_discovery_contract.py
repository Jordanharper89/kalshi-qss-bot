
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

SCHEMA_VERSION = "SID-001"
CONTRACT_ID = "oracle.discovery.contract.social_intelligence"


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


class SocialIntelligenceFamily(str, Enum):
    SOCIAL_MOMENTUM = "social_momentum"
    VIRAL_NARRATIVE = "viral_narrative"
    INFLUENCER_SIGNAL = "influencer_signal"
    SENTIMENT_SHIFT = "sentiment_shift"
    COMMUNITY_BUZZ = "community_buzz"
    PREDICTION_MARKET_SOCIAL = "prediction_market_social"
    CRYPTO_SOCIAL = "crypto_social"
    SPORTS_SOCIAL = "sports_social"


@dataclass(frozen=True)
class SocialIntelligenceDiscoveryRequest:
    request_id: str
    family: SocialIntelligenceFamily
    source_name: str
    post_ids: Tuple[str, ...] = field(default_factory=tuple)
    topics: Tuple[str, ...] = field(default_factory=tuple)
    markets: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "post_ids", tuple(str(x) for x in self.post_ids))
        object.__setattr__(self, "topics", tuple(str(x).lower() for x in self.topics))
        object.__setattr__(self, "markets", tuple(str(x).upper() for x in self.markets))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "post_ids": list(self.post_ids),
            "topics": list(self.topics),
            "markets": list(self.markets),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligenceDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    posts_seen: int
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
            "posts_seen": self.posts_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SocialIntelligenceDiscoveryHealth:
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
class SocialIntelligenceDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: SocialIntelligenceFamily
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
class SocialIntelligenceDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: SocialIntelligenceDiscoveryTelemetry
    health: SocialIntelligenceDiscoveryHealth
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


class SocialIntelligenceDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> SocialIntelligenceDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> SocialIntelligenceDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: SocialIntelligenceDiscoveryRequest) -> SocialIntelligenceDiscoveryResult:
        raise NotImplementedError


class EmptySocialIntelligenceDiscoveryEngine(SocialIntelligenceDiscoveryEngineContract):
    engine_id = "oracle.discovery.social_intelligence.empty"

    def capabilities(self) -> SocialIntelligenceDiscoveryCapability:
        return SocialIntelligenceDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=SocialIntelligenceFamily.SOCIAL_MOMENTUM,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> SocialIntelligenceDiscoveryHealth:
        return SocialIntelligenceDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: SocialIntelligenceDiscoveryRequest) -> SocialIntelligenceDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = SocialIntelligenceDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            posts_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return SocialIntelligenceDiscoveryResult(
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
    "SocialIntelligenceFamily",
    "SocialIntelligenceDiscoveryRequest",
    "SocialIntelligenceDiscoveryTelemetry",
    "SocialIntelligenceDiscoveryHealth",
    "SocialIntelligenceDiscoveryCapability",
    "SocialIntelligenceDiscoveryResult",
    "SocialIntelligenceDiscoveryEngineContract",
    "EmptySocialIntelligenceDiscoveryEngine",
]
