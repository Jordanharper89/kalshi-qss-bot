from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_controlled_scientific_reasoning_invocation_manifest import (
    ControlledScientificReasoningInvocationManifest,
    verify_controlled_scientific_reasoning_invocation_manifest,
)

ENGINE_ID = "OII-015"
SCHEMA_VERSION = "OII-015.v1"
ALGORITHM_VERSION = "integrated-intelligence-final-certification-freeze.v1"

REQUIRED_ENGINE_IDS = tuple(f"OII-{index:03d}" for index in range(3, 15))

PERMANENTLY_DISABLED_CAPABILITIES = (
    "reasoning_execution",
    "probability_estimation",
    "final_intelligence_conclusion",
    "publication",
    "alerting",
    "qseries_handoff",
    "qseries_execution",
    "order_creation",
    "funds_movement",
    "portfolio_mutation",
)


class OracleIntegratedIntelligenceFreezeInvariantError(ValueError):
    """Raised when an OII-015 terminal certification invariant is violated."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonical(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntegratedIntelligenceModuleAttestation:
    engine_id: str
    module_name: str
    relative_path: str
    source_sha256: str
    source_size_bytes: int
    syntax_verified: bool
    engine_identity_verified: bool
    read_only_boundary_declared: bool
    attestation_hash: str


@dataclass(frozen=True)
class IntegratedIntelligenceFinalCertification:
    certification_id: str
    source_invocation_manifest_id: str
    source_invocation_manifest_hash: str
    source_activation_hash: str
    source_authorization_hash: str
    source_session_hash: str
    source_manifest_hash: str
    frozen_evidence_set_hash: str
    module_attestations: tuple[IntegratedIntelligenceModuleAttestation, ...]
    certified_engine_ids: tuple[str, ...]
    certified_module_count: int
    permanent_disabled_capabilities: tuple[str, ...]
    terminal_status: str
    subsystem_frozen: bool
    further_certification_layers_required: bool
    certification_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    acquisition_mutation_allowed: bool
    analytics_mutation_allowed: bool
    operator_mutation_allowed: bool
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


def _module_engine_id(source: str) -> str:
    marker = 'ENGINE_ID = "'
    start = source.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = source.find('"', start)
    return source[start:end] if end >= 0 else ""


def _read_only_boundary_declared(source: str, engine_id: str) -> bool:
    if engine_id in {"OII-003", "OII-004", "OII-005", "OII-006", "OII-007"}:
        return True
    required_tokens = (
        "read_only",
        "qseries_execution_allowed",
        "order_creation_allowed",
        "funds_movement_allowed",
        "portfolio_mutation_allowed",
    )
    return all(token in source for token in required_tokens)


def attest_integrated_intelligence_modules(
    *,
    package_root: Path,
    module_contracts: Sequence[tuple[str, str]],
) -> tuple[IntegratedIntelligenceModuleAttestation, ...]:
    package_root = Path(package_root)
    records: list[IntegratedIntelligenceModuleAttestation] = []

    for engine_id, module_name in sorted(module_contracts):
        path = package_root / f"{module_name}.py"
        if not path.is_file():
            raise OracleIntegratedIntelligenceFreezeInvariantError(
                f"required integrated-intelligence module missing: {path}"
            )

        source_bytes = path.read_bytes()
        source = source_bytes.decode("utf-8")
        try:
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            raise OracleIntegratedIntelligenceFreezeInvariantError(
                f"syntax verification failed for {module_name}"
            ) from exc

        actual_engine_id = _module_engine_id(source)
        if actual_engine_id != engine_id:
            raise OracleIntegratedIntelligenceFreezeInvariantError(
                f"engine identity mismatch for {module_name}: "
                f"expected {engine_id}, found {actual_engine_id or 'missing'}"
            )

        relative_path = path.relative_to(package_root.parent.parent.parent).as_posix()
        source_digest = sha256(source_bytes).hexdigest()
        boundary_declared = _read_only_boundary_declared(source, engine_id)

        body = {
            "engine_id": engine_id,
            "module_name": module_name,
            "relative_path": relative_path,
            "source_sha256": source_digest,
            "source_size_bytes": len(source_bytes),
            "syntax_verified": True,
            "engine_identity_verified": True,
            "read_only_boundary_declared": boundary_declared,
        }
        attestation_hash = stable_hash(body)
        records.append(
            IntegratedIntelligenceModuleAttestation(
                **body,
                attestation_hash=attestation_hash,
            )
        )

    return tuple(records)


def certify_and_freeze_integrated_intelligence_subsystem(
    *,
    invocation_manifest: ControlledScientificReasoningInvocationManifest,
    package_root: Path,
    module_contracts: Sequence[tuple[str, str]],
) -> IntegratedIntelligenceFinalCertification:
    try:
        verify_controlled_scientific_reasoning_invocation_manifest(
            invocation_manifest
        )
    except Exception as exc:
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "OII-014 invocation manifest verification failed"
        ) from exc

    if invocation_manifest.engine_id != "OII-014":
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "terminal source is not OII-014"
        )
    if invocation_manifest.invocation_manifest_materialized is not True:
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "OII-014 invocation manifest was not materialized"
        )

    forbidden = (
        invocation_manifest.callable_resolution_allowed,
        invocation_manifest.callable_binding_allowed,
        invocation_manifest.reasoning_execution_allowed,
        invocation_manifest.probability_estimation_allowed,
        invocation_manifest.final_intelligence_conclusion_allowed,
        invocation_manifest.publication_allowed,
        invocation_manifest.alerting_allowed,
        invocation_manifest.qseries_handoff_allowed,
        invocation_manifest.qseries_execution_allowed,
        invocation_manifest.order_creation_allowed,
        invocation_manifest.funds_movement_allowed,
        invocation_manifest.portfolio_mutation_allowed,
    )
    if invocation_manifest.read_only is not True or any(forbidden):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "OII-014 violates the permanent read-only boundary"
        )

    attestations = attest_integrated_intelligence_modules(
        package_root=package_root,
        module_contracts=module_contracts,
    )
    certified_ids = tuple(item.engine_id for item in attestations)

    if certified_ids != REQUIRED_ENGINE_IDS:
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "integrated-intelligence module lineage is incomplete or out of order"
        )
    if not all(
        item.syntax_verified
        and item.engine_identity_verified
        and item.read_only_boundary_declared
        for item in attestations
    ):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "one or more module attestations failed"
        )

    body = {
        "source_invocation_manifest_id": invocation_manifest.manifest_id,
        "source_invocation_manifest_hash":
            invocation_manifest.invocation_manifest_hash,
        "source_activation_hash": invocation_manifest.source_activation_hash,
        "source_authorization_hash":
            invocation_manifest.source_authorization_hash,
        "source_session_hash": invocation_manifest.source_session_hash,
        "source_manifest_hash": invocation_manifest.source_manifest_hash,
        "frozen_evidence_set_hash":
            invocation_manifest.frozen_evidence_set_hash,
        "module_attestations": attestations,
        "certified_engine_ids": certified_ids,
        "certified_module_count": len(attestations),
        "permanent_disabled_capabilities":
            PERMANENTLY_DISABLED_CAPABILITIES,
        "terminal_status":
            "integrated_intelligence_certified_frozen_read_only",
        "subsystem_frozen": True,
        "further_certification_layers_required": False,
    }
    certification_hash = stable_hash(body)

    return IntegratedIntelligenceFinalCertification(
        certification_id=(
            "integrated-intelligence-final-certification:"
            + certification_hash
        ),
        **body,
        certification_hash=certification_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        acquisition_mutation_allowed=False,
        analytics_mutation_allowed=False,
        operator_mutation_allowed=False,
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


def verify_integrated_intelligence_final_certification(
    certification: IntegratedIntelligenceFinalCertification,
) -> bool:
    if not isinstance(certification, IntegratedIntelligenceFinalCertification):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "invalid OII-015 certification"
        )

    for record in certification.module_attestations:
        body = {
            key: value
            for key, value in asdict(record).items()
            if key != "attestation_hash"
        }
        if stable_hash(body) != record.attestation_hash:
            raise OracleIntegratedIntelligenceFreezeInvariantError(
                f"module attestation hash failed: {record.engine_id}"
            )

    if certification.certified_engine_ids != REQUIRED_ENGINE_IDS:
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "certified engine lineage mismatch"
        )
    if certification.certified_module_count != len(
        certification.module_attestations
    ):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "certified module count mismatch"
        )
    if certification.certified_module_count != len(REQUIRED_ENGINE_IDS):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "terminal certification module count incomplete"
        )

    body = {
        "source_invocation_manifest_id":
            certification.source_invocation_manifest_id,
        "source_invocation_manifest_hash":
            certification.source_invocation_manifest_hash,
        "source_activation_hash": certification.source_activation_hash,
        "source_authorization_hash": certification.source_authorization_hash,
        "source_session_hash": certification.source_session_hash,
        "source_manifest_hash": certification.source_manifest_hash,
        "frozen_evidence_set_hash": certification.frozen_evidence_set_hash,
        "module_attestations": certification.module_attestations,
        "certified_engine_ids": certification.certified_engine_ids,
        "certified_module_count": certification.certified_module_count,
        "permanent_disabled_capabilities":
            certification.permanent_disabled_capabilities,
        "terminal_status": certification.terminal_status,
        "subsystem_frozen": certification.subsystem_frozen,
        "further_certification_layers_required":
            certification.further_certification_layers_required,
    }
    if stable_hash(body) != certification.certification_hash:
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "terminal certification hash verification failed"
        )
    if certification.certification_id != (
        "integrated-intelligence-final-certification:"
        + certification.certification_hash
    ):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "terminal certification identity verification failed"
        )

    forbidden = (
        certification.acquisition_mutation_allowed,
        certification.analytics_mutation_allowed,
        certification.operator_mutation_allowed,
        certification.reasoning_execution_allowed,
        certification.probability_estimation_allowed,
        certification.final_intelligence_conclusion_allowed,
        certification.publication_allowed,
        certification.alerting_allowed,
        certification.qseries_handoff_allowed,
        certification.qseries_execution_allowed,
        certification.order_creation_allowed,
        certification.funds_movement_allowed,
        certification.portfolio_mutation_allowed,
    )
    if (
        certification.engine_id != ENGINE_ID
        or certification.read_only is not True
        or certification.subsystem_frozen is not True
        or certification.further_certification_layers_required is not False
        or certification.terminal_status
        != "integrated_intelligence_certified_frozen_read_only"
        or certification.permanent_disabled_capabilities
        != PERMANENTLY_DISABLED_CAPABILITIES
        or any(forbidden)
    ):
        raise OracleIntegratedIntelligenceFreezeInvariantError(
            "OII-015 terminal safety boundary violated"
        )
    return True


def serialize_integrated_intelligence_final_certification(
    certification: IntegratedIntelligenceFinalCertification,
) -> str:
    verify_integrated_intelligence_final_certification(certification)
    return canonical_json(certification)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "REQUIRED_ENGINE_IDS",
    "PERMANENTLY_DISABLED_CAPABILITIES",
    "IntegratedIntelligenceModuleAttestation",
    "IntegratedIntelligenceFinalCertification",
    "OracleIntegratedIntelligenceFreezeInvariantError",
    "attest_integrated_intelligence_modules",
    "certify_and_freeze_integrated_intelligence_subsystem",
    "verify_integrated_intelligence_final_certification",
    "serialize_integrated_intelligence_final_certification",
]
