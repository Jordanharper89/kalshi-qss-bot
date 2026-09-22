from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import ExplanationEvidencePackage
from .oi_019_evidence_contradiction_registry import EvidenceContradictionRegistry
from .oi_021_explanation_candidate_assembly import ExplanationCandidateSet

BUILD_ID = "OI-022"
OI_022_REVISION = "OI_022_EVIDENCE_NARRATIVE_ASSEMBLY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False


class EvidenceNarrativeAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NarrativeEvidenceEntry:
    ordinal: int
    evidence_observation_id: str
    temporal_relation: str
    seconds_from_change_observation: int
    agreement_count: int
    contradiction_count: int
    entry_hash: str


@dataclass(frozen=True, slots=True)
class EvidenceNarrative:
    package_hash: str
    candidate_set_hash: str
    entries: tuple[NarrativeEvidenceEntry, ...]
    supporting_relationship_count: int
    contradicting_relationship_count: int
    narrative_hash: str
    causal_claim_allowed: bool
    predictive: bool
    edge_score_allowed: bool
    read_only: bool


class EvidenceNarrativeAssembler:
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
        candidates: ExplanationCandidateSet,
        relationships: EvidenceContradictionRegistry,
    ) -> EvidenceNarrative:
        if not isinstance(package, ExplanationEvidencePackage):
            raise TypeError("package must be ExplanationEvidencePackage")

        if not isinstance(candidates, ExplanationCandidateSet):
            raise TypeError("candidates must be ExplanationCandidateSet")

        if not isinstance(relationships, EvidenceContradictionRegistry):
            raise TypeError("relationships must be EvidenceContradictionRegistry")

        if candidates.package_hash != package.package_hash:
            raise EvidenceNarrativeAssemblyError(
                "candidate set does not belong to explanation package"
            )

        entries = []

        for ordinal, candidate in enumerate(candidates.candidates, start=1):
            body = {
                "ordinal": ordinal,
                "evidence_observation_id": candidate.evidence_observation_id,
                "temporal_relation": candidate.temporal_relation,
                "seconds_from_change_observation": candidate.seconds_from_change_observation,
                "agreement_count": candidate.agreement_count,
                "contradiction_count": candidate.contradiction_count,
            }

            entries.append(
                NarrativeEvidenceEntry(
                    ordinal=ordinal,
                    evidence_observation_id=candidate.evidence_observation_id,
                    temporal_relation=candidate.temporal_relation,
                    seconds_from_change_observation=candidate.seconds_from_change_observation,
                    agreement_count=candidate.agreement_count,
                    contradiction_count=candidate.contradiction_count,
                    entry_hash=deterministic_sha256(body),
                )
            )

        supporting_count = len(relationships.by_relation("agrees"))
        contradicting_count = len(relationships.by_relation("contradicts"))

        body = {
            "package_hash": package.package_hash,
            "candidate_set_hash": candidates.candidate_set_hash,
            "entry_hashes": tuple(item.entry_hash for item in entries),
            "supporting_relationship_count": supporting_count,
            "contradicting_relationship_count": contradicting_count,
            "causal_claim_allowed": False,
            "predictive": False,
            "edge_score_allowed": False,
            "read_only": True,
        }

        return EvidenceNarrative(
            package_hash=package.package_hash,
            candidate_set_hash=candidates.candidate_set_hash,
            entries=tuple(entries),
            supporting_relationship_count=supporting_count,
            contradicting_relationship_count=contradicting_count,
            narrative_hash=deterministic_sha256(body),
            causal_claim_allowed=False,
            predictive=False,
            edge_score_allowed=False,
            read_only=True,
        )


def verify_evidence_narrative_assembly() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-022 must remain read-only")

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
        raise AssertionError("OI-022 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_022_REVISION",
    "EvidenceNarrativeAssemblyError",
    "NarrativeEvidenceEntry",
    "EvidenceNarrative",
    "EvidenceNarrativeAssembler",
    "verify_evidence_narrative_assembly",
]
