from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_052_terminal_explanation_adapter import TerminalExplanationView

BUILD_ID = "OI-053"
OI_053_REVISION = "OI_053_EXPLANATION_QUERY_RESPONSE_PACKAGE_V1"

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
class ExplanationQueryResponsePackage:
    response_id: str
    query_id: str
    query_kind: str
    subject_hint: str
    completeness_status: str
    title: str
    body_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    footer: str
    assembled_at: datetime
    response_hash: str
    read_only: bool


class ExplanationQueryResponsePackageBuilder:
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
        response_id: str,
        query: OracleExplanationQuery,
        view: TerminalExplanationView,
        assembled_at: datetime,
    ) -> ExplanationQueryResponsePackage:
        response_id_value = str(response_id).strip()

        if not response_id_value:
            raise ValueError(
                "response_id must not be empty"
            )

        if not isinstance(query, OracleExplanationQuery):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(view, TerminalExplanationView):
            raise TypeError(
                "view must be TerminalExplanationView"
            )

        if query.query_id != view.query_id:
            raise ValueError(
                "query/view query_id mismatch"
            )

        if not isinstance(assembled_at, datetime):
            raise TypeError(
                "assembled_at must be datetime"
            )

        if assembled_at.tzinfo is None:
            raise ValueError(
                "assembled_at must be timezone-aware"
            )

        assembled_at = assembled_at.astimezone(
            timezone.utc
        )

        body = {
            "response_id": response_id_value,
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "completeness_status": view.completeness_status,
            "title": view.title,
            "body_lines": view.body_lines,
            "caveat_lines": view.caveat_lines,
            "footer": view.footer,
            "assembled_at": assembled_at,
            "read_only": True,
        }

        return ExplanationQueryResponsePackage(
            response_id=response_id_value,
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            completeness_status=view.completeness_status,
            title=view.title,
            body_lines=view.body_lines,
            caveat_lines=view.caveat_lines,
            footer=view.footer,
            assembled_at=assembled_at,
            response_hash=deterministic_sha256(body),
            read_only=True,
        )


def verify_explanation_query_response_package() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-053 must remain read-only"
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
            TERMINAL_MUTATION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-053 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_053_REVISION",
    "ExplanationQueryResponsePackage",
    "ExplanationQueryResponsePackageBuilder",
    "verify_explanation_query_response_package",
]
