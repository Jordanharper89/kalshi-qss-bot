from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import ExplanationEvidencePackage
from .oi_022_evidence_narrative_assembly import EvidenceNarrative
from .oi_023_evidence_confidence_composition import EvidenceConfidenceProfile

BUILD_ID = "OI-024"
OI_024_REVISION = "OI_024_ORACLE_EXPLANATION_READ_MODEL_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class OracleExplanationReadModelError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationTimelineEntry:
    ordinal: int
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    agreement_count: int
    contradiction_count: int


@dataclass(frozen=True, slots=True)
class OracleExplanationReadModel:
    query_id: str
    profile_id: str
    built_at: datetime
    sufficient_evidence: bool
    completeness_status: str
    evidence_item_count: int
    distinct_source_count: int
    stale_evidence_count: int
    supporting_relationship_count: int
    contradicting_relationship_count: int
    timeline: tuple[OracleExplanationTimelineEntry, ...]
    missing_required_evidence: bool
    read_model_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool
    probability_allowed: bool
    read_only: bool


class OracleExplanationReadModelBuilder:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def build(
        self,
        *,
        package: ExplanationEvidencePackage,
        narrative: EvidenceNarrative,
        confidence: EvidenceConfidenceProfile,
        built_at: datetime,
    ) -> OracleExplanationReadModel:
        if not isinstance(package, ExplanationEvidencePackage):
            raise TypeError(
                "package must be ExplanationEvidencePackage"
            )

        if not isinstance(narrative, EvidenceNarrative):
            raise TypeError(
                "narrative must be EvidenceNarrative"
            )

        if not isinstance(confidence, EvidenceConfidenceProfile):
            raise TypeError(
                "confidence must be EvidenceConfidenceProfile"
            )

        if narrative.package_hash != package.package_hash:
            raise OracleExplanationReadModelError(
                "narrative does not belong to explanation package"
            )

        if confidence.narrative_hash != narrative.narrative_hash:
            raise OracleExplanationReadModelError(
                "confidence profile does not belong to narrative"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleExplanationReadModelError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        timeline = tuple(
            OracleExplanationTimelineEntry(
                ordinal=item.ordinal,
                evidence_observation_id=(
                    item.evidence_observation_id
                ),
                temporal_relation=(
                    item.temporal_relation
                ),
                seconds_from_change_observation=(
                    item.seconds_from_change_observation
                ),
                agreement_count=item.agreement_count,
                contradiction_count=(
                    item.contradiction_count
                ),
            )
            for item in narrative.entries
        )

        missing_required = (
            not package.sufficient_evidence
        )

        body = {
            "query_id": package.query_id,
            "profile_id": package.profile_id,
            "built_at": built_at,
            "sufficient_evidence": (
                package.sufficient_evidence
            ),
            "completeness_status": (
                confidence.completeness_status
            ),
            "evidence_item_count": (
                confidence.evidence_item_count
            ),
            "distinct_source_count": (
                confidence.distinct_source_count
            ),
            "stale_evidence_count": (
                confidence.stale_evidence_count
            ),
            "supporting_relationship_count": (
                confidence.supporting_relationship_count
            ),
            "contradicting_relationship_count": (
                confidence.contradicting_relationship_count
            ),
            "timeline": tuple(
                (
                    item.ordinal,
                    item.evidence_observation_id,
                    item.temporal_relation,
                    item.seconds_from_change_observation,
                    item.agreement_count,
                    item.contradiction_count,
                )
                for item in timeline
            ),
            "missing_required_evidence": (
                missing_required
            ),
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
            "probability_allowed": False,
            "read_only": True,
        }

        return OracleExplanationReadModel(
            query_id=package.query_id,
            profile_id=package.profile_id,
            built_at=built_at,
            sufficient_evidence=(
                package.sufficient_evidence
            ),
            completeness_status=(
                confidence.completeness_status
            ),
            evidence_item_count=(
                confidence.evidence_item_count
            ),
            distinct_source_count=(
                confidence.distinct_source_count
            ),
            stale_evidence_count=(
                confidence.stale_evidence_count
            ),
            supporting_relationship_count=(
                confidence.supporting_relationship_count
            ),
            contradicting_relationship_count=(
                confidence.contradicting_relationship_count
            ),
            timeline=timeline,
            missing_required_evidence=(
                missing_required
            ),
            read_model_hash=(
                deterministic_sha256(body)
            ),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
            probability_allowed=False,
            read_only=True,
        )


def verify_oracle_explanation_read_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-024 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-024 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_024_REVISION",
    "OracleExplanationReadModelError",
    "OracleExplanationTimelineEntry",
    "OracleExplanationReadModel",
    "OracleExplanationReadModelBuilder",
    "verify_oracle_explanation_read_model",
]
