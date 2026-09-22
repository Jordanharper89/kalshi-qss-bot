from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_042_oracle_reasoning_assembly import OracleReasoningAssembly
from .oi_043_structural_reasoning_synthesis import (
    StructuralReasoningSynthesis,
)
from .oi_044_explanation_support_profile import ExplanationSupportProfile

BUILD_ID = "OI-045"
OI_045_REVISION = "OI_045_ORACLE_REASONING_READ_MODEL_V1"

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


class OracleReasoningReadModelError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleReasoningReadItem:
    subject: str
    signal_type: str
    support_class: str
    evidence_count: int
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True, slots=True)
class OracleReasoningReadModel:
    query_id: str
    profile_id: str
    subject_hint: str
    admission_status: str
    evidence_count: int
    relationship_count: int
    missing_need_count: int
    items: tuple[OracleReasoningReadItem, ...]
    built_at: datetime
    read_model_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class OracleReasoningReadModelBuilder:
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
        *,
        assembly: OracleReasoningAssembly,
        synthesis: StructuralReasoningSynthesis,
        support_profile: ExplanationSupportProfile,
        built_at: datetime,
    ) -> OracleReasoningReadModel:
        if not isinstance(assembly, OracleReasoningAssembly):
            raise TypeError("assembly must be OracleReasoningAssembly")
        if not isinstance(
            synthesis,
            StructuralReasoningSynthesis,
        ):
            raise TypeError(
                "synthesis must be StructuralReasoningSynthesis"
            )
        if not isinstance(
            support_profile,
            ExplanationSupportProfile,
        ):
            raise TypeError(
                "support_profile must be ExplanationSupportProfile"
            )

        if synthesis.assembly_hash != assembly.assembly_hash:
            raise OracleReasoningReadModelError(
                "synthesis does not belong to assembly"
            )

        if support_profile.synthesis_hash != synthesis.synthesis_hash:
            raise OracleReasoningReadModelError(
                "support profile does not belong to synthesis"
            )

        if not isinstance(built_at, datetime):
            raise TypeError("built_at must be datetime")

        if built_at.tzinfo is None:
            raise OracleReasoningReadModelError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(timezone.utc)

        support_by_subject = {
            item.subject: item
            for item in support_profile.items
        }

        items = []

        for signal in synthesis.signals:
            support = support_by_subject.get(
                signal.subject
            )

            if support is None:
                raise OracleReasoningReadModelError(
                    f"support profile missing subject: {signal.subject}"
                )

            body = {
                "subject": signal.subject,
                "signal_type": signal.signal_type,
                "support_class": support.support_class,
                "evidence_count": len(
                    signal.evidence_observation_ids
                ),
                "context_roles": signal.context_roles,
                "relationship_types": signal.relationship_types,
            }

            items.append(
                OracleReasoningReadItem(
                    subject=signal.subject,
                    signal_type=signal.signal_type,
                    support_class=support.support_class,
                    evidence_count=len(
                        signal.evidence_observation_ids
                    ),
                    context_roles=signal.context_roles,
                    relationship_types=signal.relationship_types,
                    item_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda item: item.subject,
            )
        )

        body = {
            "query_id": assembly.query_id,
            "profile_id": assembly.profile_id,
            "subject_hint": assembly.subject_hint,
            "admission_status": assembly.admission_status,
            "evidence_count": assembly.evidence_count,
            "relationship_count": assembly.relationship_count,
            "missing_need_count": assembly.missing_need_count,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return OracleReasoningReadModel(
            query_id=assembly.query_id,
            profile_id=assembly.profile_id,
            subject_hint=assembly.subject_hint,
            admission_status=assembly.admission_status,
            evidence_count=assembly.evidence_count,
            relationship_count=assembly.relationship_count,
            missing_need_count=assembly.missing_need_count,
            items=items,
            built_at=built_at,
            read_model_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_oracle_reasoning_read_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-045 must remain read-only")

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
        raise AssertionError("OI-045 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_045_REVISION",
    "OracleReasoningReadModelError",
    "OracleReasoningReadItem",
    "OracleReasoningReadModel",
    "OracleReasoningReadModelBuilder",
    "verify_oracle_reasoning_read_model",
]
