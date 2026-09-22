from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_039_reasoning_evidence_context_registry import (
    ReasoningEvidenceContextRegistry,
)
from .oi_041_reasoning_evidence_relationship_registry import (
    ReasoningEvidenceRelationshipRegistry,
)
from .oi_042_oracle_reasoning_assembly import OracleReasoningAssembly

BUILD_ID = "OI-043"
OI_043_REVISION = "OI_043_STRUCTURAL_REASONING_SYNTHESIS_V1"

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


class StructuralReasoningSynthesisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StructuralReasoningSignal:
    signal_type: str
    subject: str
    evidence_observation_ids: tuple[str, ...]
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    signal_hash: str


@dataclass(frozen=True, slots=True)
class StructuralReasoningSynthesis:
    assembly_hash: str
    signals: tuple[StructuralReasoningSignal, ...]
    signal_count: int
    synthesis_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class StructuralReasoningSynthesizer:
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

    def synthesize(
        self,
        *,
        assembly: OracleReasoningAssembly,
        context_registry: ReasoningEvidenceContextRegistry,
        relationship_registry: ReasoningEvidenceRelationshipRegistry,
    ) -> StructuralReasoningSynthesis:
        if not isinstance(assembly, OracleReasoningAssembly):
            raise TypeError("assembly must be OracleReasoningAssembly")
        if not isinstance(
            context_registry,
            ReasoningEvidenceContextRegistry,
        ):
            raise TypeError(
                "context_registry must be ReasoningEvidenceContextRegistry"
            )
        if not isinstance(
            relationship_registry,
            ReasoningEvidenceRelationshipRegistry,
        ):
            raise TypeError(
                "relationship_registry must be ReasoningEvidenceRelationshipRegistry"
            )

        if assembly.context_registry_hash != context_registry.registry_hash:
            raise StructuralReasoningSynthesisError(
                "assembly/context registry lineage mismatch"
            )

        if (
            assembly.relationship_registry_hash
            != relationship_registry.registry_hash
        ):
            raise StructuralReasoningSynthesisError(
                "assembly/relationship registry lineage mismatch"
            )

        subjects = sorted(
            {
                item.subject
                for item in context_registry.contexts
            }
        )

        signals = []

        for subject in subjects:
            subject_contexts = tuple(
                item
                for item in context_registry.contexts
                if item.subject == subject
            )

            ids = tuple(
                sorted(
                    item.canonical_observation_id
                    for item in subject_contexts
                )
            )

            roles = tuple(
                sorted(
                    {
                        role
                        for item in subject_contexts
                        for role in item.context_roles
                    }
                )
            )

            relationship_types = tuple(
                sorted(
                    {
                        relation
                        for relationship in relationship_registry.relationships
                        if (
                            relationship.left_observation_id in ids
                            or relationship.right_observation_id in ids
                        )
                        for relation in relationship.relation_types
                    }
                )
            )

            signal_type = (
                "multi_evidence_context"
                if len(ids) > 1
                else "single_evidence_context"
            )

            body = {
                "signal_type": signal_type,
                "subject": subject,
                "evidence_observation_ids": ids,
                "context_roles": roles,
                "relationship_types": relationship_types,
            }

            signals.append(
                StructuralReasoningSignal(
                    signal_type=signal_type,
                    subject=subject,
                    evidence_observation_ids=ids,
                    context_roles=roles,
                    relationship_types=relationship_types,
                    signal_hash=deterministic_sha256(body),
                )
            )

        signals = tuple(
            sorted(
                signals,
                key=lambda item: (
                    item.subject,
                    item.signal_type,
                ),
            )
        )

        body = {
            "assembly_hash": assembly.assembly_hash,
            "signal_hashes": tuple(
                item.signal_hash
                for item in signals
            ),
            "signal_count": len(signals),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return StructuralReasoningSynthesis(
            assembly_hash=assembly.assembly_hash,
            signals=signals,
            signal_count=len(signals),
            synthesis_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_structural_reasoning_synthesis() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-043 must remain read-only")

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
        raise AssertionError("OI-043 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_043_REVISION",
    "StructuralReasoningSynthesisError",
    "StructuralReasoningSignal",
    "StructuralReasoningSynthesis",
    "StructuralReasoningSynthesizer",
    "verify_structural_reasoning_synthesis",
]
