from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_certified_evidence_admission_gate import (
    CertifiedEvidenceAdmissionPackage,
    CertifiedEvidenceRecord,
    verify_certified_evidence_admission_package,
)

ENGINE_ID = "OII-009"
SCHEMA_VERSION = "OII-009.v1"
ALGORITHM_VERSION = "scientific-reasoning-input-manifest.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")

SUPPORTED_REASONING_DISCIPLINES = (
    "bayesian_inference",
    "causal_inference",
    "calibration_science",
    "consensus_reasoning",
    "decision_theory",
    "game_theory",
    "information_theory",
    "signal_detection",
    "adversarial_epistemology",
    "complex_systems",
)


class OracleScientificReasoningInputManifestInvariantError(ValueError):
    """Raised when an OII-009 reasoning-input invariant is violated."""


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
        raise OracleScientificReasoningInputManifestInvariantError(
            f"invalid decimal value: {value!r}"
        ) from exc
    if result.is_nan() or result.is_infinite():
        raise OracleScientificReasoningInputManifestInvariantError(
            "decimal values must be finite"
        )
    return result


def _q(value: Decimal) -> str:
    bounded = min(_ONE, max(_ZERO, value))
    return format(bounded.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


@dataclass(frozen=True)
class ScientificReasoningRequest:
    request_id: str
    subject_id: str
    question_text: str
    requested_disciplines: tuple[str, ...]
    requested_claim_ids: tuple[str, ...]
    request_context: tuple[tuple[str, str], ...]
    request_hash: str


@dataclass(frozen=True)
class ReasoningEvidenceInput:
    certified_evidence_id: str
    evidence_node_id: str
    evidence_id: str
    source_id: str
    provenance_confidence_score: str
    information_gain_score: str
    source_traceability_score: str
    lineage_integrity_score: str
    replay_integrity_score: str
    certification_hash: str
    evidence_weight: str
    admissible_disciplines: tuple[str, ...]
    input_hash: str


@dataclass(frozen=True)
class ScientificReasoningInputManifest:
    manifest_id: str
    source_certified_evidence_package_id: str
    source_certified_evidence_package_hash: str
    reasoning_request: ScientificReasoningRequest
    reasoning_evidence_inputs: tuple[ReasoningEvidenceInput, ...]
    selected_disciplines: tuple[str, ...]
    certified_evidence_count: int
    aggregate_evidence_weight: str
    mean_provenance_confidence_score: str
    mean_information_gain_score: str
    manifest_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    reasoning_input_ready: bool
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


def build_scientific_reasoning_request(
    *,
    subject_id: str,
    question_text: str,
    requested_disciplines: tuple[str, ...] | list[str],
    requested_claim_ids: tuple[str, ...] | list[str] = (),
    request_context: Mapping[str, Any] | None = None,
) -> ScientificReasoningRequest:
    subject = str(subject_id).strip()
    question = str(question_text).strip()
    if not subject:
        raise OracleScientificReasoningInputManifestInvariantError(
            "subject_id is required"
        )
    if not question:
        raise OracleScientificReasoningInputManifestInvariantError(
            "question_text is required"
        )

    disciplines = tuple(sorted({str(item).strip() for item in requested_disciplines}))
    if not disciplines:
        raise OracleScientificReasoningInputManifestInvariantError(
            "at least one reasoning discipline is required"
        )
    unsupported = tuple(
        item for item in disciplines if item not in SUPPORTED_REASONING_DISCIPLINES
    )
    if unsupported:
        raise OracleScientificReasoningInputManifestInvariantError(
            "unsupported reasoning disciplines: " + ", ".join(unsupported)
        )

    claims = tuple(sorted({str(item).strip() for item in requested_claim_ids if str(item).strip()}))
    context = tuple(
        sorted(
            (
                str(key),
                canonical_json(value),
            )
            for key, value in (request_context or {}).items()
        )
    )

    body = {
        "subject_id": subject,
        "question_text": question,
        "requested_disciplines": disciplines,
        "requested_claim_ids": claims,
        "request_context": context,
    }
    request_hash = stable_hash(body)
    return ScientificReasoningRequest(
        request_id="scientific-reasoning-request:" + request_hash,
        **body,
        request_hash=request_hash,
    )


def _verify_request(request: ScientificReasoningRequest) -> None:
    if not isinstance(request, ScientificReasoningRequest):
        raise OracleScientificReasoningInputManifestInvariantError(
            "invalid scientific reasoning request"
        )
    body = {
        key: value
        for key, value in asdict(request).items()
        if key not in {"request_id", "request_hash"}
    }
    if stable_hash(body) != request.request_hash:
        raise OracleScientificReasoningInputManifestInvariantError(
            "reasoning request hash verification failed"
        )
    if request.request_id != "scientific-reasoning-request:" + request.request_hash:
        raise OracleScientificReasoningInputManifestInvariantError(
            "reasoning request identity verification failed"
        )
    if not request.requested_disciplines:
        raise OracleScientificReasoningInputManifestInvariantError(
            "reasoning request has no disciplines"
        )
    unsupported = tuple(
        item
        for item in request.requested_disciplines
        if item not in SUPPORTED_REASONING_DISCIPLINES
    )
    if unsupported:
        raise OracleScientificReasoningInputManifestInvariantError(
            "reasoning request contains unsupported disciplines"
        )


def _evidence_weight(record: CertifiedEvidenceRecord) -> Decimal:
    confidence = _d(record.provenance_confidence_score)
    information_gain = _d(record.information_gain_score)
    traceability = _d(record.source_traceability_score)
    lineage = _d(record.lineage_integrity_score)
    replay = _d(record.replay_integrity_score)
    values = (confidence, information_gain, traceability, lineage, replay)
    if any(value < _ZERO or value > _ONE for value in values):
        raise OracleScientificReasoningInputManifestInvariantError(
            "certified evidence scores must remain within [0,1]"
        )
    return (
        confidence * Decimal("0.300000")
        + information_gain * Decimal("0.250000")
        + traceability * Decimal("0.150000")
        + lineage * Decimal("0.150000")
        + replay * Decimal("0.150000")
    )


def build_scientific_reasoning_input_manifest(
    *,
    certified_evidence_package: CertifiedEvidenceAdmissionPackage,
    reasoning_request: ScientificReasoningRequest,
) -> ScientificReasoningInputManifest:
    if not isinstance(
        certified_evidence_package,
        CertifiedEvidenceAdmissionPackage,
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "source must be the canonical OII-008 package"
        )

    try:
        verify_certified_evidence_admission_package(certified_evidence_package)
    except Exception as exc:
        raise OracleScientificReasoningInputManifestInvariantError(
            "OII-008 package verification failed"
        ) from exc

    _verify_request(reasoning_request)

    forbidden = (
        certified_evidence_package.publication_allowed,
        certified_evidence_package.alerting_allowed,
        certified_evidence_package.final_intelligence_conclusion_allowed,
        certified_evidence_package.probability_estimation_allowed,
        certified_evidence_package.qseries_handoff_allowed,
        certified_evidence_package.qseries_execution_allowed,
        certified_evidence_package.order_creation_allowed,
        certified_evidence_package.funds_movement_allowed,
        certified_evidence_package.portfolio_mutation_allowed,
    )
    if (
        certified_evidence_package.read_only is not True
        or certified_evidence_package.reasoning_consumption_allowed is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "OII-008 package violates permanent safety boundary"
        )

    records = tuple(
        sorted(
            certified_evidence_package.certified_evidence_records,
            key=lambda item: item.evidence_node_id,
        )
    )
    if not records:
        raise OracleScientificReasoningInputManifestInvariantError(
            "no certified evidence is available for reasoning"
        )

    inputs: list[ReasoningEvidenceInput] = []
    for record in records:
        weight = _evidence_weight(record)
        input_body = {
            "certified_evidence_id": record.certified_evidence_id,
            "evidence_node_id": record.evidence_node_id,
            "evidence_id": record.evidence_id,
            "source_id": record.source_id,
            "provenance_confidence_score": record.provenance_confidence_score,
            "information_gain_score": record.information_gain_score,
            "source_traceability_score": record.source_traceability_score,
            "lineage_integrity_score": record.lineage_integrity_score,
            "replay_integrity_score": record.replay_integrity_score,
            "certification_hash": record.certification_hash,
            "evidence_weight": _q(weight),
            "admissible_disciplines": reasoning_request.requested_disciplines,
        }
        inputs.append(
            ReasoningEvidenceInput(
                **input_body,
                input_hash=stable_hash(input_body),
            )
        )

    inputs_tuple = tuple(
        sorted(inputs, key=lambda item: item.evidence_node_id)
    )
    weights = [_d(item.evidence_weight) for item in inputs_tuple]
    confidences = [
        _d(item.provenance_confidence_score) for item in inputs_tuple
    ]
    gains = [_d(item.information_gain_score) for item in inputs_tuple]

    def mean(values: list[Decimal]) -> Decimal:
        if not values:
            return _ZERO
        return sum(values, _ZERO) / Decimal(len(values))

    aggregate_weight = min(_ONE, sum(weights, _ZERO) / Decimal(len(weights)))
    manifest_body = {
        "source_certified_evidence_package_id":
            certified_evidence_package.package_id,
        "source_certified_evidence_package_hash":
            certified_evidence_package.package_hash,
        "reasoning_request": reasoning_request,
        "reasoning_evidence_inputs": inputs_tuple,
        "selected_disciplines": reasoning_request.requested_disciplines,
        "certified_evidence_count": len(inputs_tuple),
        "aggregate_evidence_weight": _q(aggregate_weight),
        "mean_provenance_confidence_score": _q(mean(confidences)),
        "mean_information_gain_score": _q(mean(gains)),
    }
    manifest_hash = stable_hash(manifest_body)

    return ScientificReasoningInputManifest(
        manifest_id="scientific-reasoning-input:" + manifest_hash,
        **manifest_body,
        manifest_hash=manifest_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        reasoning_input_ready=True,
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


def verify_scientific_reasoning_input_manifest(
    manifest: ScientificReasoningInputManifest,
) -> bool:
    if not isinstance(manifest, ScientificReasoningInputManifest):
        raise OracleScientificReasoningInputManifestInvariantError(
            "invalid OII-009 manifest type"
        )

    _verify_request(manifest.reasoning_request)

    for item in manifest.reasoning_evidence_inputs:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "input_hash"
        }
        if stable_hash(body) != item.input_hash:
            raise OracleScientificReasoningInputManifestInvariantError(
                "reasoning evidence input hash verification failed"
            )

    if manifest.certified_evidence_count != len(
        manifest.reasoning_evidence_inputs
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "certified evidence count mismatch"
        )
    if manifest.certified_evidence_count <= 0:
        raise OracleScientificReasoningInputManifestInvariantError(
            "reasoning manifest contains no certified evidence"
        )
    if manifest.selected_disciplines != (
        manifest.reasoning_request.requested_disciplines
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "selected discipline lineage mismatch"
        )

    manifest_body = {
        "source_certified_evidence_package_id":
            manifest.source_certified_evidence_package_id,
        "source_certified_evidence_package_hash":
            manifest.source_certified_evidence_package_hash,
        "reasoning_request": manifest.reasoning_request,
        "reasoning_evidence_inputs": manifest.reasoning_evidence_inputs,
        "selected_disciplines": manifest.selected_disciplines,
        "certified_evidence_count": manifest.certified_evidence_count,
        "aggregate_evidence_weight": manifest.aggregate_evidence_weight,
        "mean_provenance_confidence_score":
            manifest.mean_provenance_confidence_score,
        "mean_information_gain_score": manifest.mean_information_gain_score,
    }
    if stable_hash(manifest_body) != manifest.manifest_hash:
        raise OracleScientificReasoningInputManifestInvariantError(
            "manifest hash verification failed"
        )
    if manifest.manifest_id != (
        "scientific-reasoning-input:" + manifest.manifest_hash
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "manifest identity verification failed"
        )

    forbidden = (
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
        or manifest.reasoning_input_ready is not True
        or any(forbidden)
    ):
        raise OracleScientificReasoningInputManifestInvariantError(
            "OII-009 safety boundary violated"
        )
    return True


def serialize_scientific_reasoning_input_manifest(
    manifest: ScientificReasoningInputManifest,
) -> str:
    verify_scientific_reasoning_input_manifest(manifest)
    return canonical_json(manifest)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "SUPPORTED_REASONING_DISCIPLINES",
    "ScientificReasoningRequest",
    "ReasoningEvidenceInput",
    "ScientificReasoningInputManifest",
    "OracleScientificReasoningInputManifestInvariantError",
    "build_scientific_reasoning_request",
    "build_scientific_reasoning_input_manifest",
    "verify_scientific_reasoning_input_manifest",
    "serialize_scientific_reasoning_input_manifest",
]
