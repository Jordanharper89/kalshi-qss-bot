from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)
from .oi_049_explanation_evidence_ordering import (
    ExplanationEvidenceOrdering,
)

BUILD_ID = "OI-050"
OI_050_REVISION = "OI_050_EXPLANATION_COMPLETENESS_EVALUATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False

COMPLETE = "complete"
PARTIAL = "partial"
INSUFFICIENT = "insufficient"


@dataclass(frozen=True, slots=True)
class ExplanationCompletenessEvaluation:
    query_id: str
    status: str
    supported_count: int
    partial_count: int
    unsupported_count: int
    ordered_item_count: int
    reason_codes: tuple[str, ...]
    evaluation_hash: str
    read_only: bool


class ExplanationCompletenessEvaluator:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False
    causal_claim_allowed = False

    def evaluate(
        self,
        *,
        resolution: ExplanationCandidateResolution,
        ordering: ExplanationEvidenceOrdering,
    ) -> ExplanationCompletenessEvaluation:
        if not isinstance(
            resolution,
            ExplanationCandidateResolution,
        ):
            raise TypeError(
                "resolution must be ExplanationCandidateResolution"
            )
        if not isinstance(
            ordering,
            ExplanationEvidenceOrdering,
        ):
            raise TypeError(
                "ordering must be ExplanationEvidenceOrdering"
            )
        if resolution.query_id != ordering.query_id:
            raise ValueError(
                "resolution/ordering query_id mismatch"
            )

        reasons = []

        if resolution.unsupported_count > 0:
            status = INSUFFICIENT
            reasons.append("unsupported_explanation_candidates")
        elif resolution.partial_count > 0:
            status = PARTIAL
            reasons.append("partial_explanation_candidates")
        elif (
            resolution.supported_count > 0
            and ordering.item_count > 0
        ):
            status = COMPLETE
        else:
            status = INSUFFICIENT
            reasons.append("no_supported_explanation")

        if ordering.item_count == 0:
            reasons.append("no_ordered_explanation_evidence")

        reasons = tuple(sorted(set(reasons)))

        body = {
            "query_id": resolution.query_id,
            "status": status,
            "supported_count": resolution.supported_count,
            "partial_count": resolution.partial_count,
            "unsupported_count": resolution.unsupported_count,
            "ordered_item_count": ordering.item_count,
            "reason_codes": reasons,
            "read_only": True,
        }

        return ExplanationCompletenessEvaluation(
            query_id=resolution.query_id,
            status=status,
            supported_count=resolution.supported_count,
            partial_count=resolution.partial_count,
            unsupported_count=resolution.unsupported_count,
            ordered_item_count=ordering.item_count,
            reason_codes=reasons,
            evaluation_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_completeness_evaluation() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-050 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
        )
    ):
        raise AssertionError("OI-050 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_050_REVISION",
    "COMPLETE",
    "PARTIAL",
    "INSUFFICIENT",
    "ExplanationCompletenessEvaluation",
    "ExplanationCompletenessEvaluator",
    "verify_explanation_completeness_evaluation",
]
