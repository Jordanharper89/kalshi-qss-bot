from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_051_oracle_explanation_delivery_model import (
    OracleExplanationDeliveryModel,
)

BUILD_ID = "OI-052"
OI_052_REVISION = "OI_052_TERMINAL_EXPLANATION_ADAPTER_V1"

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
class TerminalExplanationView:
    query_id: str
    subject_hint: str
    completeness_status: str
    title: str
    body_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    footer: str
    view_hash: str
    read_only: bool


class TerminalExplanationAdapter:
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

    def adapt(
        self,
        delivery: OracleExplanationDeliveryModel,
    ) -> TerminalExplanationView:
        if not isinstance(
            delivery,
            OracleExplanationDeliveryModel,
        ):
            raise TypeError(
                "delivery must be OracleExplanationDeliveryModel"
            )

        body_lines = tuple(delivery.ordered_explanations)

        caveat_lines = tuple(delivery.caveats)

        footer = (
            "MODE: READ-ONLY | "
            "NO TRADE AUTHORIZATION | "
            "NO CAUSAL CLAIM"
        )

        body = {
            "query_id": delivery.query_id,
            "subject_hint": delivery.subject_hint,
            "completeness_status": delivery.completeness_status,
            "title": delivery.headline,
            "body_lines": body_lines,
            "caveat_lines": caveat_lines,
            "footer": footer,
            "read_only": True,
        }

        return TerminalExplanationView(
            query_id=delivery.query_id,
            subject_hint=delivery.subject_hint,
            completeness_status=delivery.completeness_status,
            title=delivery.headline,
            body_lines=body_lines,
            caveat_lines=caveat_lines,
            footer=footer,
            view_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_terminal_explanation_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-052 must remain read-only")

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
        raise AssertionError("OI-052 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_052_REVISION",
    "TerminalExplanationView",
    "TerminalExplanationAdapter",
    "verify_terminal_explanation_adapter",
]
