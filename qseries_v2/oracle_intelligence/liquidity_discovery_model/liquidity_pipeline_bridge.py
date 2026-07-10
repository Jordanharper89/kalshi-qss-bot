
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .liquidity_discovery_engine import LiquidityDiscoveryEngine, LiquidityDiscoveryResult
from .liquidity_pipeline_gate import LiquidityPipelineGate, LiquidityPipelineGateResult
from .liquidity_registry_bridge import LiquidityRegistryBridge, LiquidityRegistryEntry


READ_ONLY = True
SCHEMA_VERSION = "LQD-006"
ENGINE_ID = "oracle.discovery.liquidity.pipeline_bridge"


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
class LiquidityPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: LiquidityDiscoveryResult
    gate: LiquidityPipelineGateResult
    registry_entry: LiquidityRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class LiquidityPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "liquidity.generic",
        min_spread_bps: float = 250.0,
        max_total_depth: float = 1000.0,
        min_depth_imbalance: float = 0.35,
        min_volume_24h: float = 0.0,
    ) -> None:
        self.source_name = str(source_name or "liquidity.generic")
        self.discovery_engine = LiquidityDiscoveryEngine(
            min_spread_bps=min_spread_bps,
            max_total_depth=max_total_depth,
            min_depth_imbalance=min_depth_imbalance,
            min_volume_24h=min_volume_24h,
        )
        self.pipeline_gate = LiquidityPipelineGate()
        self.registry_bridge = LiquidityRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> LiquidityPipelineBridgeResult:
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

        unsigned = LiquidityPipelineBridgeResult(
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

        return LiquidityPipelineBridgeResult(
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


def run_liquidity_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "liquidity.generic",
    observed_at: Optional[str] = None,
    min_spread_bps: float = 250.0,
    max_total_depth: float = 1000.0,
    min_depth_imbalance: float = 0.35,
    min_volume_24h: float = 0.0,
) -> LiquidityPipelineBridgeResult:
    bridge = LiquidityPipelineBridge(
        source_name=source_name,
        min_spread_bps=min_spread_bps,
        max_total_depth=max_total_depth,
        min_depth_imbalance=min_depth_imbalance,
        min_volume_24h=min_volume_24h,
    )
    return bridge.run(raw_records=raw_records, observed_at=observed_at)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquidityPipelineBridge",
    "LiquidityPipelineBridgeResult",
    "run_liquidity_pipeline",
]
