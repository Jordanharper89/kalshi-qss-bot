from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel

BUILD_ID = "OI-046"
OI_046_REVISION = "OI_046_EXPLANATION_CANDIDATE_RESOLUTION_V1"

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

STATUS_SUPPORTED = "supported"
STATUS_PARTIAL = "partial"
STATUS_UNSUPPORTED = "unsupported"


class ExplanationCandidateResolutionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExplanationCandidateResolutionItem:
    subject: str
    status: str
    evidence_count: int
    support_class: str
    context_roles: tuple[str, ...]
    relationship_types: tuple[str, ...]
    reason_codes: tuple[str, ...]
    item_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationCandidateResolution:
    query_id: str
    read_model_hash: str
    items: tuple[ExplanationCandidateResolutionItem, ...]
    supported_count: int
    partial_count: int
    unsupported_count: int
    resolution_hash: str
    read_only: bool


class ExplanationCandidateResolver:
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

    def resolve(
        self,
        read_model: OracleReasoningReadModel,
    ) -> ExplanationCandidateResolution:
        if not isinstance(
            read_model,
            OracleReasoningReadModel,
        ):
            raise TypeError(
                "read_model must be OracleReasoningReadModel"
            )

        items = []

        for item in read_model.items:
            reasons = []

            if item.evidence_count < 1:
                status = STATUS_UNSUPPORTED
                reasons.append("no_evidence")
            elif (
                read_model.admission_status == "partial"
                or read_model.missing_need_count > 0
            ):
                status = STATUS_PARTIAL
                reasons.append("missing_required_evidence")
            else:
                status = STATUS_SUPPORTED

            if not item.relationship_types:
                reasons.append("no_structural_relationships")

            if len(item.context_roles) < 1:
                reasons.append("no_context_roles")

            reasons = tuple(sorted(set(reasons)))

            body = {
                "subject": item.subject,
                "status": status,
                "evidence_count": item.evidence_count,
                "support_class": item.support_class,
                "context_roles": item.context_roles,
                "relationship_types": item.relationship_types,
                "reason_codes": reasons,
            }

            items.append(
                ExplanationCandidateResolutionItem(
                    subject=item.subject,
                    status=status,
                    evidence_count=item.evidence_count,
                    support_class=item.support_class,
                    context_roles=item.context_roles,
                    relationship_types=item.relationship_types,
                    reason_codes=reasons,
                    item_hash=deterministic_sha256(body),
                )
            )

        items = tuple(
            sorted(
                items,
                key=lambda value: value.subject,
            )
        )

        supported_count = sum(
            1 for item in items
            if item.status == STATUS_SUPPORTED
        )
        partial_count = sum(
            1 for item in items
            if item.status == STATUS_PARTIAL
        )
        unsupported_count = sum(
            1 for item in items
            if item.status == STATUS_UNSUPPORTED
        )

        body = {
            "query_id": read_model.query_id,
            "read_model_hash": read_model.read_model_hash,
            "item_hashes": tuple(
                item.item_hash
                for item in items
            ),
            "supported_count": supported_count,
            "partial_count": partial_count,
            "unsupported_count": unsupported_count,
            "read_only": True,
        }

        return ExplanationCandidateResolution(
            query_id=read_model.query_id,
            read_model_hash=read_model.read_model_hash,
            items=items,
            supported_count=supported_count,
            partial_count=partial_count,
            unsupported_count=unsupported_count,
            resolution_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_candidate_resolution() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-046 must remain read-only"
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
            "OI-046 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_046_REVISION",
    "STATUS_SUPPORTED",
    "STATUS_PARTIAL",
    "STATUS_UNSUPPORTED",
    "ExplanationCandidateResolutionError",
    "ExplanationCandidateResolutionItem",
    "ExplanationCandidateResolution",
    "ExplanationCandidateResolver",
    "verify_explanation_candidate_resolution",
]
