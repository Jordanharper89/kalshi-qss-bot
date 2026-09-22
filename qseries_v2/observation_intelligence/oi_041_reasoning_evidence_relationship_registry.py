from __future__ import annotations

from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_040_reasoning_evidence_relationship_projection import (
    ReasoningEvidenceRelationship,
    ReasoningEvidenceRelationshipProjection,
)

BUILD_ID = "OI-041"
OI_041_REVISION = "OI_041_REASONING_EVIDENCE_RELATIONSHIP_REGISTRY_V1"

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


class ReasoningEvidenceRelationshipRegistryError(ValueError):
    pass


class ReasoningEvidenceRelationshipRegistry:
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

    def __init__(
        self,
        projection: ReasoningEvidenceRelationshipProjection,
    ) -> None:
        if not isinstance(
            projection,
            ReasoningEvidenceRelationshipProjection,
        ):
            raise TypeError(
                "projection must be ReasoningEvidenceRelationshipProjection"
            )

        keys = tuple(
            (
                item.left_observation_id,
                item.right_observation_id,
            )
            for item in projection.relationships
        )

        if len(keys) != len(set(keys)):
            raise ReasoningEvidenceRelationshipRegistryError(
                "duplicate evidence relationship pair"
            )

        self._projection = projection
        self._relationships = tuple(
            projection.relationships
        )

    @property
    def relationships(
        self,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        return self._relationships

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            {
                "projection_hash": (
                    self._projection.projection_hash
                ),
                "relationship_hashes": tuple(
                    item.relationship_hash
                    for item in self._relationships
                ),
            }
        )

    def by_observation(
        self,
        canonical_observation_id: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = str(canonical_observation_id).strip()

        return tuple(
            item
            for item in self._relationships
            if (
                item.left_observation_id == key
                or item.right_observation_id == key
            )
        )

    def by_relation(
        self,
        relation_type: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = " ".join(
            str(relation_type).strip().lower().split()
        )

        return tuple(
            item
            for item in self._relationships
            if key in item.relation_types
        )

    def by_shared_context_role(
        self,
        role: str,
    ) -> tuple[ReasoningEvidenceRelationship, ...]:
        key = " ".join(
            str(role).strip().lower().split()
        )

        return tuple(
            item
            for item in self._relationships
            if key in item.shared_context_roles
        )


def verify_reasoning_evidence_relationship_registry() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-041 must remain read-only"
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
            CAUSAL_CLAIM_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-041 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_041_REVISION",
    "ReasoningEvidenceRelationshipRegistryError",
    "ReasoningEvidenceRelationshipRegistry",
    "verify_reasoning_evidence_relationship_registry",
]
