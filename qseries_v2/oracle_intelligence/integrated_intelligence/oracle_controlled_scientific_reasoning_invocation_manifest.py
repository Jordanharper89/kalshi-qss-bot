from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_authorization_consumption_activation_gate import (
    ScientificReasoningSessionActivationPackage,
    verify_scientific_reasoning_session_activation_package,
)

ENGINE_ID = "OII-014"
SCHEMA_VERSION = "OII-014.v1"
ALGORITHM_VERSION = "controlled-scientific-reasoning-invocation-manifest.v1"


class OracleControlledReasoningInvocationInvariantError(ValueError):
    """Raised when an OII-014 invocation-manifest invariant is violated."""


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
class ControlledReasoningInvocationStep:
    invocation_step_id: str
    discipline_activation_id: str
    discipline_name: str
    ordinal: int
    source_activation_record_hash: str
    source_session_hash: str
    source_manifest_hash: str
    frozen_evidence_set_hash: str
    invocation_mode: str
    invocation_status: str
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    invocation_execution_allowed: bool
    probability_estimation_allowed: bool
    conclusion_generation_allowed: bool
    invocation_step_hash: str


@dataclass(frozen=True)
class ControlledScientificReasoningInvocationManifest:
    manifest_id: str
    source_activation_package_id: str
    source_activation_hash: str
    source_activation_token: str
    source_authorization_hash: str
    source_session_id: str
    source_session_hash: str
    source_manifest_id: str
    source_manifest_hash: str
    frozen_evidence_set_id: str
    frozen_evidence_set_hash: str
    invocation_steps: tuple[ControlledReasoningInvocationStep, ...]
    deterministic_execution_order: tuple[str, ...]
    invocation_step_count: int
    invocation_scope: str
    invocation_status: str
    invocation_manifest_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    authorization_consumed: bool
    activation_verified: bool
    invocation_manifest_materialized: bool
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


def build_controlled_scientific_reasoning_invocation_manifest(
    *,
    activation_package: ScientificReasoningSessionActivationPackage,
) -> ControlledScientificReasoningInvocationManifest:
    if not isinstance(
        activation_package,
        ScientificReasoningSessionActivationPackage,
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "source must be the canonical OII-013 activation package"
        )

    try:
        verify_scientific_reasoning_session_activation_package(
            activation_package
        )
    except Exception as exc:
        raise OracleControlledReasoningInvocationInvariantError(
            "OII-013 activation package verification failed"
        ) from exc

    if activation_package.authorization_consumed is not True:
        raise OracleControlledReasoningInvocationInvariantError(
            "authorization consumption was not verified"
        )
    if activation_package.activation_materialized is not True:
        raise OracleControlledReasoningInvocationInvariantError(
            "activation package was not materialized"
        )
    if activation_package.invocation_manifest_allowed is not True:
        raise OracleControlledReasoningInvocationInvariantError(
            "activation package does not allow invocation-manifest creation"
        )
    if (
        activation_package.activation_status
        != "activated_for_controlled_invocation_manifest"
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "activation status is not invocation-manifest eligible"
        )
    if activation_package.blocked_discipline_count != 0:
        raise OracleControlledReasoningInvocationInvariantError(
            "activation package contains blocked disciplines"
        )

    forbidden = (
        activation_package.reasoning_execution_allowed,
        activation_package.probability_estimation_allowed,
        activation_package.final_intelligence_conclusion_allowed,
        activation_package.publication_allowed,
        activation_package.alerting_allowed,
        activation_package.qseries_handoff_allowed,
        activation_package.qseries_execution_allowed,
        activation_package.order_creation_allowed,
        activation_package.funds_movement_allowed,
        activation_package.portfolio_mutation_allowed,
    )
    if activation_package.read_only is not True or any(forbidden):
        raise OracleControlledReasoningInvocationInvariantError(
            "OII-013 activation package violates permanent safety boundary"
        )

    steps: list[ControlledReasoningInvocationStep] = []
    for activation in activation_package.discipline_activations:
        eligible = (
            activation.activation_status
            == "activated_for_invocation_manifest"
            and activation.source_session_hash
            == activation_package.source_session_hash
            and activation.source_manifest_hash
            == activation_package.source_manifest_hash
            and activation.frozen_evidence_set_hash
            == activation_package.frozen_evidence_set_hash
        )
        if not eligible:
            raise OracleControlledReasoningInvocationInvariantError(
                "discipline activation is not eligible for manifest materialization"
            )

        body = {
            "discipline_activation_id":
                activation.discipline_activation_id,
            "discipline_name": activation.discipline_name,
            "ordinal": activation.ordinal,
            "source_activation_record_hash":
                activation.activation_record_hash,
            "source_session_hash": activation.source_session_hash,
            "source_manifest_hash": activation.source_manifest_hash,
            "frozen_evidence_set_hash":
                activation.frozen_evidence_set_hash,
            "invocation_mode": "read_only_contract_only",
            "invocation_status": "manifested_not_resolved_not_bound_not_executed",
            "callable_resolution_allowed": False,
            "callable_binding_allowed": False,
            "invocation_execution_allowed": False,
            "probability_estimation_allowed": False,
            "conclusion_generation_allowed": False,
        }
        step_hash = stable_hash(body)
        steps.append(
            ControlledReasoningInvocationStep(
                invocation_step_id=(
                    "controlled-reasoning-invocation-step:"
                    + activation.discipline_name
                    + ":"
                    + step_hash
                ),
                **body,
                invocation_step_hash=step_hash,
            )
        )

    step_tuple = tuple(sorted(steps, key=lambda item: item.ordinal))
    if tuple(item.discipline_name for item in step_tuple) != (
        activation_package.deterministic_execution_order
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "deterministic execution order was not preserved"
        )

    manifest_body = {
        "source_activation_package_id": activation_package.package_id,
        "source_activation_hash": activation_package.activation_hash,
        "source_activation_token": activation_package.activation_token,
        "source_authorization_hash":
            activation_package.source_authorization_hash,
        "source_session_id": activation_package.source_session_id,
        "source_session_hash": activation_package.source_session_hash,
        "source_manifest_id": activation_package.source_manifest_id,
        "source_manifest_hash": activation_package.source_manifest_hash,
        "frozen_evidence_set_id":
            activation_package.frozen_evidence_set_id,
        "frozen_evidence_set_hash":
            activation_package.frozen_evidence_set_hash,
        "invocation_steps": step_tuple,
        "deterministic_execution_order":
            activation_package.deterministic_execution_order,
        "invocation_step_count": len(step_tuple),
        "invocation_scope": "exact_oii013_activation_hash_only",
        "invocation_status":
            "controlled_manifest_materialized_not_resolved_not_bound_not_executed",
    }
    manifest_hash = stable_hash(manifest_body)

    return ControlledScientificReasoningInvocationManifest(
        manifest_id="controlled-reasoning-invocation-manifest:" + manifest_hash,
        **manifest_body,
        invocation_manifest_hash=manifest_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        authorization_consumed=True,
        activation_verified=True,
        invocation_manifest_materialized=True,
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


def verify_controlled_reasoning_invocation_step(
    step: ControlledReasoningInvocationStep,
) -> bool:
    if not isinstance(step, ControlledReasoningInvocationStep):
        raise OracleControlledReasoningInvocationInvariantError(
            "invalid OII-014 invocation step"
        )

    body = {
        key: value
        for key, value in asdict(step).items()
        if key not in {"invocation_step_id", "invocation_step_hash"}
    }
    if stable_hash(body) != step.invocation_step_hash:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-step hash verification failed"
        )
    expected_id = (
        "controlled-reasoning-invocation-step:"
        + step.discipline_name
        + ":"
        + step.invocation_step_hash
    )
    if step.invocation_step_id != expected_id:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-step identity verification failed"
        )

    forbidden = (
        step.callable_resolution_allowed,
        step.callable_binding_allowed,
        step.invocation_execution_allowed,
        step.probability_estimation_allowed,
        step.conclusion_generation_allowed,
    )
    if (
        step.invocation_mode != "read_only_contract_only"
        or step.invocation_status
        != "manifested_not_resolved_not_bound_not_executed"
        or any(forbidden)
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-step safety boundary violated"
        )
    return True


def verify_controlled_scientific_reasoning_invocation_manifest(
    manifest: ControlledScientificReasoningInvocationManifest,
) -> bool:
    if not isinstance(
        manifest,
        ControlledScientificReasoningInvocationManifest,
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "invalid OII-014 invocation manifest"
        )

    for step in manifest.invocation_steps:
        verify_controlled_reasoning_invocation_step(step)
        if (
            step.source_session_hash != manifest.source_session_hash
            or step.source_manifest_hash != manifest.source_manifest_hash
            or step.frozen_evidence_set_hash
            != manifest.frozen_evidence_set_hash
        ):
            raise OracleControlledReasoningInvocationInvariantError(
                "invocation-step lineage mismatch"
            )

    actual_order = tuple(
        step.discipline_name for step in manifest.invocation_steps
    )
    if actual_order != manifest.deterministic_execution_order:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-manifest execution-order mismatch"
        )

    expected_ordinals = tuple(range(1, len(manifest.invocation_steps) + 1))
    actual_ordinals = tuple(step.ordinal for step in manifest.invocation_steps)
    if actual_ordinals != expected_ordinals:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-step ordinals are not contiguous"
        )
    if manifest.invocation_step_count != len(manifest.invocation_steps):
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-step count mismatch"
        )
    if manifest.invocation_step_count <= 0:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation manifest is empty"
        )

    manifest_body = {
        "source_activation_package_id":
            manifest.source_activation_package_id,
        "source_activation_hash": manifest.source_activation_hash,
        "source_activation_token": manifest.source_activation_token,
        "source_authorization_hash": manifest.source_authorization_hash,
        "source_session_id": manifest.source_session_id,
        "source_session_hash": manifest.source_session_hash,
        "source_manifest_id": manifest.source_manifest_id,
        "source_manifest_hash": manifest.source_manifest_hash,
        "frozen_evidence_set_id": manifest.frozen_evidence_set_id,
        "frozen_evidence_set_hash": manifest.frozen_evidence_set_hash,
        "invocation_steps": manifest.invocation_steps,
        "deterministic_execution_order":
            manifest.deterministic_execution_order,
        "invocation_step_count": manifest.invocation_step_count,
        "invocation_scope": manifest.invocation_scope,
        "invocation_status": manifest.invocation_status,
    }
    if stable_hash(manifest_body) != manifest.invocation_manifest_hash:
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-manifest hash verification failed"
        )
    if manifest.manifest_id != (
        "controlled-reasoning-invocation-manifest:"
        + manifest.invocation_manifest_hash
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "invocation-manifest identity verification failed"
        )

    forbidden = (
        manifest.callable_resolution_allowed,
        manifest.callable_binding_allowed,
        manifest.reasoning_execution_allowed,
        manifest.probability_estimation_allowed,
        manifest.final_intelligence_conclusion_allowed,
        manifest.publication_allowed,
        manifest.alerting_allowed,
        manifest.qseries_handoff_allowed,
        manifest.qseries_execution_allowed,
        manifest.order_creation_allowed,
        manifest.funds_movement_allowed,
        manifest.portfolio_mutation_allowed,
    )
    if (
        manifest.read_only is not True
        or manifest.authorization_consumed is not True
        or manifest.activation_verified is not True
        or manifest.invocation_manifest_materialized is not True
        or manifest.invocation_scope
        != "exact_oii013_activation_hash_only"
        or manifest.invocation_status
        != "controlled_manifest_materialized_not_resolved_not_bound_not_executed"
        or any(forbidden)
    ):
        raise OracleControlledReasoningInvocationInvariantError(
            "OII-014 safety boundary violated"
        )
    return True


def serialize_controlled_scientific_reasoning_invocation_manifest(
    manifest: ControlledScientificReasoningInvocationManifest,
) -> str:
    verify_controlled_scientific_reasoning_invocation_manifest(manifest)
    return canonical_json(manifest)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ControlledReasoningInvocationStep",
    "ControlledScientificReasoningInvocationManifest",
    "OracleControlledReasoningInvocationInvariantError",
    "build_controlled_scientific_reasoning_invocation_manifest",
    "verify_controlled_reasoning_invocation_step",
    "verify_controlled_scientific_reasoning_invocation_manifest",
    "serialize_controlled_scientific_reasoning_invocation_manifest",
]
