from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel
from .oi_047_evidence_explanation_synthesis import EvidenceExplanationSynthesis

BUILD_ID = "OI-049"
OI_049_REVISION = "OI_049_EXPLANATION_EVIDENCE_ORDERING_V1"

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


@dataclass(frozen=True, slots=True)
class OrderedExplanationEvidenceItem:
    ordinal: int
    subject: str
    status: str
    statement: str
    evidence_count: int
    context_role_count: int
    relationship_type_count: int
    order_hash: str


@dataclass(frozen=True, slots=True)
class ExplanationEvidenceOrdering:
    query_id: str
    items: tuple[OrderedExplanationEvidenceItem, ...]
    item_count: int
    ordering_hash: str
    read_only: bool


class ExplanationEvidenceOrderer:
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

    def order(
        self,
        *,
        read_model: OracleReasoningReadModel,
        synthesis: EvidenceExplanationSynthesis,
    ) -> ExplanationEvidenceOrdering:
        if not isinstance(read_model, OracleReasoningReadModel):
            raise TypeError("read_model must be OracleReasoningReadModel")
        if not isinstance(synthesis, EvidenceExplanationSynthesis):
            raise TypeError("synthesis must be EvidenceExplanationSynthesis")
        if synthesis.read_model_hash != read_model.read_model_hash:
            raise ValueError("synthesis/read model lineage mismatch")

        model_by_subject = {
            item.subject: item
            for item in read_model.items
        }

        rows = []

        for statement in synthesis.statements:
            model_item = model_by_subject.get(statement.subject)
            if model_item is None:
                raise ValueError(
                    f"read model missing explanation subject: {statement.subject}"
                )

            rows.append(
                (
                    -model_item.evidence_count,
                    -len(model_item.relationship_types),
                    -len(model_item.context_roles),
                    statement.subject,
                    statement,
                    model_item,
                )
            )

        rows.sort()

        items = []

        for ordinal, row in enumerate(rows, start=1):
            _, _, _, subject, statement, model_item = row

            body = {
                "ordinal": ordinal,
                "subject": subject,
                "status": statement.status,
                "statement": statement.statement,
                "evidence_count": model_item.evidence_count,
                "context_role_count": len(model_item.context_roles),
                "relationship_type_count": len(model_item.relationship_types),
            }

            items.append(
                OrderedExplanationEvidenceItem(
                    ordinal=ordinal,
                    subject=subject,
                    status=statement.status,
                    statement=statement.statement,
                    evidence_count=model_item.evidence_count,
                    context_role_count=len(model_item.context_roles),
                    relationship_type_count=len(model_item.relationship_types),
                    order_hash=deterministic_sha256(body),
                )
            )

        items = tuple(items)

        body = {
            "query_id": read_model.query_id,
            "item_hashes": tuple(item.order_hash for item in items),
            "item_count": len(items),
            "read_only": True,
        }

        return ExplanationEvidenceOrdering(
            query_id=read_model.query_id,
            items=items,
            item_count=len(items),
            ordering_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_evidence_ordering() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-049 must remain read-only")

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
        raise AssertionError("OI-049 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_049_REVISION",
    "OrderedExplanationEvidenceItem",
    "ExplanationEvidenceOrdering",
    "ExplanationEvidenceOrderer",
    "verify_explanation_evidence_ordering",
]
