
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .liquidity_pipeline_gate import LiquidityPipelineGateResult


READ_ONLY = True
SCHEMA_VERSION = "LQD-005"
ENGINE_ID = "oracle.discovery.liquidity.registry_bridge"


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
class LiquidityRegistryEntry:
    schema_version: str
    engine_id: str
    family: str
    bridge_status: str
    accepted: bool
    registry_key: str
    source_gate_hash: str
    source_result_hash: str
    opportunity_count: int
    capabilities: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    registry_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class LiquidityRegistryBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(self, family: str = "liquidity_discovery") -> None:
        self.family = str(family or "liquidity_discovery")

    def bridge(self, gate_result: LiquidityPipelineGateResult) -> LiquidityRegistryEntry:
        if not isinstance(gate_result, LiquidityPipelineGateResult):
            raise TypeError("gate_result must be a LiquidityPipelineGateResult")

        registry_key = _stable_hash(
            {
                "family": self.family,
                "source_gate_hash": gate_result.gate_hash,
                "source_result_hash": gate_result.discovery_result_hash,
                "source_schema_version": gate_result.schema_version,
            }
        )

        capabilities = {
            "family": self.family,
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "auditable": True,
            "source_schema_version": gate_result.schema_version,
            "source_engine_id": gate_result.engine_id,
            "source_status": gate_result.status,
            "checks": dict(gate_result.checks),
        }

        unsigned = LiquidityRegistryEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            family=self.family,
            bridge_status="registered" if gate_result.accepted else "rejected",
            accepted=gate_result.accepted,
            registry_key=registry_key,
            source_gate_hash=gate_result.gate_hash,
            source_result_hash=gate_result.discovery_result_hash,
            opportunity_count=gate_result.opportunity_count,
            capabilities=capabilities,
            read_only=True,
            registry_hash="",
        )

        return LiquidityRegistryEntry(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            family=unsigned.family,
            bridge_status=unsigned.bridge_status,
            accepted=unsigned.accepted,
            registry_key=unsigned.registry_key,
            source_gate_hash=unsigned.source_gate_hash,
            source_result_hash=unsigned.source_result_hash,
            opportunity_count=unsigned.opportunity_count,
            capabilities=unsigned.capabilities,
            read_only=True,
            registry_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def bridge_liquidity_registry(gate_result: LiquidityPipelineGateResult) -> LiquidityRegistryEntry:
    return LiquidityRegistryBridge().bridge(gate_result)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquidityRegistryBridge",
    "LiquidityRegistryEntry",
    "bridge_liquidity_registry",
]
