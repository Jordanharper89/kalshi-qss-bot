
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .correlation_pipeline_gate import CorrelationPipelineGateResult


READ_ONLY = True
SCHEMA_VERSION = "CRD-005"
ENGINE_ID = "oracle.discovery.correlation.registry_bridge"


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
class CorrelationRegistryEntry:
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


class CorrelationRegistryBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        family: str = "correlation_discovery",
    ) -> None:
        self.family = str(
            family or "correlation_discovery"
        )

    def bridge(
        self,
        gate_result: CorrelationPipelineGateResult,
    ) -> CorrelationRegistryEntry:
        if not isinstance(
            gate_result,
            CorrelationPipelineGateResult,
        ):
            raise TypeError(
                "gate_result must be a "
                "CorrelationPipelineGateResult"
            )

        registry_key = _stable_hash(
            {
                "family": self.family,
                "source_gate_hash": gate_result.gate_hash,
                "source_result_hash": (
                    gate_result.discovery_result_hash
                ),
                "source_schema_version": (
                    gate_result.schema_version
                ),
                "source_engine_id": gate_result.engine_id,
            }
        )

        capabilities = {
            "family": self.family,
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "auditable": True,
            "execution_capable": False,
            "external_mutation_allowed": False,
            "source_schema_version": (
                gate_result.schema_version
            ),
            "source_engine_id": gate_result.engine_id,
            "source_status": gate_result.status,
            "source_accepted": gate_result.accepted,
            "checks": dict(gate_result.checks),
            "supported_signals": [
                "correlation_break",
                "correlation_sign_flip",
                "return_divergence",
                "lead_lag_relationship",
                "correlation_decay",
            ],
        }

        bridge_status = (
            "registered"
            if gate_result.accepted
            else "rejected"
        )

        unsigned = CorrelationRegistryEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            family=self.family,
            bridge_status=bridge_status,
            accepted=gate_result.accepted,
            registry_key=registry_key,
            source_gate_hash=gate_result.gate_hash,
            source_result_hash=(
                gate_result.discovery_result_hash
            ),
            opportunity_count=(
                gate_result.opportunity_count
            ),
            capabilities=capabilities,
            read_only=True,
            registry_hash="",
        )

        return CorrelationRegistryEntry(
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
            registry_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "family": self.family,
            "read_only": True,
            "supports": [
                "accepted_gate_registration",
                "rejected_gate_registration",
                "deterministic_registry_keys",
                "deterministic_registry_hashes",
                "capability_manifest_generation",
            ],
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

        return True


def bridge_correlation_registry(
    gate_result: CorrelationPipelineGateResult,
) -> CorrelationRegistryEntry:
    return CorrelationRegistryBridge().bridge(
        gate_result
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationRegistryBridge",
    "CorrelationRegistryEntry",
    "bridge_correlation_registry",
]
