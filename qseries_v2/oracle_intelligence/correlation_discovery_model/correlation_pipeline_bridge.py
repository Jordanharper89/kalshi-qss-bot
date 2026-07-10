
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .correlation_discovery_engine import (
    CorrelationDiscoveryEngine,
    CorrelationDiscoveryResult,
)
from .correlation_pipeline_gate import (
    CorrelationPipelineGate,
    CorrelationPipelineGateResult,
)
from .correlation_registry_bridge import (
    CorrelationRegistryBridge,
    CorrelationRegistryEntry,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-006"
ENGINE_ID = "oracle.discovery.correlation.pipeline_bridge"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CorrelationPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: CorrelationDiscoveryResult
    gate: CorrelationPipelineGateResult
    registry_entry: CorrelationRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "correlation.generic",
        strong_correlation_threshold: float = 0.70,
        correlation_break_threshold: float = 0.30,
        return_divergence_threshold: float = 0.04,
        min_sample_size: int = 20,
    ) -> None:
        self.source_name = str(
            source_name or "correlation.generic"
        )

        self.discovery_engine = CorrelationDiscoveryEngine(
            strong_correlation_threshold=(
                strong_correlation_threshold
            ),
            correlation_break_threshold=(
                correlation_break_threshold
            ),
            return_divergence_threshold=(
                return_divergence_threshold
            ),
            min_sample_size=min_sample_size,
        )

        self.pipeline_gate = CorrelationPipelineGate()
        self.registry_bridge = CorrelationRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> CorrelationPipelineBridgeResult:
        raw_list = list(raw_records or [])

        discovery = self.discovery_engine.discover_from_raw(
            raw_records=raw_list,
            source_name=self.source_name,
            observed_at=observed_at,
        )

        gate = self.pipeline_gate.validate(discovery)
        registry_entry = self.registry_bridge.bridge(gate)

        accepted = (
            gate.accepted
            and registry_entry.accepted
        )

        status = (
            "accepted"
            if accepted
            else "rejected"
        )

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "execution_capable": False,
            "external_mutation_allowed": False,
            "pipeline_steps": [
                "source_adapter",
                "discovery_engine",
                "pipeline_gate",
                "registry_bridge",
            ],
            "source_name": self.source_name,
            "source_record_count": len(raw_list),
            "discovery_result_hash": (
                discovery.result_hash
            ),
            "gate_hash": gate.gate_hash,
            "registry_hash": (
                registry_entry.registry_hash
            ),
        }

        unsigned = CorrelationPipelineBridgeResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            source_name=self.source_name,
            observed_at=discovery.observed_at,
            discovery=discovery,
            gate=gate,
            registry_entry=registry_entry,
            opportunity_count=(
                discovery.opportunity_count
            ),
            read_only=True,
            pipeline_hash="",
            audit=audit,
        )

        return CorrelationPipelineBridgeResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            discovery=unsigned.discovery,
            gate=unsigned.gate,
            registry_entry=unsigned.registry_entry,
            opportunity_count=(
                unsigned.opportunity_count
            ),
            read_only=True,
            pipeline_hash=_stable_hash(
                unsigned.canonical()
            ),
            audit=unsigned.audit,
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "source_normalization",
                "correlation_discovery",
                "pipeline_validation",
                "registry_bridging",
                "deterministic_pipeline_hashing",
                "order_independent_processing",
                "empty_pipeline_processing",
            ],
            "thresholds": {
                "strong_correlation_threshold": (
                    self.discovery_engine
                    .strong_correlation_threshold
                ),
                "correlation_break_threshold": (
                    self.discovery_engine
                    .correlation_break_threshold
                ),
                "return_divergence_threshold": (
                    self.discovery_engine
                    .return_divergence_threshold
                ),
                "min_sample_size": (
                    self.discovery_engine
                    .min_sample_size
                ),
            },
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                f"mutation-like methods are forbidden: "
                f"{offenders}"
            )

        self.discovery_engine.assert_read_only()
        self.pipeline_gate.assert_read_only()
        self.registry_bridge.assert_read_only()

        return True


def run_correlation_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
) -> CorrelationPipelineBridgeResult:
    bridge = CorrelationPipelineBridge(
        source_name=source_name,
        strong_correlation_threshold=(
            strong_correlation_threshold
        ),
        correlation_break_threshold=(
            correlation_break_threshold
        ),
        return_divergence_threshold=(
            return_divergence_threshold
        ),
        min_sample_size=min_sample_size,
    )

    return bridge.run(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationPipelineBridge",
    "CorrelationPipelineBridgeResult",
    "run_correlation_pipeline",
]
