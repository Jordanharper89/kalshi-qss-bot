"""
ODM-001 Oracle Discovery Contract

Canonical discovery interface for Oracle Intelligence V3.

Purpose:
- Define one interface for all future discovery engines.
- Support prediction markets, crypto, settlement, arbitrage, Solana launches,
  wallet intelligence, macro discovery, and future opportunity hunters.
- Discovery engines produce UniversalOpportunity objects.
- Oracle remains read-only.
- Q Series remains execution-only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


ODM_VERSION = "ODM-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DiscoveryStatus(str, Enum):
    OK = "ok"
    EMPTY = "empty"
    DEGRADED = "degraded"
    FAILED = "failed"


class DiscoveryMode(str, Enum):
    SNAPSHOT = "snapshot"
    STREAM = "stream"
    BACKFILL = "backfill"
    REPLAY = "replay"
    TEST = "test"


@dataclass(frozen=True)
class DiscoveryCapability:
    name: str
    description: str
    supported_market_types: List[str]
    supported_modes: List[str]
    produces_opportunities: bool = True
    read_only: bool = True
    schema_version: str = ODM_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryRequest:
    request_id: str
    market_types: List[str] = field(default_factory=list)
    venues: List[str] = field(default_factory=list)
    mode: DiscoveryMode = DiscoveryMode.SNAPSHOT
    limit: Optional[int] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    schema_version: str = ODM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["mode"] = self.mode.value
        return data


@dataclass(frozen=True)
class DiscoveryTelemetry:
    engine_id: str
    opportunities_discovered: int
    markets_scanned: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now)
    schema_version: str = ODM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiscoveryHealth:
    engine_id: str
    status: DiscoveryStatus
    ready: bool
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=utc_now)
    schema_version: str = ODM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class DiscoveryResult:
    engine_id: str
    status: DiscoveryStatus
    request: DiscoveryRequest
    opportunities: List[Any] = field(default_factory=list)
    telemetry: Optional[DiscoveryTelemetry] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=utc_now)
    schema_version: str = ODM_VERSION
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "status": self.status.value,
            "request": self.request.to_dict(),
            "opportunities": [
                opportunity.to_dict() if hasattr(opportunity, "to_dict") and callable(opportunity.to_dict) else opportunity
                for opportunity in self.opportunities
            ],
            "telemetry": self.telemetry.to_dict() if self.telemetry else None,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "generated_at": self.generated_at,
            "schema_version": self.schema_version,
            "read_only": self.read_only,
        }


class OracleDiscoveryEngineContract(ABC):
    """
    Base contract for all Oracle discovery engines.

    Discovery engines are read-only opportunity producers.
    They do not place trades, manage positions, or execute orders.
    """

    read_only = True
    schema_version = ODM_VERSION

    @abstractmethod
    def engine_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def engine_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def engine_version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def supported_market_types(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> List[DiscoveryCapability]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> DiscoveryHealth:
        raise NotImplementedError

    @abstractmethod
    def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        raise NotImplementedError

    def telemetry(self) -> DiscoveryTelemetry:
        return DiscoveryTelemetry(
            engine_id=self.engine_id(),
            opportunities_discovered=0,
            metadata={
                "engine_name": self.engine_name(),
                "engine_version": self.engine_version(),
                "contract": self.schema_version,
            },
        )

    def validate_result(self, result: DiscoveryResult) -> bool:
        if result.read_only is not True:
            return False
        if result.engine_id != self.engine_id():
            return False
        for opportunity in result.opportunities:
            if not bool(getattr(opportunity, "read_only", False)):
                return False
            if not callable(getattr(opportunity, "fingerprint", None)):
                return False
            if not callable(getattr(opportunity, "to_dict", None)):
                return False
        return True


class TestDiscoveryEngine(OracleDiscoveryEngineContract):
    """
    Minimal concrete discovery engine used for regression testing and examples.
    """

    def engine_id(self) -> str:
        return "oracle.discovery.test"

    def engine_name(self) -> str:
        return "Test Discovery Engine"

    def engine_version(self) -> str:
        return ODM_VERSION

    def supported_market_types(self) -> List[str]:
        return ["prediction_market", "crypto_spot"]

    def capabilities(self) -> List[DiscoveryCapability]:
        return [
            DiscoveryCapability(
                name="test_discovery",
                description="Produces test discovery results for contract validation.",
                supported_market_types=self.supported_market_types(),
                supported_modes=[DiscoveryMode.SNAPSHOT.value, DiscoveryMode.TEST.value],
            )
        ]

    def health_check(self) -> DiscoveryHealth:
        return DiscoveryHealth(
            engine_id=self.engine_id(),
            status=DiscoveryStatus.OK,
            ready=True,
            details={
                "read_only": True,
                "contract": ODM_VERSION,
            },
        )

    def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        telemetry = DiscoveryTelemetry(
            engine_id=self.engine_id(),
            opportunities_discovered=0,
            markets_scanned=0,
            metadata={
                "mode": request.mode.value,
                "test_engine": True,
            },
        )

        return DiscoveryResult(
            engine_id=self.engine_id(),
            status=DiscoveryStatus.EMPTY,
            request=request,
            opportunities=[],
            telemetry=telemetry,
        )


def make_discovery_request(
    request_id: str,
    market_types: Optional[List[str]] = None,
    venues: Optional[List[str]] = None,
    mode: DiscoveryMode = DiscoveryMode.SNAPSHOT,
    limit: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> DiscoveryRequest:
    return DiscoveryRequest(
        request_id=request_id,
        market_types=market_types or [],
        venues=venues or [],
        mode=mode,
        limit=limit,
        filters=filters or {},
        metadata=metadata or {},
    )


__all__ = [
    "ODM_VERSION",
    "DiscoveryStatus",
    "DiscoveryMode",
    "DiscoveryCapability",
    "DiscoveryRequest",
    "DiscoveryTelemetry",
    "DiscoveryHealth",
    "DiscoveryResult",
    "OracleDiscoveryEngineContract",
    "TestDiscoveryEngine",
    "make_discovery_request",
]
