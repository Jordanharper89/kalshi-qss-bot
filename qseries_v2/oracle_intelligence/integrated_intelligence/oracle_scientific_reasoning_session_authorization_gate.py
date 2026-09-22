from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_session_readiness_gate import (
    ScientificReasoningSessionReadinessPackage,
    verify_scientific_reasoning_session_readiness_package,
)

ENGINE_ID = "OII-012"
SCHEMA_VERSION = "OII-012.v1"
ALGORITHM_VERSION = "scientific-reasoning-session-authorization.v1"


class OracleScientificReasoningAuthorizationInvariantError(ValueError):
    """Raised when an OII-012 authorization invariant is violated."""


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
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
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
class ScientificReasoningAuthorizationPolicy:
    policy_id: str
    require_all_disciplines_ready: bool
    require_zero_blocked_disciplines: bool
    require_frozen_evidence_lineage: bool
    require_deterministic_execution_order: bool
    require_read_only_boundary: bool
    single_use_authorization: bool
    authorization_scope: str
    policy_hash: str


@dataclass(frozen=True)
class DisciplineAuthorizationRecord:
    discipline_authorization_id: str
    discipline_id: str
    discipline_name: str
    ordinal: int
    source_assessment_hash: str
    source_session_hash: str
    source_manifest_hash: str
    frozen_evidence_set_hash: str
    authorization_status: str
    authorization_reasons: tuple[str, ...]
    authorization_record_hash: str


@dataclass(frozen=True)
class ScientificReasoningSessionAuthorizationPackage:
    package_id: str
    source_readiness_package_id: str
    source_readiness_hash: str
    source_session_id: str
    source_session_hash: str
    source_manifest_id: str
    source_manifest_hash: str
    frozen_evidence_set_id: str
    frozen_evidence_set_hash: str
    authorization_policy: ScientificReasoningAuthorizationPolicy
    discipline_authorizations: tuple[DisciplineAuthorizationRecord, ...]
    deterministic_execution_order: tuple[str, ...]
    authorized_discipline_count: int
    denied_discipline_count: int
    session_authorization_status: str
    authorization_token: str
    authorization_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    authorization_issued: bool
    authorization_single_use: bool
    authorization_consumed: bool
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


def build_scientific_reasoning_authorization_policy() -> (
    ScientificReasoningAuthorizationPolicy
):
    body = {
        "require_all_disciplines_ready": True,
        "require_zero_blocked_disciplines": True,
        "require_frozen_evidence_lineage": True,
        "require_deterministic_execution_order": True,
        "require_read_only_boundary": True,
        "single_use_authorization": True,
        "authorization_scope": "exact_oii010_session_hash_only",
    }
    policy_hash = stable_hash(body)
    return ScientificReasoningAuthorizationPolicy(
        policy_id="scientific-reasoning-authorization-policy:" + policy_hash,
        **body,
        policy_hash=policy_hash,
    )


def authorize_scientific_reasoning_session(
    *,
    readiness_package: ScientificReasoningSessionReadinessPackage,
    policy: ScientificReasoningAuthorizationPolicy | None = None,
) -> ScientificReasoningSessionAuthorizationPackage:
    if not isinstance(
        readiness_package,
        ScientificReasoningSessionReadinessPackage,
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "source must be the canonical OII-011 readiness package"
        )

    try:
        verify_scientific_reasoning_session_readiness_package(readiness_package)
    except Exception as exc:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "OII-011 readiness package verification failed"
        ) from exc

    policy = policy or build_scientific_reasoning_authorization_policy()
    verify_scientific_reasoning_authorization_policy(policy)

    forbidden = (
        readiness_package.reasoning_execution_allowed,
        readiness_package.probability_estimation_allowed,
        readiness_package.final_intelligence_conclusion_allowed,
        readiness_package.publication_allowed,
        readiness_package.alerting_allowed,
        readiness_package.qseries_handoff_allowed,
        readiness_package.qseries_execution_allowed,
        readiness_package.order_creation_allowed,
        readiness_package.funds_movement_allowed,
        readiness_package.portfolio_mutation_allowed,
    )
    if readiness_package.read_only is not True or any(forbidden):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "OII-011 readiness package violates permanent safety boundary"
        )

    records: list[DisciplineAuthorizationRecord] = []
    for assessment in readiness_package.discipline_readiness_assessments:
        reasons: list[str] = []

        ready = (
            assessment.readiness_status == "ready_for_authorization_review"
            and assessment.materialization_verified
            and assessment.frozen_evidence_verified
            and assessment.deterministic_order_verified
            and assessment.execution_disabled_verified
            and assessment.probability_estimation_disabled_verified
            and assessment.conclusion_generation_disabled_verified
        )
        if ready:
            reasons.extend(
                (
                    "discipline_readiness_verified",
                    "frozen_evidence_binding_verified",
                    "deterministic_order_verified",
                    "execution_boundary_preserved",
                )
            )

        status = "authorized_for_activation_review" if ready else "denied"
        body = {
            "discipline_id": assessment.discipline_id,
            "discipline_name": assessment.discipline_name,
            "ordinal": assessment.ordinal,
            "source_assessment_hash": assessment.assessment_hash,
            "source_session_hash": readiness_package.source_session_hash,
            "source_manifest_hash": readiness_package.source_manifest_hash,
            "frozen_evidence_set_hash":
                readiness_package.frozen_evidence_set_hash,
            "authorization_status": status,
            "authorization_reasons": tuple(reasons),
        }
        record_hash = stable_hash(body)
        records.append(
            DisciplineAuthorizationRecord(
                discipline_authorization_id=(
                    "discipline-authorization:"
                    + assessment.discipline_name
                    + ":"
                    + record_hash
                ),
                **body,
                authorization_record_hash=record_hash,
            )
        )

    record_tuple = tuple(sorted(records, key=lambda item: item.ordinal))
    authorized_count = sum(
        item.authorization_status == "authorized_for_activation_review"
        for item in record_tuple
    )
    denied_count = len(record_tuple) - authorized_count

    session_authorized = (
        readiness_package.session_readiness_verified
        and readiness_package.session_readiness_status
        == "ready_for_authorization_review"
        and readiness_package.blocked_discipline_count == 0
        and record_tuple
        and denied_count == 0
        and authorized_count == len(record_tuple)
    )
    session_status = (
        "authorized_for_single_use_activation"
        if session_authorized
        else "denied"
    )

    authorization_token_body = {
        "source_session_hash": readiness_package.source_session_hash,
        "source_readiness_hash": readiness_package.readiness_hash,
        "frozen_evidence_set_hash":
            readiness_package.frozen_evidence_set_hash,
        "policy_hash": policy.policy_hash,
        "discipline_authorization_hashes": tuple(
            item.authorization_record_hash for item in record_tuple
        ),
        "single_use": policy.single_use_authorization,
    }
    authorization_token = stable_hash(authorization_token_body)

    package_body = {
        "source_readiness_package_id": readiness_package.package_id,
        "source_readiness_hash": readiness_package.readiness_hash,
        "source_session_id": readiness_package.source_session_id,
        "source_session_hash": readiness_package.source_session_hash,
        "source_manifest_id": readiness_package.source_manifest_id,
        "source_manifest_hash": readiness_package.source_manifest_hash,
        "frozen_evidence_set_id":
            readiness_package.frozen_evidence_set_id,
        "frozen_evidence_set_hash":
            readiness_package.frozen_evidence_set_hash,
        "authorization_policy": policy,
        "discipline_authorizations": record_tuple,
        "deterministic_execution_order":
            readiness_package.deterministic_execution_order,
        "authorized_discipline_count": authorized_count,
        "denied_discipline_count": denied_count,
        "session_authorization_status": session_status,
        "authorization_token": authorization_token,
    }
    authorization_hash = stable_hash(package_body)

    return ScientificReasoningSessionAuthorizationPackage(
        package_id="scientific-reasoning-authorization:" + authorization_hash,
        **package_body,
        authorization_hash=authorization_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        authorization_issued=session_authorized,
        authorization_single_use=True,
        authorization_consumed=False,
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


def verify_scientific_reasoning_authorization_policy(
    policy: ScientificReasoningAuthorizationPolicy,
) -> bool:
    if not isinstance(policy, ScientificReasoningAuthorizationPolicy):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "invalid OII-012 authorization policy"
        )
    body = {
        key: value
        for key, value in asdict(policy).items()
        if key not in {"policy_id", "policy_hash"}
    }
    if stable_hash(body) != policy.policy_hash:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization policy hash verification failed"
        )
    if policy.policy_id != (
        "scientific-reasoning-authorization-policy:" + policy.policy_hash
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization policy identity verification failed"
        )
    if (
        policy.require_all_disciplines_ready is not True
        or policy.require_zero_blocked_disciplines is not True
        or policy.require_frozen_evidence_lineage is not True
        or policy.require_deterministic_execution_order is not True
        or policy.require_read_only_boundary is not True
        or policy.single_use_authorization is not True
        or policy.authorization_scope
        != "exact_oii010_session_hash_only"
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization policy weakens mandatory safeguards"
        )
    return True


def verify_scientific_reasoning_session_authorization_package(
    package: ScientificReasoningSessionAuthorizationPackage,
) -> bool:
    if not isinstance(
        package,
        ScientificReasoningSessionAuthorizationPackage,
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "invalid OII-012 authorization package"
        )

    verify_scientific_reasoning_authorization_policy(
        package.authorization_policy
    )

    for record in package.discipline_authorizations:
        body = {
            key: value
            for key, value in asdict(record).items()
            if key not in {
                "discipline_authorization_id",
                "authorization_record_hash",
            }
        }
        if stable_hash(body) != record.authorization_record_hash:
            raise OracleScientificReasoningAuthorizationInvariantError(
                "discipline authorization hash verification failed"
            )
        expected_id = (
            "discipline-authorization:"
            + record.discipline_name
            + ":"
            + record.authorization_record_hash
        )
        if record.discipline_authorization_id != expected_id:
            raise OracleScientificReasoningAuthorizationInvariantError(
                "discipline authorization identity verification failed"
            )

    actual_order = tuple(
        item.discipline_name for item in package.discipline_authorizations
    )
    if actual_order != package.deterministic_execution_order:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization execution-order lineage mismatch"
        )

    authorized_count = sum(
        item.authorization_status == "authorized_for_activation_review"
        for item in package.discipline_authorizations
    )
    denied_count = sum(
        item.authorization_status == "denied"
        for item in package.discipline_authorizations
    )
    if authorized_count != package.authorized_discipline_count:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorized discipline count mismatch"
        )
    if denied_count != package.denied_discipline_count:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "denied discipline count mismatch"
        )

    token_body = {
        "source_session_hash": package.source_session_hash,
        "source_readiness_hash": package.source_readiness_hash,
        "frozen_evidence_set_hash": package.frozen_evidence_set_hash,
        "policy_hash": package.authorization_policy.policy_hash,
        "discipline_authorization_hashes": tuple(
            item.authorization_record_hash
            for item in package.discipline_authorizations
        ),
        "single_use": package.authorization_policy.single_use_authorization,
    }
    if stable_hash(token_body) != package.authorization_token:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization token verification failed"
        )

    expected_status = (
        "authorized_for_single_use_activation"
        if package.discipline_authorizations
        and denied_count == 0
        and authorized_count == len(package.discipline_authorizations)
        else "denied"
    )
    if package.session_authorization_status != expected_status:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "session authorization status mismatch"
        )
    if package.authorization_issued != (
        expected_status == "authorized_for_single_use_activation"
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization-issued flag mismatch"
        )

    package_body = {
        "source_readiness_package_id":
            package.source_readiness_package_id,
        "source_readiness_hash": package.source_readiness_hash,
        "source_session_id": package.source_session_id,
        "source_session_hash": package.source_session_hash,
        "source_manifest_id": package.source_manifest_id,
        "source_manifest_hash": package.source_manifest_hash,
        "frozen_evidence_set_id": package.frozen_evidence_set_id,
        "frozen_evidence_set_hash": package.frozen_evidence_set_hash,
        "authorization_policy": package.authorization_policy,
        "discipline_authorizations": package.discipline_authorizations,
        "deterministic_execution_order":
            package.deterministic_execution_order,
        "authorized_discipline_count":
            package.authorized_discipline_count,
        "denied_discipline_count": package.denied_discipline_count,
        "session_authorization_status":
            package.session_authorization_status,
        "authorization_token": package.authorization_token,
    }
    if stable_hash(package_body) != package.authorization_hash:
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization package hash verification failed"
        )
    if package.package_id != (
        "scientific-reasoning-authorization:" + package.authorization_hash
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "authorization package identity verification failed"
        )

    forbidden = (
        package.authorization_consumed,
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
        or package.authorization_single_use is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningAuthorizationInvariantError(
            "OII-012 safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_session_authorization_package(
    package: ScientificReasoningSessionAuthorizationPackage,
) -> str:
    verify_scientific_reasoning_session_authorization_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ScientificReasoningAuthorizationPolicy",
    "DisciplineAuthorizationRecord",
    "ScientificReasoningSessionAuthorizationPackage",
    "OracleScientificReasoningAuthorizationInvariantError",
    "build_scientific_reasoning_authorization_policy",
    "authorize_scientific_reasoning_session",
    "verify_scientific_reasoning_authorization_policy",
    "verify_scientific_reasoning_session_authorization_package",
    "serialize_scientific_reasoning_session_authorization_package",
]
