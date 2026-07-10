
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


READ_ONLY = True
SCHEMA_VERSION = "CRD-001"
ENGINE_ID = "oracle.discovery.correlation.contract"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CorrelationDiscoveryOpportunity:
    opportunity_id: str
    primary_market_id: str
    related_market_id: str
    venue: str
    signal_type: str
    relationship: str
    confidence: float
    magnitude: float
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def opportunity_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class CorrelationDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    opportunities: Tuple[CorrelationDiscoveryOpportunity, ...] = tuple()
    read_only: bool = True
    result_hash: str = ""

    @property
    def opportunity_count(self) -> int:
        return len(self.opportunities)

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunity_count"] = self.opportunity_count
        data["opportunities"] = [o.canonical() for o in self.opportunities]
        return _deep_sort(data)


def empty_correlation_discovery_result(
    engine_id: str = "oracle.discovery.correlation.empty",
) -> CorrelationDiscoveryResult:
    unsigned = CorrelationDiscoveryResult(
        schema_version=SCHEMA_VERSION,
        engine_id=engine_id,
        status="empty",
        opportunities=tuple(),
        read_only=True,
        result_hash="",
    )

    return CorrelationDiscoveryResult(
        schema_version=unsigned.schema_version,
        engine_id=unsigned.engine_id,
        status=unsigned.status,
        opportunities=unsigned.opportunities,
        read_only=True,
        result_hash=_stable_hash(unsigned.canonical()),
    )


def assert_correlation_contract_read_only(result: CorrelationDiscoveryResult) -> bool:
    if not isinstance(result, CorrelationDiscoveryResult):
        raise TypeError("result must be a CorrelationDiscoveryResult")
    if result.read_only is not True:
        raise AssertionError("correlation discovery result must be read-only")
    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationDiscoveryOpportunity",
    "CorrelationDiscoveryResult",
    "empty_correlation_discovery_result",
    "assert_correlation_contract_read_only",
]
