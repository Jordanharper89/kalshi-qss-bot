from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_final_certification_freeze_gate import (
    IntegratedIntelligenceFinalCertification,
    verify_integrated_intelligence_final_certification,
)

ENGINE_ID = "OSR-001"
SCHEMA_VERSION = "OSR-001.v1"
ALGORITHM_VERSION = "scientific-reasoning-callable-registry.v1"

APPROVED_DISCIPLINES = (
    "adversarial_epistemology",
    "bayesian_inference",
    "calibration_science",
    "causal_inference",
    "complex_systems",
    "decision_theory",
    "game_theory",
    "information_theory",
    "signal_detection_theory",
)

class OracleScientificReasoningRegistryInvariantError(ValueError):
    pass

def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)

def stable_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningCallableDescriptor:
    discipline_id: str
    callable_id: str
    implementation_module: str
    implementation_symbol: str
    registry_status: str
    active: bool
    resolved: bool
    bound: bool
    executable: bool
    read_only: bool
    descriptor_hash: str

@dataclass(frozen=True)
class ScientificReasoningCallableRegistry:
    registry_id: str
    source_oii015_certification_id: str
    source_oii015_certification_hash: str
    source_frozen_evidence_set_hash: str
    callable_descriptors: tuple[ScientificReasoningCallableDescriptor, ...]
    registered_disciplines: tuple[str, ...]
    registered_callable_count: int
    registry_status: str
    registry_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    reasoning_execution_allowed: bool
    probability_estimation_allowed: bool
    final_intelligence_conclusion_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool

def build_scientific_reasoning_callable_descriptor(discipline_id: str) -> ScientificReasoningCallableDescriptor:
    discipline_id = discipline_id.strip().lower()
    if discipline_id not in APPROVED_DISCIPLINES:
        raise OracleScientificReasoningRegistryInvariantError("discipline is not approved")
    body = {
        "discipline_id": discipline_id,
        "callable_id": f"oracle.scientific_reasoning.{discipline_id}.v1",
        "implementation_module": f"qseries_v2.oracle_scientific_reasoning_runtime.disciplines.{discipline_id}_adapter",
        "implementation_symbol": f"evaluate_{discipline_id}_read_only",
        "registry_status": "registered_inactive_unresolved_unbound",
        "active": False,
        "resolved": False,
        "bound": False,
        "executable": False,
        "read_only": True,
    }
    return ScientificReasoningCallableDescriptor(**body, descriptor_hash=stable_hash(body))

def verify_scientific_reasoning_callable_descriptor(item: ScientificReasoningCallableDescriptor) -> bool:
    body = {k: v for k, v in asdict(item).items() if k != "descriptor_hash"}
    if stable_hash(body) != item.descriptor_hash:
        raise OracleScientificReasoningRegistryInvariantError("descriptor hash failed")
    if item.discipline_id not in APPROVED_DISCIPLINES or item.active or item.resolved or item.bound or item.executable or not item.read_only:
        raise OracleScientificReasoningRegistryInvariantError("descriptor boundary failed")
    return True

def build_scientific_reasoning_callable_registry(*, terminal_certification: IntegratedIntelligenceFinalCertification, descriptors: Sequence[ScientificReasoningCallableDescriptor] | None = None) -> ScientificReasoningCallableRegistry:
    try:
        verify_integrated_intelligence_final_certification(terminal_certification)
    except Exception as exc:
        raise OracleScientificReasoningRegistryInvariantError("OII-015 verification failed") from exc
    if terminal_certification.engine_id != "OII-015" or not terminal_certification.subsystem_frozen or terminal_certification.further_certification_layers_required or not terminal_certification.read_only:
        raise OracleScientificReasoningRegistryInvariantError("OII-015 freeze boundary failed")
    ordered = tuple(sorted(descriptors or tuple(build_scientific_reasoning_callable_descriptor(d) for d in APPROVED_DISCIPLINES), key=lambda x: x.discipline_id))
    disciplines = tuple(x.discipline_id for x in ordered)
    if disciplines != APPROVED_DISCIPLINES or len(set(x.callable_id for x in ordered)) != len(ordered):
        raise OracleScientificReasoningRegistryInvariantError("registry completeness failed")
    for item in ordered:
        verify_scientific_reasoning_callable_descriptor(item)
    body = {
        "source_oii015_certification_id": terminal_certification.certification_id,
        "source_oii015_certification_hash": terminal_certification.certification_hash,
        "source_frozen_evidence_set_hash": terminal_certification.frozen_evidence_set_hash,
        "callable_descriptors": ordered,
        "registered_disciplines": disciplines,
        "registered_callable_count": len(ordered),
        "registry_status": "certified_registry_materialized_inactive_unresolved_unbound",
    }
    h = stable_hash(body)
    return ScientificReasoningCallableRegistry(
        registry_id="scientific-reasoning-callable-registry:" + h,
        **body,
        registry_hash=h,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        callable_resolution_allowed=False,
        callable_binding_allowed=False,
        reasoning_execution_allowed=False,
        probability_estimation_allowed=False,
        final_intelligence_conclusion_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )

def verify_scientific_reasoning_callable_registry(registry: ScientificReasoningCallableRegistry) -> bool:
    for item in registry.callable_descriptors:
        verify_scientific_reasoning_callable_descriptor(item)
    body = {
        "source_oii015_certification_id": registry.source_oii015_certification_id,
        "source_oii015_certification_hash": registry.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash": registry.source_frozen_evidence_set_hash,
        "callable_descriptors": registry.callable_descriptors,
        "registered_disciplines": registry.registered_disciplines,
        "registered_callable_count": registry.registered_callable_count,
        "registry_status": registry.registry_status,
    }
    if stable_hash(body) != registry.registry_hash or registry.registered_disciplines != APPROVED_DISCIPLINES:
        raise OracleScientificReasoningRegistryInvariantError("registry verification failed")
    forbidden = (registry.callable_resolution_allowed, registry.callable_binding_allowed, registry.reasoning_execution_allowed, registry.probability_estimation_allowed, registry.final_intelligence_conclusion_allowed, registry.publication_allowed, registry.alerting_allowed, registry.qseries_handoff_allowed, registry.qseries_execution_allowed, registry.order_creation_allowed, registry.funds_movement_allowed, registry.portfolio_mutation_allowed)
    if registry.engine_id != ENGINE_ID or not registry.read_only or any(forbidden):
        raise OracleScientificReasoningRegistryInvariantError("registry safety boundary failed")
    return True

def serialize_scientific_reasoning_callable_registry(registry: ScientificReasoningCallableRegistry) -> str:
    verify_scientific_reasoning_callable_registry(registry)
    return json.dumps(_canonical(registry), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
