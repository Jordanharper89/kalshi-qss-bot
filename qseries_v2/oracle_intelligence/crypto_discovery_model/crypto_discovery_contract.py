"""
CDM-001 Crypto Discovery Contract

Canonical read-only contract for Oracle Crypto Discovery divisions.

Oracle responsibilities:
- discover crypto market opportunities
- normalize source records
- emit UniversalOpportunity-compatible records
- preserve determinism, replayability, explainability, telemetry

Oracle does NOT:
- place trades
- size positions
- execute swaps/orders
- manage exits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "CDM-001"
CONTRACT_ID = "oracle.discovery.contract.crypto"


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


class CryptoDiscoveryFamily(str, Enum):
    CRYPTO_SPOT = "crypto_spot"
    ARBITRAGE = "crypto_arbitrage"
    SOLANA_LAUNCH = "solana_launch"
    WALLET_INTELLIGENCE = "wallet_intelligence"
    LIQUIDITY = "crypto_liquidity"
    VOLATILITY = "crypto_volatility"


@dataclass(frozen=True)
class CryptoDiscoveryRequest:
    request_id: str
    family: CryptoDiscoveryFamily
    source_name: str
    symbols: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "symbols", tuple(str(s).upper() for s in self.symbols))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "symbols": list(self.symbols),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
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
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoDiscoveryHealth:
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
class CryptoDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: CryptoDiscoveryFamily
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
class CryptoDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: CryptoDiscoveryTelemetry
    health: CryptoDiscoveryHealth
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


class CryptoDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> CryptoDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> CryptoDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: CryptoDiscoveryRequest) -> CryptoDiscoveryResult:
        raise NotImplementedError


class EmptyCryptoDiscoveryEngine(CryptoDiscoveryEngineContract):
    engine_id = "oracle.discovery.crypto.empty"

    def capabilities(self) -> CryptoDiscoveryCapability:
        return CryptoDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name="empty",
            metadata={"purpose": "contract regression test"},
        )

    def health(self) -> CryptoDiscoveryHealth:
        return CryptoDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True},
        )

    def discover(self, request: CryptoDiscoveryRequest) -> CryptoDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = CryptoDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True},
        )
        return CryptoDiscoveryResult(
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
    "CryptoDiscoveryFamily",
    "CryptoDiscoveryRequest",
    "CryptoDiscoveryTelemetry",
    "CryptoDiscoveryHealth",
    "CryptoDiscoveryCapability",
    "CryptoDiscoveryResult",
    "CryptoDiscoveryEngineContract",
    "EmptyCryptoDiscoveryEngine",
]
