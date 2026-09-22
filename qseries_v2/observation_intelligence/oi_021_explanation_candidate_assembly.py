from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)
from .oi_019_evidence_contradiction_registry import (
    EvidenceContradictionRegistry,
)
from .oi_020_temporal_association import (
    TemporalAssociation,
)

BUILD_ID = "OI-021"
OI_021_REVISION = "OI_021_EXPLANATION_CANDIDATE_ASSEMBLY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False


class ExplanationCandidateAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationCandidate:
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    contradiction_count: int
    agreement_count: int
    candidate_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationCandidateSet:
    package_hash: str
    candidates: tuple[ExplanationCandidate, ...]
    candidate_set_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool


class ExplanationCandidateAssembler:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False

    def assemble(
        self,
        *,
        package: ExplanationEvidencePackage,
        temporal_associations: tuple[TemporalAssociation, ...],
        evidence_relationships: EvidenceContradictionRegistry,
    ) -> ExplanationCandidateSet:
        if not isinstance(
            package,
            ExplanationEvidencePackage,
        ):
            raise TypeError(
                "package must be ExplanationEvidencePackage"
            )

        if not isinstance(
            evidence_relationships,
            EvidenceContradictionRegistry,
        ):
            raise TypeError(
                "evidence_relationships must be "
                "EvidenceContradictionRegistry"
            )

        associations = tuple(
            temporal_associations
        )

        if any(
            not isinstance(
                item,
                TemporalAssociation,
            )
            for item in associations
        ):
            raise TypeError(
                "all temporal associations must be "
                "TemporalAssociation"
            )

        candidates = []

        for association in associations:
            relationships = (
                evidence_relationships.for_evidence(
                    association.evidence_observation_id
                )
            )

            contradiction_count = sum(
                1
                for item in relationships
                if item.relation == "contradicts"
            )

            agreement_count = sum(
                1
                for item in relationships
                if item.relation == "agrees"
            )

            body = {
                "evidence_observation_id": (
                    association.evidence_observation_id
                ),
                "temporal_relation": (
                    association.temporal_relation
                ),
                "seconds_from_change_observation": (
                    association.seconds_from_change_observation
                ),
                "contradiction_count": (
                    contradiction_count
                ),
                "agreement_count": (
                    agreement_count
                ),
            }

            candidates.append(
                ExplanationCandidate(
                    evidence_observation_id=(
                        association.evidence_observation_id
                    ),
                    temporal_relation=(
                        association.temporal_relation
                    ),
                    seconds_from_change_observation=(
                        association.seconds_from_change_observation
                    ),
                    contradiction_count=(
                        contradiction_count
                    ),
                    agreement_count=(
                        agreement_count
                    ),
                    candidate_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        ordered = tuple(
            sorted(
                candidates,
                key=lambda item: (
                    abs(
                        item.seconds_from_change_observation
                    ),
                    item.evidence_observation_id,
                ),
            )
        )

        body = {
            "package_hash": package.package_hash,
            "candidate_hashes": tuple(
                item.candidate_hash
                for item in ordered
            ),
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
        }

        return ExplanationCandidateSet(
            package_hash=package.package_hash,
            candidates=ordered,
            candidate_set_hash=(
                deterministic_sha256(body)
            ),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
        )


def verify_explanation_candidate_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-021 must remain read-only"
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
        )
    ):
        raise AssertionError(
            "OI-021 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_021_REVISION",
    "ExplanationCandidateAssemblyError",
    "ExplanationCandidate",
    "ExplanationCandidateSet",
    "ExplanationCandidateAssembler",
    "verify_explanation_candidate_assembly",
]
