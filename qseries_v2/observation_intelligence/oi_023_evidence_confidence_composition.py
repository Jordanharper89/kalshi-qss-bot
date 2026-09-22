from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_016_evidence_sufficiency_gate import EvidenceSufficiencyDecision
from .oi_022_evidence_narrative_assembly import EvidenceNarrative

BUILD_ID = "OI-023"
OI_023_REVISION = "OI_023_EVIDENCE_CONFIDENCE_COMPOSITION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False

COMPLETE = "complete"
PARTIAL = "partial"
INSUFFICIENT = "insufficient"


class EvidenceConfidenceCompositionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceConfidenceProfile:
    sufficiency_decision_hash: str
    narrative_hash: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    supporting_relationship_count: int
    contradicting_relationship_count: int
    completeness_status: str
    confidence_hash: str
    predictive: bool
    edge_score_allowed: bool
    probability_allowed: bool
    read_only: bool


class EvidenceConfidenceComposer:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def compose(
        self,
        *,
        sufficiency: EvidenceSufficiencyDecision,
        narrative: EvidenceNarrative,
    ) -> EvidenceConfidenceProfile:
        if not isinstance(sufficiency, EvidenceSufficiencyDecision):
            raise TypeError(
                "sufficiency must be EvidenceSufficiencyDecision"
            )

        if not isinstance(narrative, EvidenceNarrative):
            raise TypeError(
                "narrative must be EvidenceNarrative"
            )

        if sufficiency.sufficient:
            completeness = COMPLETE
        elif (
            sufficiency.evidence_item_count > 0
            or narrative.entries
        ):
            completeness = PARTIAL
        else:
            completeness = INSUFFICIENT

        body = {
            "sufficiency_decision_hash": sufficiency.decision_hash,
            "narrative_hash": narrative.narrative_hash,
            "evidence_item_count": sufficiency.evidence_item_count,
            "distinct_source_count": sufficiency.distinct_source_count,
            "stale_evidence_count": sufficiency.stale_evidence_count,
            "supporting_relationship_count": narrative.supporting_relationship_count,
            "contradicting_relationship_count": narrative.contradicting_relationship_count,
            "completeness_status": completeness,
            "predictive": False,
            "edge_score_allowed": False,
            "probability_allowed": False,
            "read_only": True,
        }

        return EvidenceConfidenceProfile(
            sufficiency_decision_hash=sufficiency.decision_hash,
            narrative_hash=narrative.narrative_hash,
            evidence_item_count=sufficiency.evidence_item_count,
            distinct_source_count=sufficiency.distinct_source_count,
            stale_evidence_count=sufficiency.stale_evidence_count,
            supporting_relationship_count=narrative.supporting_relationship_count,
            contradicting_relationship_count=narrative.contradicting_relationship_count,
            completeness_status=completeness,
            confidence_hash=deterministic_sha256(body),
            predictive=False,
            edge_score_allowed=False,
            probability_allowed=False,
            read_only=True,
        )


def verify_evidence_confidence_composition() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-023 must remain read-only"
        )

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
        )
    ):
        raise AssertionError(
            "OI-023 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_023_REVISION",
    "COMPLETE",
    "PARTIAL",
    "INSUFFICIENT",
    "EvidenceConfidenceCompositionError",
    "EvidenceConfidenceProfile",
    "EvidenceConfidenceComposer",
    "verify_evidence_confidence_composition",
]
