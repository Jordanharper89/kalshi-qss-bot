from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSynthesis,
)

BUILD_ID = "OI-044"
OI_044_REVISION = "OI_044_EXPLANATION_SUPPORT_PROFILE_V1"

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

SUPPORT_SINGLE = "single_source_structure"
SUPPORT_MULTI = "multi_evidence_structure"
SUPPORT_MIXED = "mixed_structure"


class ExplanationSupportProfileError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationSupportItem:
    subject: str
    support_class: str
    evidence_count: int
    context_role_count: int
    relationship_type_count: int
    support_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationSupportProfile:
    synthesis_hash: str
    items: tuple[ExplanationSupportItem, ...]
    item_count: int
    profile_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class ExplanationSupportProfiler:
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

    def build(
        self,
        synthesis: StructuralReasoningSynthesis,
    ) -> ExplanationSupportProfile:
        if not isinstance(
            synthesis,
            StructuralReasoningSynthesis,
        ):
            raise TypeError(
                "synthesis must be StructuralReasoningSynthesis"
            )

        items = []

        for signal in synthesis.signals:
            evidence_count = len(
                signal.evidence_observation_ids
            )
            role_count = len(
                signal.context_roles
            )
            relationship_count = len(
                signal.relationship_types
            )

            if (
                evidence_count > 1
                and relationship_count > 0
            ):
                support_class = SUPPORT_MULTI
            elif evidence_count == 1:
                support_class = SUPPORT_SINGLE
            else:
                support_class = SUPPORT_MIXED

            body = {
                "subject": signal.subject,
                "support_class": support_class,
                "evidence_count": evidence_count,
                "context_role_count": role_count,
                "relationship_type_count": relationship_count,
            }

            items.append(
                ExplanationSupportItem(
                    subject=signal.subject,
                    support_class=support_class,
                    evidence_count=evidence_count,
                    context_role_count=role_count,
                    relationship_type_count=relationship_count,
                    support_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda item: item.subject,
            )
        )

        body = {
            "synthesis_hash": synthesis.synthesis_hash,
            "support_hashes": tuple(
                item.support_hash
                for item in items
            ),
            "item_count": len(items),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return ExplanationSupportProfile(
            synthesis_hash=synthesis.synthesis_hash,
            items=items,
            item_count=len(items),
            profile_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_explanation_support_profile() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-044 must remain read-only")

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
        raise AssertionError("OI-044 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_044_REVISION",
    "SUPPORT_SINGLE",
    "SUPPORT_MULTI",
    "SUPPORT_MIXED",
    "ExplanationSupportProfileError",
    "ExplanationSupportItem",
    "ExplanationSupportProfile",
    "ExplanationSupportProfiler",
    "verify_explanation_support_profile",
]
