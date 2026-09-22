from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_session_authorization_gate import (
    ScientificReasoningSessionAuthorizationPackage,
    verify_scientific_reasoning_session_authorization_package,
)

ENGINE_ID = "OII-013"
SCHEMA_VERSION = "OII-013.v1"
ALGORITHM_VERSION = "scientific-reasoning-authorization-consumption-activation.v1"


class OracleScientificReasoningActivationInvariantError(ValueError):
    """Raised when an OII-013 activation invariant is violated."""


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
class DisciplineActivationRecord:
    discipline_activation_id: str
    discipline_authorization_id: str
    discipline_name: str
    ordinal: int
    source_authorization_record_hash: str
    source_session_hash: str
    source_manifest_hash: str
    frozen_evidence_set_hash: str
    activation_status: str
    activation_reasons: tuple[str, ...]
    activation_record_hash: str


@dataclass(frozen=True)
class ScientificReasoningAuthorizationConsumptionReceipt:
    receipt_id: str
    source_authorization_package_id: str
    source_authorization_hash: str
    authorization_token: str
    source_session_id: str
    source_session_hash: str
    frozen_evidence_set_hash: str
    single_use_enforced: bool
    consumed: bool
    consumption_status: str
    consumption_hash: str


@dataclass(frozen=True)
class ScientificReasoningSessionActivationPackage:
    package_id: str
    source_authorization_package_id: str
    source_authorization_hash: str
    source_session_id: str
    source_session_hash: str
    source_manifest_id: str
    source_manifest_hash: str
    frozen_evidence_set_id: str
    frozen_evidence_set_hash: str
    authorization_consumption_receipt: ScientificReasoningAuthorizationConsumptionReceipt
    discipline_activations: tuple[DisciplineActivationRecord, ...]
    deterministic_execution_order: tuple[str, ...]
    activated_discipline_count: int
    blocked_discipline_count: int
    activation_status: str
    activation_token: str
    activation_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    authorization_consumed: bool
    activation_materialized: bool
    invocation_manifest_allowed: bool
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


def consume_and_activate_scientific_reasoning_authorization(
    *,
    authorization_package: ScientificReasoningSessionAuthorizationPackage,
) -> ScientificReasoningSessionActivationPackage:
    if not isinstance(
        authorization_package,
        ScientificReasoningSessionAuthorizationPackage,
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "source must be the canonical OII-012 authorization package"
        )

    try:
        verify_scientific_reasoning_session_authorization_package(
            authorization_package
        )
    except Exception as exc:
        raise OracleScientificReasoningActivationInvariantError(
            "OII-012 authorization package verification failed"
        ) from exc

    if authorization_package.authorization_issued is not True:
        raise OracleScientificReasoningActivationInvariantError(
            "authorization was not issued"
        )
    if authorization_package.authorization_single_use is not True:
        raise OracleScientificReasoningActivationInvariantError(
            "authorization is not single use"
        )
    if authorization_package.authorization_consumed is not False:
        raise OracleScientificReasoningActivationInvariantError(
            "authorization was already consumed"
        )
    if (
        authorization_package.session_authorization_status
        != "authorized_for_single_use_activation"
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "authorization package is not activation eligible"
        )
    if authorization_package.denied_discipline_count != 0:
        raise OracleScientificReasoningActivationInvariantError(
            "authorization package contains denied disciplines"
        )

    forbidden = (
        authorization_package.reasoning_execution_allowed,
        authorization_package.probability_estimation_allowed,
        authorization_package.final_intelligence_conclusion_allowed,
        authorization_package.publication_allowed,
        authorization_package.alerting_allowed,
        authorization_package.qseries_handoff_allowed,
        authorization_package.qseries_execution_allowed,
        authorization_package.order_creation_allowed,
        authorization_package.funds_movement_allowed,
        authorization_package.portfolio_mutation_allowed,
    )
    if authorization_package.read_only is not True or any(forbidden):
        raise OracleScientificReasoningActivationInvariantError(
            "OII-012 authorization package violates permanent safety boundary"
        )

    receipt_body = {
        "source_authorization_package_id":
            authorization_package.package_id,
        "source_authorization_hash":
            authorization_package.authorization_hash,
        "authorization_token":
            authorization_package.authorization_token,
        "source_session_id": authorization_package.source_session_id,
        "source_session_hash": authorization_package.source_session_hash,
        "frozen_evidence_set_hash":
            authorization_package.frozen_evidence_set_hash,
        "single_use_enforced": True,
        "consumed": True,
        "consumption_status": "consumed_for_exact_session_activation",
    }
    consumption_hash = stable_hash(receipt_body)
    receipt = ScientificReasoningAuthorizationConsumptionReceipt(
        receipt_id="scientific-reasoning-consumption:" + consumption_hash,
        **receipt_body,
        consumption_hash=consumption_hash,
    )

    records: list[DisciplineActivationRecord] = []
    for authorization in authorization_package.discipline_authorizations:
        reasons: list[str] = []

        eligible = (
            authorization.authorization_status
            == "authorized_for_activation_review"
            and authorization.source_session_hash
            == authorization_package.source_session_hash
            and authorization.source_manifest_hash
            == authorization_package.source_manifest_hash
            and authorization.frozen_evidence_set_hash
            == authorization_package.frozen_evidence_set_hash
        )
        if eligible:
            reasons.extend(
                (
                    "authorization_record_verified",
                    "exact_session_scope_verified",
                    "frozen_evidence_lineage_verified",
                    "single_use_consumption_verified",
                )
            )
        status = "activated_for_invocation_manifest" if eligible else "blocked"

        body = {
            "discipline_authorization_id":
                authorization.discipline_authorization_id,
            "discipline_name": authorization.discipline_name,
            "ordinal": authorization.ordinal,
            "source_authorization_record_hash":
                authorization.authorization_record_hash,
            "source_session_hash": authorization.source_session_hash,
            "source_manifest_hash": authorization.source_manifest_hash,
            "frozen_evidence_set_hash":
                authorization.frozen_evidence_set_hash,
            "activation_status": status,
            "activation_reasons": tuple(reasons),
        }
        record_hash = stable_hash(body)
        records.append(
            DisciplineActivationRecord(
                discipline_activation_id=(
                    "discipline-activation:"
                    + authorization.discipline_name
                    + ":"
                    + record_hash
                ),
                **body,
                activation_record_hash=record_hash,
            )
        )

    record_tuple = tuple(sorted(records, key=lambda item: item.ordinal))
    activated_count = sum(
        item.activation_status == "activated_for_invocation_manifest"
        for item in record_tuple
    )
    blocked_count = len(record_tuple) - activated_count
    fully_activated = (
        record_tuple
        and blocked_count == 0
        and activated_count == len(record_tuple)
    )
    activation_status = (
        "activated_for_controlled_invocation_manifest"
        if fully_activated
        else "blocked"
    )

    activation_token_body = {
        "source_authorization_hash":
            authorization_package.authorization_hash,
        "authorization_consumption_hash": receipt.consumption_hash,
        "source_session_hash": authorization_package.source_session_hash,
        "frozen_evidence_set_hash":
            authorization_package.frozen_evidence_set_hash,
        "discipline_activation_hashes": tuple(
            item.activation_record_hash for item in record_tuple
        ),
        "deterministic_execution_order":
            authorization_package.deterministic_execution_order,
    }
    activation_token = stable_hash(activation_token_body)

    package_body = {
        "source_authorization_package_id":
            authorization_package.package_id,
        "source_authorization_hash":
            authorization_package.authorization_hash,
        "source_session_id": authorization_package.source_session_id,
        "source_session_hash": authorization_package.source_session_hash,
        "source_manifest_id": authorization_package.source_manifest_id,
        "source_manifest_hash": authorization_package.source_manifest_hash,
        "frozen_evidence_set_id":
            authorization_package.frozen_evidence_set_id,
        "frozen_evidence_set_hash":
            authorization_package.frozen_evidence_set_hash,
        "authorization_consumption_receipt": receipt,
        "discipline_activations": record_tuple,
        "deterministic_execution_order":
            authorization_package.deterministic_execution_order,
        "activated_discipline_count": activated_count,
        "blocked_discipline_count": blocked_count,
        "activation_status": activation_status,
        "activation_token": activation_token,
    }
    activation_hash = stable_hash(package_body)

    return ScientificReasoningSessionActivationPackage(
        package_id="scientific-reasoning-activation:" + activation_hash,
        **package_body,
        activation_hash=activation_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        authorization_consumed=True,
        activation_materialized=fully_activated,
        invocation_manifest_allowed=fully_activated,
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


def verify_scientific_reasoning_authorization_consumption_receipt(
    receipt: ScientificReasoningAuthorizationConsumptionReceipt,
) -> bool:
    if not isinstance(
        receipt,
        ScientificReasoningAuthorizationConsumptionReceipt,
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "invalid OII-013 consumption receipt"
        )
    body = {
        key: value
        for key, value in asdict(receipt).items()
        if key not in {"receipt_id", "consumption_hash"}
    }
    if stable_hash(body) != receipt.consumption_hash:
        raise OracleScientificReasoningActivationInvariantError(
            "authorization consumption hash verification failed"
        )
    if receipt.receipt_id != (
        "scientific-reasoning-consumption:" + receipt.consumption_hash
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "authorization consumption identity verification failed"
        )
    if (
        receipt.single_use_enforced is not True
        or receipt.consumed is not True
        or receipt.consumption_status
        != "consumed_for_exact_session_activation"
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "authorization consumption semantics violated"
        )
    return True


def verify_scientific_reasoning_session_activation_package(
    package: ScientificReasoningSessionActivationPackage,
) -> bool:
    if not isinstance(package, ScientificReasoningSessionActivationPackage):
        raise OracleScientificReasoningActivationInvariantError(
            "invalid OII-013 activation package"
        )

    verify_scientific_reasoning_authorization_consumption_receipt(
        package.authorization_consumption_receipt
    )

    receipt = package.authorization_consumption_receipt
    if (
        receipt.source_authorization_package_id
        != package.source_authorization_package_id
        or receipt.source_authorization_hash
        != package.source_authorization_hash
        or receipt.source_session_hash != package.source_session_hash
        or receipt.frozen_evidence_set_hash
        != package.frozen_evidence_set_hash
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "consumption receipt lineage mismatch"
        )

    for record in package.discipline_activations:
        body = {
            key: value
            for key, value in asdict(record).items()
            if key not in {
                "discipline_activation_id",
                "activation_record_hash",
            }
        }
        if stable_hash(body) != record.activation_record_hash:
            raise OracleScientificReasoningActivationInvariantError(
                "discipline activation hash verification failed"
            )
        expected_id = (
            "discipline-activation:"
            + record.discipline_name
            + ":"
            + record.activation_record_hash
        )
        if record.discipline_activation_id != expected_id:
            raise OracleScientificReasoningActivationInvariantError(
                "discipline activation identity verification failed"
            )
        if (
            record.source_session_hash != package.source_session_hash
            or record.source_manifest_hash != package.source_manifest_hash
            or record.frozen_evidence_set_hash
            != package.frozen_evidence_set_hash
        ):
            raise OracleScientificReasoningActivationInvariantError(
                "discipline activation lineage mismatch"
            )

    actual_order = tuple(
        item.discipline_name for item in package.discipline_activations
    )
    if actual_order != package.deterministic_execution_order:
        raise OracleScientificReasoningActivationInvariantError(
            "activation execution-order lineage mismatch"
        )

    expected_ordinals = tuple(
        range(1, len(package.discipline_activations) + 1)
    )
    actual_ordinals = tuple(
        item.ordinal for item in package.discipline_activations
    )
    if actual_ordinals != expected_ordinals:
        raise OracleScientificReasoningActivationInvariantError(
            "activation discipline ordinals are not contiguous"
        )

    activated_count = sum(
        item.activation_status == "activated_for_invocation_manifest"
        for item in package.discipline_activations
    )
    blocked_count = sum(
        item.activation_status == "blocked"
        for item in package.discipline_activations
    )
    if activated_count != package.activated_discipline_count:
        raise OracleScientificReasoningActivationInvariantError(
            "activated discipline count mismatch"
        )
    if blocked_count != package.blocked_discipline_count:
        raise OracleScientificReasoningActivationInvariantError(
            "blocked discipline count mismatch"
        )

    expected_status = (
        "activated_for_controlled_invocation_manifest"
        if package.discipline_activations
        and blocked_count == 0
        and activated_count == len(package.discipline_activations)
        else "blocked"
    )
    if package.activation_status != expected_status:
        raise OracleScientificReasoningActivationInvariantError(
            "activation status mismatch"
        )

    activation_token_body = {
        "source_authorization_hash": package.source_authorization_hash,
        "authorization_consumption_hash": receipt.consumption_hash,
        "source_session_hash": package.source_session_hash,
        "frozen_evidence_set_hash": package.frozen_evidence_set_hash,
        "discipline_activation_hashes": tuple(
            item.activation_record_hash
            for item in package.discipline_activations
        ),
        "deterministic_execution_order":
            package.deterministic_execution_order,
    }
    if stable_hash(activation_token_body) != package.activation_token:
        raise OracleScientificReasoningActivationInvariantError(
            "activation token verification failed"
        )

    package_body = {
        "source_authorization_package_id":
            package.source_authorization_package_id,
        "source_authorization_hash": package.source_authorization_hash,
        "source_session_id": package.source_session_id,
        "source_session_hash": package.source_session_hash,
        "source_manifest_id": package.source_manifest_id,
        "source_manifest_hash": package.source_manifest_hash,
        "frozen_evidence_set_id": package.frozen_evidence_set_id,
        "frozen_evidence_set_hash": package.frozen_evidence_set_hash,
        "authorization_consumption_receipt":
            package.authorization_consumption_receipt,
        "discipline_activations": package.discipline_activations,
        "deterministic_execution_order":
            package.deterministic_execution_order,
        "activated_discipline_count": package.activated_discipline_count,
        "blocked_discipline_count": package.blocked_discipline_count,
        "activation_status": package.activation_status,
        "activation_token": package.activation_token,
    }
    if stable_hash(package_body) != package.activation_hash:
        raise OracleScientificReasoningActivationInvariantError(
            "activation package hash verification failed"
        )
    if package.package_id != (
        "scientific-reasoning-activation:" + package.activation_hash
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "activation package identity verification failed"
        )

    expected_active = (
        expected_status == "activated_for_controlled_invocation_manifest"
    )
    forbidden = (
        package.reasoning_execution_allowed,
        package.probability_estimation_allowed,
        package.final_intelligence_conclusion_allowed,
        package.publication_allowed,
        package.alerting_allowed,
        package.qseries_handoff_allowed,
        package.qseries_execution_allowed,
        package.order_creation_allowed,
        package.funds_movement_allowed,
        package.portfolio_mutation_allowed,
    )
    if (
        package.read_only is not True
        or package.authorization_consumed is not True
        or package.activation_materialized != expected_active
        or package.invocation_manifest_allowed != expected_active
        or any(forbidden)
    ):
        raise OracleScientificReasoningActivationInvariantError(
            "OII-013 safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_session_activation_package(
    package: ScientificReasoningSessionActivationPackage,
) -> str:
    verify_scientific_reasoning_session_activation_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "DisciplineActivationRecord",
    "ScientificReasoningAuthorizationConsumptionReceipt",
    "ScientificReasoningSessionActivationPackage",
    "OracleScientificReasoningActivationInvariantError",
    "consume_and_activate_scientific_reasoning_authorization",
    "verify_scientific_reasoning_authorization_consumption_receipt",
    "verify_scientific_reasoning_session_activation_package",
    "serialize_scientific_reasoning_session_activation_package",
]
