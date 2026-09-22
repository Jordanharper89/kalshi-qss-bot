from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_session_orchestrator import (
    ScientificReasoningSession,
    verify_scientific_reasoning_session,
)

ENGINE_ID = "OII-011"
SCHEMA_VERSION = "OII-011.v1"
ALGORITHM_VERSION = "scientific-reasoning-session-readiness.v1"


class OracleScientificReasoningSessionReadinessInvariantError(ValueError):
    """Raised when an OII-011 session-readiness invariant is violated."""


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
class DisciplineReadinessAssessment:
    discipline_id: str
    discipline_name: str
    ordinal: int
    evidence_count: int
    evidence_set_hash: str
    source_manifest_hash: str
    materialization_verified: bool
    frozen_evidence_verified: bool
    deterministic_order_verified: bool
    execution_disabled_verified: bool
    probability_estimation_disabled_verified: bool
    conclusion_generation_disabled_verified: bool
    readiness_status: str
    readiness_reasons: tuple[str, ...]
    assessment_hash: str


@dataclass(frozen=True)
class ScientificReasoningSessionReadinessPackage:
    package_id: str
    source_session_id: str
    source_session_hash: str
    source_manifest_id: str
    source_manifest_hash: str
    frozen_evidence_set_id: str
    frozen_evidence_set_hash: str
    discipline_readiness_assessments: tuple[
        DisciplineReadinessAssessment, ...
    ]
    deterministic_execution_order: tuple[str, ...]
    ready_discipline_count: int
    blocked_discipline_count: int
    session_readiness_status: str
    readiness_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    session_readiness_verified: bool
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


def evaluate_scientific_reasoning_session_readiness(
    *,
    reasoning_session: ScientificReasoningSession,
) -> ScientificReasoningSessionReadinessPackage:
    if not isinstance(reasoning_session, ScientificReasoningSession):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "source must be the canonical OII-010 session"
        )

    try:
        verify_scientific_reasoning_session(reasoning_session)
    except Exception as exc:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "OII-010 session verification failed"
        ) from exc

    forbidden = (
        reasoning_session.reasoning_execution_allowed,
        reasoning_session.probability_estimation_allowed,
        reasoning_session.final_intelligence_conclusion_allowed,
        reasoning_session.publication_allowed,
        reasoning_session.alerting_allowed,
        reasoning_session.qseries_handoff_allowed,
        reasoning_session.qseries_execution_allowed,
        reasoning_session.order_creation_allowed,
        reasoning_session.funds_movement_allowed,
        reasoning_session.portfolio_mutation_allowed,
    )
    if (
        reasoning_session.read_only is not True
        or reasoning_session.evidence_set_frozen is not True
        or reasoning_session.session_materialized is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "OII-010 session violates permanent safety boundary"
        )

    frozen = reasoning_session.frozen_evidence_set
    expected_order = reasoning_session.deterministic_execution_order
    assessments: list[DisciplineReadinessAssessment] = []

    for discipline in reasoning_session.discipline_sessions:
        reasons: list[str] = []

        materialization_verified = (
            discipline.session_status == "materialized_not_executing"
        )
        if materialization_verified:
            reasons.append("discipline_session_materialized")

        frozen_evidence_verified = (
            discipline.evidence_input_hashes == frozen.evidence_input_hashes
            and discipline.evidence_count == frozen.evidence_count
            and discipline.evidence_count > 0
        )
        if frozen_evidence_verified:
            reasons.append("frozen_evidence_binding_verified")

        deterministic_order_verified = (
            1 <= discipline.ordinal <= len(expected_order)
            and expected_order[discipline.ordinal - 1]
            == discipline.discipline_name
        )
        if deterministic_order_verified:
            reasons.append("deterministic_execution_order_verified")

        execution_disabled_verified = discipline.execution_allowed is False
        if execution_disabled_verified:
            reasons.append("reasoning_execution_disabled")

        probability_disabled_verified = (
            discipline.probability_estimation_allowed is False
        )
        if probability_disabled_verified:
            reasons.append("probability_estimation_disabled")

        conclusion_disabled_verified = (
            discipline.conclusion_generation_allowed is False
        )
        if conclusion_disabled_verified:
            reasons.append("conclusion_generation_disabled")

        ready = all(
            (
                materialization_verified,
                frozen_evidence_verified,
                deterministic_order_verified,
                execution_disabled_verified,
                probability_disabled_verified,
                conclusion_disabled_verified,
            )
        )
        status = "ready_for_authorization_review" if ready else "blocked"

        body = {
            "discipline_id": discipline.discipline_id,
            "discipline_name": discipline.discipline_name,
            "ordinal": discipline.ordinal,
            "evidence_count": discipline.evidence_count,
            "evidence_set_hash": frozen.frozen_evidence_set_hash,
            "source_manifest_hash": discipline.source_manifest_hash,
            "materialization_verified": materialization_verified,
            "frozen_evidence_verified": frozen_evidence_verified,
            "deterministic_order_verified": deterministic_order_verified,
            "execution_disabled_verified": execution_disabled_verified,
            "probability_estimation_disabled_verified":
                probability_disabled_verified,
            "conclusion_generation_disabled_verified":
                conclusion_disabled_verified,
            "readiness_status": status,
            "readiness_reasons": tuple(reasons),
        }
        assessments.append(
            DisciplineReadinessAssessment(
                **body,
                assessment_hash=stable_hash(body),
            )
        )

    assessment_tuple = tuple(
        sorted(assessments, key=lambda item: item.ordinal)
    )
    ready_count = sum(
        item.readiness_status == "ready_for_authorization_review"
        for item in assessment_tuple
    )
    blocked_count = len(assessment_tuple) - ready_count

    session_status = (
        "ready_for_authorization_review"
        if assessment_tuple
        and blocked_count == 0
        and ready_count == len(assessment_tuple)
        else "blocked"
    )

    package_body = {
        "source_session_id": reasoning_session.session_id,
        "source_session_hash": reasoning_session.session_hash,
        "source_manifest_id":
            reasoning_session.source_reasoning_input_manifest_id,
        "source_manifest_hash":
            reasoning_session.source_reasoning_input_manifest_hash,
        "frozen_evidence_set_id": frozen.frozen_evidence_set_id,
        "frozen_evidence_set_hash": frozen.frozen_evidence_set_hash,
        "discipline_readiness_assessments": assessment_tuple,
        "deterministic_execution_order": expected_order,
        "ready_discipline_count": ready_count,
        "blocked_discipline_count": blocked_count,
        "session_readiness_status": session_status,
    }
    readiness_hash = stable_hash(package_body)

    return ScientificReasoningSessionReadinessPackage(
        package_id="scientific-reasoning-readiness:" + readiness_hash,
        **package_body,
        readiness_hash=readiness_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        session_readiness_verified=(session_status == "ready_for_authorization_review"),
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


def verify_scientific_reasoning_session_readiness_package(
    package: ScientificReasoningSessionReadinessPackage,
) -> bool:
    if not isinstance(package, ScientificReasoningSessionReadinessPackage):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "invalid OII-011 package type"
        )

    for item in package.discipline_readiness_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleScientificReasoningSessionReadinessInvariantError(
                "discipline readiness hash verification failed"
            )

    expected_order = tuple(
        item.discipline_name
        for item in package.discipline_readiness_assessments
    )
    if expected_order != package.deterministic_execution_order:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "readiness execution-order lineage mismatch"
        )

    expected_ordinals = tuple(
        range(1, len(package.discipline_readiness_assessments) + 1)
    )
    actual_ordinals = tuple(
        item.ordinal
        for item in package.discipline_readiness_assessments
    )
    if actual_ordinals != expected_ordinals:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "discipline readiness ordinals are not contiguous"
        )

    ready_count = sum(
        item.readiness_status == "ready_for_authorization_review"
        for item in package.discipline_readiness_assessments
    )
    blocked_count = sum(
        item.readiness_status == "blocked"
        for item in package.discipline_readiness_assessments
    )
    if ready_count != package.ready_discipline_count:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "ready discipline count mismatch"
        )
    if blocked_count != package.blocked_discipline_count:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "blocked discipline count mismatch"
        )

    expected_status = (
        "ready_for_authorization_review"
        if package.discipline_readiness_assessments
        and blocked_count == 0
        and ready_count == len(package.discipline_readiness_assessments)
        else "blocked"
    )
    if package.session_readiness_status != expected_status:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "session readiness status mismatch"
        )
    if package.session_readiness_verified != (
        expected_status == "ready_for_authorization_review"
    ):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "session readiness flag mismatch"
        )

    package_body = {
        "source_session_id": package.source_session_id,
        "source_session_hash": package.source_session_hash,
        "source_manifest_id": package.source_manifest_id,
        "source_manifest_hash": package.source_manifest_hash,
        "frozen_evidence_set_id": package.frozen_evidence_set_id,
        "frozen_evidence_set_hash": package.frozen_evidence_set_hash,
        "discipline_readiness_assessments":
            package.discipline_readiness_assessments,
        "deterministic_execution_order":
            package.deterministic_execution_order,
        "ready_discipline_count": package.ready_discipline_count,
        "blocked_discipline_count": package.blocked_discipline_count,
        "session_readiness_status": package.session_readiness_status,
    }
    if stable_hash(package_body) != package.readiness_hash:
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "readiness package hash verification failed"
        )
    if package.package_id != (
        "scientific-reasoning-readiness:" + package.readiness_hash
    ):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "readiness package identity verification failed"
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
    if package.read_only is not True or any(forbidden):
        raise OracleScientificReasoningSessionReadinessInvariantError(
            "OII-011 safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_session_readiness_package(
    package: ScientificReasoningSessionReadinessPackage,
) -> str:
    verify_scientific_reasoning_session_readiness_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "DisciplineReadinessAssessment",
    "ScientificReasoningSessionReadinessPackage",
    "OracleScientificReasoningSessionReadinessInvariantError",
    "evaluate_scientific_reasoning_session_readiness",
    "verify_scientific_reasoning_session_readiness_package",
    "serialize_scientific_reasoning_session_readiness_package",
]
