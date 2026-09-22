from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_048_oracle_explanation_readout import OracleExplanationReadout
from .oi_049_explanation_evidence_ordering import ExplanationEvidenceOrdering
from .oi_050_explanation_completeness_evaluation import (
    ExplanationCompletenessEvaluation,
)

BUILD_ID = "OI-051"
OI_051_REVISION = "OI_051_ORACLE_EXPLANATION_DELIVERY_MODEL_V1"

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
TERMINAL_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class OracleExplanationDeliveryModel:
    query_id: str
    subject_hint: str
    completeness_status: str
    headline: str
    ordered_explanations: tuple[str, ...]
    caveats: tuple[str, ...]
    delivered_at: datetime
    delivery_hash: str
    read_only: bool
    terminal_mutation_allowed: bool


class OracleExplanationDeliveryModelBuilder:
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
    terminal_mutation_allowed = False

    def build(
        self,
        *,
        readout: OracleExplanationReadout,
        ordering: ExplanationEvidenceOrdering,
        completeness: ExplanationCompletenessEvaluation,
        delivered_at: datetime,
    ) -> OracleExplanationDeliveryModel:
        if not isinstance(readout, OracleExplanationReadout):
            raise TypeError("readout must be OracleExplanationReadout")
        if not isinstance(ordering, ExplanationEvidenceOrdering):
            raise TypeError(
                "ordering must be ExplanationEvidenceOrdering"
            )
        if not isinstance(
            completeness,
            ExplanationCompletenessEvaluation,
        ):
            raise TypeError(
                "completeness must be ExplanationCompletenessEvaluation"
            )

        if not (
            readout.query_id
            == ordering.query_id
            == completeness.query_id
        ):
            raise ValueError(
                "readout/ordering/completeness query_id mismatch"
            )

        if not isinstance(delivered_at, datetime):
            raise TypeError("delivered_at must be datetime")

        if delivered_at.tzinfo is None:
            raise ValueError(
                "delivered_at must be timezone-aware"
            )

        delivered_at = delivered_at.astimezone(timezone.utc)

        ordered_explanations = tuple(
            item.statement
            for item in ordering.items
        )

        caveats = tuple(
            sorted(
                set(readout.caveat_lines)
                | set(completeness.reason_codes)
            )
        )

        body = {
            "query_id": readout.query_id,
            "subject_hint": readout.subject_hint,
            "completeness_status": completeness.status,
            "headline": readout.headline,
            "ordered_explanations": ordered_explanations,
            "caveats": caveats,
            "delivered_at": delivered_at,
            "read_only": True,
            "terminal_mutation_allowed": False,
        }

        return OracleExplanationDeliveryModel(
            query_id=readout.query_id,
            subject_hint=readout.subject_hint,
            completeness_status=completeness.status,
            headline=readout.headline,
            ordered_explanations=ordered_explanations,
            caveats=caveats,
            delivered_at=delivered_at,
            delivery_hash=deterministic_sha256(body),
            read_only=True,
            terminal_mutation_allowed=False,
        )


def verify_oracle_explanation_delivery_model() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-051 must remain read-only")

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
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError("OI-051 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_051_REVISION",
    "OracleExplanationDeliveryModel",
    "OracleExplanationDeliveryModelBuilder",
    "verify_oracle_explanation_delivery_model",
]
