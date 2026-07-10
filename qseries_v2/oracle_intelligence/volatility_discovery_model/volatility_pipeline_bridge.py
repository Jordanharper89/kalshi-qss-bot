
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .volatility_discovery_engine import VolatilityDiscoveryEngine, VolatilityDiscoveryResult
from .volatility_pipeline_gate import VolatilityPipelineGate, VolatilityPipelineGateResult
from .volatility_registry_bridge import VolatilityRegistryBridge, VolatilityRegistryEntry


READ_ONLY = True
SCHEMA_VERSION = "VLD-006"
ENGINE_ID = "oracle.discovery.volatility.pipeline_bridge"


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
class VolatilityPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: VolatilityDiscoveryResult
    gate: VolatilityPipelineGateResult
    registry_entry: VolatilityRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class VolatilityPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "volatility.generic",
        expansion_ratio_threshold: float = 1.50,
        contraction_ratio_threshold: float = 0.70,
        iv_rv_gap_threshold: float = 0.10,
        shock_return_threshold: float = 0.05,
        min_volume: float = 0.0,
    ) -> None:
        self.source_name = str(source_name or "volatility.generic")
        self.discovery_engine = VolatilityDiscoveryEngine(
            expansion_ratio_threshold=expansion_ratio_threshold,
            contraction_ratio_threshold=contraction_ratio_threshold,
            iv_rv_gap_threshold=iv_rv_gap_threshold,
            shock_return_threshold=shock_return_threshold,
            min_volume=min_volume,
        )
        self.pipeline_gate = VolatilityPipelineGate()
        self.registry_bridge = VolatilityRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> VolatilityPipelineBridgeResult:
        discovery = self.discovery_engine.discover_from_raw(
            raw_records=raw_records,
            source_name=self.source_name,
            observed_at=observed_at,
        )
        gate = self.pipeline_gate.validate(discovery)
        registry_entry = self.registry_bridge.bridge(gate)

        accepted = gate.accepted and registry_entry.accepted
        status = "accepted" if accepted else "rejected"

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "pipeline_steps": [
                "source_adapter",
                "discovery_engine",
                "pipeline_gate",
                "registry_bridge",
            ],
            "discovery_result_hash": discovery.result_hash,
            "gate_hash": gate.gate_hash,
            "registry_hash": registry_entry.registry_hash,
        }

        unsigned = VolatilityPipelineBridgeResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            source_name=self.source_name,
            observed_at=discovery.observed_at,
            discovery=discovery,
            gate=gate,
            registry_entry=registry_entry,
            opportunity_count=discovery.opportunity_count,
            read_only=True,
            pipeline_hash="",
            audit=audit,
        )

        return VolatilityPipelineBridgeResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            discovery=unsigned.discovery,
            gate=unsigned.gate,
            registry_entry=unsigned.registry_entry,
            opportunity_count=unsigned.opportunity_count,
            read_only=True,
            pipeline_hash=_stable_hash(unsigned.canonical()),
            audit=unsigned.audit,
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        self.discovery_engine.assert_read_only()
        self.pipeline_gate.assert_read_only()
        self.registry_bridge.assert_read_only()
        return True


def run_volatility_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.generic",
    observed_at: Optional[str] = None,
    expansion_ratio_threshold: float = 1.50,
    contraction_ratio_threshold: float = 0.70,
    iv_rv_gap_threshold: float = 0.10,
    shock_return_threshold: float = 0.05,
    min_volume: float = 0.0,
) -> VolatilityPipelineBridgeResult:
    bridge = VolatilityPipelineBridge(
        source_name=source_name,
        expansion_ratio_threshold=expansion_ratio_threshold,
        contraction_ratio_threshold=contraction_ratio_threshold,
        iv_rv_gap_threshold=iv_rv_gap_threshold,
        shock_return_threshold=shock_return_threshold,
        min_volume=min_volume,
    )
    return bridge.run(raw_records=raw_records, observed_at=observed_at)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityPipelineBridge",
    "VolatilityPipelineBridgeResult",
    "run_volatility_pipeline",
]
