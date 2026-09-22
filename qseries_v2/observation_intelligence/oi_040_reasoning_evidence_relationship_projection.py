from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_037_reasoning_evidence_registry import ReasoningEvidenceRegistry
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)

BUILD_ID = "OI-040"
OI_040_REVISION = "OI_040_REASONING_EVIDENCE_RELATIONSHIP_PROJECTION_V1"

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

RELATION_SAME_SUBJECT = "same_subject"
RELATION_SAME_PROVIDER = "same_provider"
RELATION_SAME_ADAPTER = "same_adapter"
RELATION_SHARED_CONTEXT_ROLE = "shared_context_role"

SUPPORTED_RELATIONS = (
    RELATION_SAME_ADAPTER,
    RELATION_SAME_PROVIDER,
    RELATION_SAME_SUBJECT,
    RELATION_SHARED_CONTEXT_ROLE,
)


class ReasoningEvidenceRelationshipProjectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRelationship:
    left_observation_id: str
    right_observation_id: str
    relation_types: tuple[str, ...]
    shared_context_roles: tuple[str, ...]
    relationship_hash: str


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceRelationshipProjection:
    evidence_registry_hash: str
    context_registry_hash: str
    relationships: tuple[ReasoningEvidenceRelationship, ...]
    relationship_count: int
    projection_hash: str
    read_only: bool


class ReasoningEvidenceRelationshipProjector:
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

    def project(
        self,
        *,
        evidence_registry: ReasoningEvidenceRegistry,
        context_registry: ReasoningEvidenceContextRegistry,
    ) -> ReasoningEvidenceRelationshipProjection:
        if not isinstance(
            evidence_registry,
            ReasoningEvidenceRegistry,
        ):
            raise TypeError(
                "evidence_registry must be ReasoningEvidenceRegistry"
            )

        if not isinstance(
            context_registry,
            ReasoningEvidenceContextRegistry,
        ):
            raise TypeError(
                "context_registry must be ReasoningEvidenceContextRegistry"
            )

        if (
            evidence_registry.package_hash
            != context_registry.package_hash
        ):
            raise ReasoningEvidenceRelationshipProjectionError(
                "evidence and context registries reference different reasoning packages"
            )

        relationships = []

        for left, right in combinations(
            evidence_registry.records,
            2,
        ):
            left_context = context_registry.get(
                left.canonical_observation_id
            )
            right_context = context_registry.get(
                right.canonical_observation_id
            )

            if left_context is None or right_context is None:
                raise ReasoningEvidenceRelationshipProjectionError(
                    "context registry missing evidence observation"
                )

            relation_types = set()
            shared_roles = tuple(
                sorted(
                    set(left_context.context_roles)
                    & set(right_context.context_roles)
                )
            )

            if left.subject == right.subject:
                relation_types.add(
                    RELATION_SAME_SUBJECT
                )

            if left.provider == right.provider:
                relation_types.add(
                    RELATION_SAME_PROVIDER
                )

            if left.adapter_id == right.adapter_id:
                relation_types.add(
                    RELATION_SAME_ADAPTER
                )

            if shared_roles:
                relation_types.add(
                    RELATION_SHARED_CONTEXT_ROLE
                )

            if not relation_types:
                continue

            relation_types = tuple(
                sorted(relation_types)
            )

            body = {
                "left_observation_id": (
                    left.canonical_observation_id
                ),
                "right_observation_id": (
                    right.canonical_observation_id
                ),
                "relation_types": relation_types,
                "shared_context_roles": shared_roles,
            }

            relationships.append(
                ReasoningEvidenceRelationship(
                    left_observation_id=(
                        left.canonical_observation_id
                    ),
                    right_observation_id=(
                        right.canonical_observation_id
                    ),
                    relation_types=relation_types,
                    shared_context_roles=shared_roles,
                    relationship_hash=(
                        deterministic_sha256(body)
                    ),
                )
            )

        relationships = tuple(
            sorted(
                relationships,
                key=lambda item: (
                    item.left_observation_id,
                    item.right_observation_id,
                ),
            )
        )

        body = {
            "evidence_registry_hash": (
                evidence_registry.registry_hash
            ),
            "context_registry_hash": (
                context_registry.registry_hash
            ),
            "relationship_hashes": tuple(
                item.relationship_hash
                for item in relationships
            ),
            "relationship_count": len(
                relationships
            ),
            "read_only": True,
        }

        return ReasoningEvidenceRelationshipProjection(
            evidence_registry_hash=(
                evidence_registry.registry_hash
            ),
            context_registry_hash=(
                context_registry.registry_hash
            ),
            relationships=relationships,
            relationship_count=len(
                relationships
            ),
            projection_hash=(
                deterministic_sha256(body)
            ),
            read_only=True,
        )


def verify_reasoning_evidence_relationship_projection() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-040 must remain read-only"
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
            "OI-040 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_040_REVISION",
    "RELATION_SAME_SUBJECT",
    "RELATION_SAME_PROVIDER",
    "RELATION_SAME_ADAPTER",
    "RELATION_SHARED_CONTEXT_ROLE",
    "SUPPORTED_RELATIONS",
    "ReasoningEvidenceRelationshipProjectionError",
    "ReasoningEvidenceRelationship",
    "ReasoningEvidenceRelationshipProjection",
    "ReasoningEvidenceRelationshipProjector",
    "verify_reasoning_evidence_relationship_projection",
]
