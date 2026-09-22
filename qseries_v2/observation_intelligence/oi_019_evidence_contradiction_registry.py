from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_018_explanation_evidence_package import (
    ExplanationEvidencePackage,
)

BUILD_ID = "OI-019"
OI_019_REVISION = "OI_019_EVIDENCE_CONTRADICTION_REGISTRY_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_INFERENCE_ALLOWED = False
PREDICTION_ALLOWED = False

SUPPORTED_RELATIONS = (
    "agrees",
    "contradicts",
    "supersedes",
    "independent",
)


class EvidenceContradictionRegistryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceRelationship:
    relationship_id: str
    left_evidence_id: str
    right_evidence_id: str
    relation: str
    basis: str

    def __post_init__(self) -> None:
        relationship_id = " ".join(
            str(self.relationship_id).strip().lower().split()
        )
        left = str(self.left_evidence_id).strip()
        right = str(self.right_evidence_id).strip()
        relation = " ".join(
            str(self.relation).strip().lower().split()
        )
        basis = " ".join(str(self.basis).strip().split())

        if not relationship_id:
            raise EvidenceContradictionRegistryError(
                "relationship_id must not be empty"
            )
        if not left or not right:
            raise EvidenceContradictionRegistryError(
                "evidence identities must not be empty"
            )
        if left == right:
            raise EvidenceContradictionRegistryError(
                "self relationship is not allowed"
            )
        if relation not in SUPPORTED_RELATIONS:
            raise EvidenceContradictionRegistryError(
                f"unsupported evidence relation: {relation}"
            )
        if not basis:
            raise EvidenceContradictionRegistryError(
                "basis must not be empty"
            )

        ordered = tuple(sorted((left, right)))

        object.__setattr__(self, "relationship_id", relationship_id)
        object.__setattr__(self, "left_evidence_id", ordered[0])
        object.__setattr__(self, "right_evidence_id", ordered[1])
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "basis", basis)

    @property
    def relationship_hash(self) -> str:
        return deterministic_sha256(
            {
                "relationship_id": self.relationship_id,
                "left_evidence_id": self.left_evidence_id,
                "right_evidence_id": self.right_evidence_id,
                "relation": self.relation,
                "basis": self.basis,
            }
        )


class EvidenceContradictionRegistry:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_inference_allowed = False
    prediction_allowed = False

    def __init__(
        self,
        relationships: tuple[EvidenceRelationship, ...],
    ) -> None:
        values = tuple(relationships)

        if any(
            not isinstance(item, EvidenceRelationship)
            for item in values
        ):
            raise TypeError(
                "all relationships must be EvidenceRelationship"
            )

        ordered = tuple(
            sorted(
                values,
                key=lambda item: item.relationship_id,
            )
        )

        if values != ordered:
            raise EvidenceContradictionRegistryError(
                "relationships must be deterministically sorted"
            )

        ids = tuple(
            item.relationship_id
            for item in values
        )
        if len(ids) != len(set(ids)):
            raise EvidenceContradictionRegistryError(
                "duplicate relationship_id"
            )

        self._relationships = values
        self._by_id = MappingProxyType(
            {item.relationship_id: item for item in values}
        )

    @property
    def relationships(self) -> tuple[EvidenceRelationship, ...]:
        return self._relationships

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            tuple(
                item.relationship_hash
                for item in self._relationships
            )
        )

    def by_relation(
        self,
        relation: str,
    ) -> tuple[EvidenceRelationship, ...]:
        normalized = " ".join(
            str(relation).strip().lower().split()
        )

        if normalized not in SUPPORTED_RELATIONS:
            return ()

        return tuple(
            item
            for item in self._relationships
            if item.relation == normalized
        )

    def for_evidence(
        self,
        evidence_id: str,
    ) -> tuple[EvidenceRelationship, ...]:
        key = str(evidence_id).strip()

        return tuple(
            item
            for item in self._relationships
            if (
                item.left_evidence_id == key
                or item.right_evidence_id == key
            )
        )


def verify_evidence_contradiction_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-019 must remain read-only"
        )

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_INFERENCE_ALLOWED,
            PREDICTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-019 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_019_REVISION",
    "SUPPORTED_RELATIONS",
    "EvidenceContradictionRegistryError",
    "EvidenceRelationship",
    "EvidenceContradictionRegistry",
    "verify_evidence_contradiction_registry",
]
