from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery
from .oi_047_evidence_explanation_synthesis import (
    EvidenceExplanationSynthesis,
)

BUILD_ID = "OI-048"
OI_048_REVISION = "OI_048_ORACLE_EXPLANATION_READOUT_V1"

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


class OracleExplanationReadoutError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OracleExplanationReadout:
    query_id: str
    query_kind: str
    subject_hint: str
    headline: str
    explanation_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    built_at: datetime
    readout_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool
    terminal_mutation_allowed: bool


class OracleExplanationReadoutBuilder:
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
        query: OracleExplanationQuery,
        synthesis: EvidenceExplanationSynthesis,
        built_at: datetime,
    ) -> OracleExplanationReadout:
        if not isinstance(
            query,
            OracleExplanationQuery,
        ):
            raise TypeError(
                "query must be OracleExplanationQuery"
            )

        if not isinstance(
            synthesis,
            EvidenceExplanationSynthesis,
        ):
            raise TypeError(
                "synthesis must be EvidenceExplanationSynthesis"
            )

        if synthesis.query_id != query.query_id:
            raise OracleExplanationReadoutError(
                "query and synthesis query_id mismatch"
            )

        if not isinstance(built_at, datetime):
            raise TypeError(
                "built_at must be datetime"
            )

        if built_at.tzinfo is None:
            raise OracleExplanationReadoutError(
                "built_at must be timezone-aware"
            )

        built_at = built_at.astimezone(
            timezone.utc
        )

        explanation_lines = tuple(
            item.statement
            for item in synthesis.statements
        )

        caveats = tuple(
            sorted(
                {
                    caveat
                    for item in synthesis.statements
                    for caveat in item.caveats
                }
            )
        )

        headline = (
            f"Oracle Evidence Explanation — "
            f"{query.subject_hint}"
        )

        body = {
            "query_id": query.query_id,
            "query_kind": query.query_kind,
            "subject_hint": query.subject_hint,
            "headline": headline,
            "explanation_lines": explanation_lines,
            "caveat_lines": caveats,
            "built_at": built_at,
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
            "terminal_mutation_allowed": False,
        }

        return OracleExplanationReadout(
            query_id=query.query_id,
            query_kind=query.query_kind,
            subject_hint=query.subject_hint,
            headline=headline,
            explanation_lines=explanation_lines,
            caveat_lines=caveats,
            built_at=built_at,
            readout_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
            terminal_mutation_allowed=False,
        )


def verify_oracle_explanation_readout() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-048 must remain read-only"
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
            "OI-048 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_048_REVISION",
    "OracleExplanationReadoutError",
    "OracleExplanationReadout",
    "OracleExplanationReadoutBuilder",
    "verify_oracle_explanation_readout",
]
