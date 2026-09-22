from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_provenance_confidence_engine import (
    ProvenanceConfidencePackage,
    verify_provenance_confidence_package,
)

ENGINE_ID = "OII-008"
SCHEMA_VERSION = "OII-008.v1"
ALGORITHM_VERSION = "certified-evidence-admission.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")

DEFAULT_MINIMUM_PROVENANCE_CONFIDENCE = Decimal("0.550000")
DEFAULT_MINIMUM_INFORMATION_GAIN = Decimal("0.300000")
DEFAULT_MAXIMUM_CIRCULARITY_PENALTY = Decimal("0.000000")


class OracleCertifiedEvidenceAdmissionInvariantError(ValueError):
    """Raised when an OII-008 certified-evidence invariant is violated."""


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
    if isinstance(value, Decimal):
        return format(value.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")
    if isinstance(value, float):
        return format(
            Decimal(str(value)).quantize(_QUANT, rounding=ROUND_HALF_EVEN),
            "f",
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


def _d(value: str | Decimal | int | float) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            f"invalid decimal value: {value!r}"
        ) from exc
    if result.is_nan() or result.is_infinite():
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "decimal values must be finite"
        )
    return result


def _q(value: Decimal) -> str:
    bounded = min(_ONE, max(_ZERO, value))
    return format(bounded.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


@dataclass(frozen=True)
class CertifiedEvidenceAdmissionPolicy:
    policy_id: str
    minimum_provenance_confidence_score: str
    minimum_information_gain_score: str
    maximum_circularity_penalty: str
    require_replay_integrity: bool
    require_lineage_integrity: bool
    require_source_traceability: bool
    reject_insufficient_confidence: bool
    policy_hash: str


@dataclass(frozen=True)
class CertifiedEvidenceAdmissionDecision:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    provenance_confidence_score: str
    information_gain_score: str
    source_traceability_score: str
    lineage_integrity_score: str
    replay_integrity_score: str
    circularity_penalty: str
    admission_status: str
    admission_reasons: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    certified_evidence_hash: str
    decision_hash: str


@dataclass(frozen=True)
class CertifiedEvidenceRecord:
    certified_evidence_id: str
    evidence_node_id: str
    evidence_id: str
    source_id: str
    provenance_confidence_score: str
    information_gain_score: str
    source_traceability_score: str
    lineage_integrity_score: str
    replay_integrity_score: str
    certification_basis: tuple[str, ...]
    source_package_id: str
    source_package_hash: str
    certification_hash: str


@dataclass(frozen=True)
class CertifiedEvidenceAdmissionPackage:
    package_id: str
    source_provenance_confidence_package_id: str
    source_provenance_confidence_package_hash: str
    admission_policy: CertifiedEvidenceAdmissionPolicy
    admission_decisions: tuple[CertifiedEvidenceAdmissionDecision, ...]
    certified_evidence_records: tuple[CertifiedEvidenceRecord, ...]
    admitted_evidence_count: int
    rejected_evidence_count: int
    admission_rate: str
    package_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    publication_allowed: bool
    alerting_allowed: bool
    final_intelligence_conclusion_allowed: bool
    probability_estimation_allowed: bool
    reasoning_consumption_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def build_certified_evidence_admission_policy(
    *,
    minimum_provenance_confidence_score: str | Decimal = DEFAULT_MINIMUM_PROVENANCE_CONFIDENCE,
    minimum_information_gain_score: str | Decimal = DEFAULT_MINIMUM_INFORMATION_GAIN,
    maximum_circularity_penalty: str | Decimal = DEFAULT_MAXIMUM_CIRCULARITY_PENALTY,
    require_replay_integrity: bool = True,
    require_lineage_integrity: bool = True,
    require_source_traceability: bool = True,
    reject_insufficient_confidence: bool = True,
) -> CertifiedEvidenceAdmissionPolicy:
    provenance = _d(minimum_provenance_confidence_score)
    information_gain = _d(minimum_information_gain_score)
    circularity = _d(maximum_circularity_penalty)

    for name, value in (
        ("minimum_provenance_confidence_score", provenance),
        ("minimum_information_gain_score", information_gain),
        ("maximum_circularity_penalty", circularity),
    ):
        if value < _ZERO or value > _ONE:
            raise OracleCertifiedEvidenceAdmissionInvariantError(
                f"{name} must be within [0,1]"
            )

    body = {
        "minimum_provenance_confidence_score": _q(provenance),
        "minimum_information_gain_score": _q(information_gain),
        "maximum_circularity_penalty": _q(circularity),
        "require_replay_integrity": bool(require_replay_integrity),
        "require_lineage_integrity": bool(require_lineage_integrity),
        "require_source_traceability": bool(require_source_traceability),
        "reject_insufficient_confidence": bool(reject_insufficient_confidence),
    }
    policy_hash = stable_hash(body)
    return CertifiedEvidenceAdmissionPolicy(
        policy_id="certified-evidence-policy:" + policy_hash,
        **body,
        policy_hash=policy_hash,
    )


def certify_evidence_for_reasoning(
    *,
    provenance_confidence_package: ProvenanceConfidencePackage,
    policy: CertifiedEvidenceAdmissionPolicy | None = None,
) -> CertifiedEvidenceAdmissionPackage:
    if not isinstance(provenance_confidence_package, ProvenanceConfidencePackage):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "source must be the canonical OII-007 package"
        )

    try:
        verify_provenance_confidence_package(provenance_confidence_package)
    except Exception as exc:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "OII-007 package verification failed"
        ) from exc

    forbidden = (
        provenance_confidence_package.publication_allowed,
        provenance_confidence_package.alerting_allowed,
        provenance_confidence_package.final_intelligence_conclusion_allowed,
        provenance_confidence_package.probability_estimation_allowed,
        provenance_confidence_package.qseries_handoff_allowed,
        provenance_confidence_package.qseries_execution_allowed,
        provenance_confidence_package.order_creation_allowed,
        provenance_confidence_package.funds_movement_allowed,
        provenance_confidence_package.portfolio_mutation_allowed,
    )
    if provenance_confidence_package.read_only is not True or any(forbidden):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "OII-007 package violates permanent safety boundary"
        )

    policy = policy or build_certified_evidence_admission_policy()
    if not isinstance(policy, CertifiedEvidenceAdmissionPolicy):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "invalid OII-008 admission policy"
        )

    policy_body = {
        key: value
        for key, value in asdict(policy).items()
        if key not in {"policy_id", "policy_hash"}
    }
    if stable_hash(policy_body) != policy.policy_hash:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "admission policy hash verification failed"
        )
    if policy.policy_id != "certified-evidence-policy:" + policy.policy_hash:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "admission policy identity verification failed"
        )

    minimum_confidence = _d(policy.minimum_provenance_confidence_score)
    minimum_gain = _d(policy.minimum_information_gain_score)
    maximum_circularity = _d(policy.maximum_circularity_penalty)

    decisions: list[CertifiedEvidenceAdmissionDecision] = []
    records: list[CertifiedEvidenceRecord] = []

    for assessment in sorted(
        provenance_confidence_package.evidence_confidence_assessments,
        key=lambda item: item.evidence_node_id,
    ):
        confidence = _d(assessment.provenance_confidence_score)
        information_gain = _d(assessment.information_gain_score)
        traceability = _d(assessment.source_traceability_score)
        lineage = _d(assessment.lineage_integrity_score)
        replay = _d(assessment.replay_integrity_score)
        circularity = _d(assessment.circularity_penalty)

        reasons: list[str] = []
        rejections: list[str] = []

        if confidence >= minimum_confidence:
            reasons.append("minimum_provenance_confidence_satisfied")
        else:
            rejections.append("provenance_confidence_below_minimum")

        if information_gain >= minimum_gain:
            reasons.append("minimum_information_gain_satisfied")
        else:
            rejections.append("information_gain_below_minimum")

        if circularity <= maximum_circularity:
            reasons.append("circularity_within_policy")
        else:
            rejections.append("circularity_exceeds_policy")

        if policy.require_replay_integrity:
            if replay >= Decimal("0.999999"):
                reasons.append("replay_integrity_verified")
            else:
                rejections.append("replay_integrity_not_verified")

        if policy.require_lineage_integrity:
            if lineage >= Decimal("0.550000"):
                reasons.append("lineage_integrity_verified")
            else:
                rejections.append("lineage_integrity_insufficient")

        if policy.require_source_traceability:
            if traceability >= Decimal("0.400000"):
                reasons.append("source_traceability_verified")
            else:
                rejections.append("source_traceability_insufficient")

        if (
            policy.reject_insufficient_confidence
            and assessment.provenance_confidence_classification
            == "insufficient_provenance_confidence"
        ):
            rejections.append("insufficient_confidence_classification")

        admitted = not rejections
        admission_status = (
            "certified_for_reasoning"
            if admitted
            else "rejected_from_reasoning"
        )

        certified_evidence_hash = stable_hash(
            {
                "evidence_node_id": assessment.evidence_node_id,
                "evidence_id": assessment.evidence_id,
                "source_id": assessment.source_id,
                "source_package_id": provenance_confidence_package.package_id,
                "source_package_hash": provenance_confidence_package.package_hash,
                "policy_hash": policy.policy_hash,
            }
        )

        decision_body = {
            "evidence_node_id": assessment.evidence_node_id,
            "evidence_id": assessment.evidence_id,
            "source_id": assessment.source_id,
            "provenance_confidence_score": assessment.provenance_confidence_score,
            "information_gain_score": assessment.information_gain_score,
            "source_traceability_score": assessment.source_traceability_score,
            "lineage_integrity_score": assessment.lineage_integrity_score,
            "replay_integrity_score": assessment.replay_integrity_score,
            "circularity_penalty": assessment.circularity_penalty,
            "admission_status": admission_status,
            "admission_reasons": tuple(reasons),
            "rejection_reasons": tuple(rejections),
            "certified_evidence_hash": certified_evidence_hash,
        }
        decision = CertifiedEvidenceAdmissionDecision(
            **decision_body,
            decision_hash=stable_hash(decision_body),
        )
        decisions.append(decision)

        if admitted:
            certification_body = {
                "evidence_node_id": assessment.evidence_node_id,
                "evidence_id": assessment.evidence_id,
                "source_id": assessment.source_id,
                "provenance_confidence_score":
                    assessment.provenance_confidence_score,
                "information_gain_score": assessment.information_gain_score,
                "source_traceability_score":
                    assessment.source_traceability_score,
                "lineage_integrity_score":
                    assessment.lineage_integrity_score,
                "replay_integrity_score":
                    assessment.replay_integrity_score,
                "certification_basis": tuple(reasons),
                "source_package_id":
                    provenance_confidence_package.package_id,
                "source_package_hash":
                    provenance_confidence_package.package_hash,
            }
            certification_hash = stable_hash(certification_body)
            records.append(
                CertifiedEvidenceRecord(
                    certified_evidence_id=
                        "certified-evidence:" + certification_hash,
                    **certification_body,
                    certification_hash=certification_hash,
                )
            )

    decisions_tuple = tuple(
        sorted(decisions, key=lambda item: item.evidence_node_id)
    )
    records_tuple = tuple(
        sorted(records, key=lambda item: item.evidence_node_id)
    )
    admitted_count = len(records_tuple)
    rejected_count = len(decisions_tuple) - admitted_count
    admission_rate = (
        Decimal(admitted_count) / Decimal(len(decisions_tuple))
        if decisions_tuple
        else _ZERO
    )

    package_body = {
        "source_provenance_confidence_package_id":
            provenance_confidence_package.package_id,
        "source_provenance_confidence_package_hash":
            provenance_confidence_package.package_hash,
        "admission_policy": policy,
        "admission_decisions": decisions_tuple,
        "certified_evidence_records": records_tuple,
        "admitted_evidence_count": admitted_count,
        "rejected_evidence_count": rejected_count,
        "admission_rate": _q(admission_rate),
    }
    package_hash = stable_hash(package_body)

    return CertifiedEvidenceAdmissionPackage(
        package_id="certified-evidence-admission:" + package_hash,
        **package_body,
        package_hash=package_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        publication_allowed=False,
        alerting_allowed=False,
        final_intelligence_conclusion_allowed=False,
        probability_estimation_allowed=False,
        reasoning_consumption_allowed=True,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def verify_certified_evidence_admission_package(
    package: CertifiedEvidenceAdmissionPackage,
) -> bool:
    if not isinstance(package, CertifiedEvidenceAdmissionPackage):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "invalid OII-008 package type"
        )

    policy_body = {
        key: value
        for key, value in asdict(package.admission_policy).items()
        if key not in {"policy_id", "policy_hash"}
    }
    if stable_hash(policy_body) != package.admission_policy.policy_hash:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "policy hash verification failed"
        )

    for decision in package.admission_decisions:
        body = {
            key: value
            for key, value in asdict(decision).items()
            if key != "decision_hash"
        }
        if stable_hash(body) != decision.decision_hash:
            raise OracleCertifiedEvidenceAdmissionInvariantError(
                "admission decision hash verification failed"
            )

    for record in package.certified_evidence_records:
        body = {
            key: value
            for key, value in asdict(record).items()
            if key not in {"certified_evidence_id", "certification_hash"}
        }
        if stable_hash(body) != record.certification_hash:
            raise OracleCertifiedEvidenceAdmissionInvariantError(
                "certified evidence hash verification failed"
            )
        if (
            record.certified_evidence_id
            != "certified-evidence:" + record.certification_hash
        ):
            raise OracleCertifiedEvidenceAdmissionInvariantError(
                "certified evidence identity verification failed"
            )

    admitted = sum(
        decision.admission_status == "certified_for_reasoning"
        for decision in package.admission_decisions
    )
    rejected = sum(
        decision.admission_status == "rejected_from_reasoning"
        for decision in package.admission_decisions
    )
    if admitted != package.admitted_evidence_count:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "admitted evidence count mismatch"
        )
    if rejected != package.rejected_evidence_count:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "rejected evidence count mismatch"
        )
    if admitted != len(package.certified_evidence_records):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "certified record count mismatch"
        )

    package_body = {
        "source_provenance_confidence_package_id":
            package.source_provenance_confidence_package_id,
        "source_provenance_confidence_package_hash":
            package.source_provenance_confidence_package_hash,
        "admission_policy": package.admission_policy,
        "admission_decisions": package.admission_decisions,
        "certified_evidence_records": package.certified_evidence_records,
        "admitted_evidence_count": package.admitted_evidence_count,
        "rejected_evidence_count": package.rejected_evidence_count,
        "admission_rate": package.admission_rate,
    }
    if stable_hash(package_body) != package.package_hash:
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "package hash verification failed"
        )
    if package.package_id != (
        "certified-evidence-admission:" + package.package_hash
    ):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "package identity verification failed"
        )

    forbidden = (
        package.publication_allowed,
        package.alerting_allowed,
        package.final_intelligence_conclusion_allowed,
        package.probability_estimation_allowed,
        package.qseries_handoff_allowed,
        package.qseries_execution_allowed,
        package.order_creation_allowed,
        package.funds_movement_allowed,
        package.portfolio_mutation_allowed,
    )
    if (
        package.read_only is not True
        or package.reasoning_consumption_allowed is not True
        or any(forbidden)
    ):
        raise OracleCertifiedEvidenceAdmissionInvariantError(
            "OII-008 safety boundary violated"
        )
    return True


def serialize_certified_evidence_admission_package(
    package: CertifiedEvidenceAdmissionPackage,
) -> str:
    verify_certified_evidence_admission_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "CertifiedEvidenceAdmissionPolicy",
    "CertifiedEvidenceAdmissionDecision",
    "CertifiedEvidenceRecord",
    "CertifiedEvidenceAdmissionPackage",
    "OracleCertifiedEvidenceAdmissionInvariantError",
    "build_certified_evidence_admission_policy",
    "certify_evidence_for_reasoning",
    "verify_certified_evidence_admission_package",
    "serialize_certified_evidence_admission_package",
]
