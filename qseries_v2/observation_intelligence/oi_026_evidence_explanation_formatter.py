from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_024_oracle_explanation_read_model import OracleExplanationReadModel
from .oi_025_oracle_explanation_query_engine import OracleExplanationQuery

BUILD_ID = "OI-026"
OI_026_REVISION = "OI_026_EVIDENCE_EXPLANATION_FORMATTER_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = False
PREDICTION_ALLOWED = False
EDGE_SCORE_ALLOWED = False
PROBABILITY_ALLOWED = False


class EvidenceExplanationFormatterError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceExplanationView:
    query_id: str
    title: str
    summary_lines: tuple[str, ...]
    timeline_lines: tuple[str, ...]
    caveat_lines: tuple[str, ...]
    view_hash: str
    read_only: bool
    predictive: bool
    causal_claim_allowed: bool


class EvidenceExplanationFormatter:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False
    causal_claim_allowed = False
    prediction_allowed = False
    edge_score_allowed = False
    probability_allowed = False

    def format(
        self,
        *,
        query: OracleExplanationQuery,
        model: OracleExplanationReadModel,
    ) -> EvidenceExplanationView:
        if not isinstance(query, OracleExplanationQuery):
            raise TypeError("query must be OracleExplanationQuery")

        if not isinstance(model, OracleExplanationReadModel):
            raise TypeError("model must be OracleExplanationReadModel")

        if model.query_id != query.query_id:
            raise EvidenceExplanationFormatterError(
                "query and read model query_id mismatch"
            )

        if model.profile_id != query.profile_id:
            raise EvidenceExplanationFormatterError(
                "query and read model profile_id mismatch"
            )

        title = (
            f"Oracle Evidence Explanation — "
            f"{query.subject_hint}"
        )

        summary_lines = (
            f"Query kind: {query.query_kind}",
            f"Evidence completeness: {model.completeness_status}",
            f"Evidence items: {model.evidence_item_count}",
            f"Distinct sources: {model.distinct_source_count}",
            f"Stale evidence items: {model.stale_evidence_count}",
            f"Supporting relationships: {model.supporting_relationship_count}",
            f"Contradicting relationships: {model.contradicting_relationship_count}",
        )

        timeline_lines = tuple(
            (
                f"{item.ordinal}. {item.evidence_observation_id} "
                f"{item.temporal_relation} change "
                f"({item.seconds_from_change_observation:+d}s); "
                f"agreements={item.agreement_count}; "
                f"contradictions={item.contradiction_count}"
            )
            for item in model.timeline
        )

        caveats = []

        if model.missing_required_evidence:
            caveats.append(
                "Required evidence is incomplete."
            )

        if model.contradicting_relationship_count:
            caveats.append(
                "Contradicting evidence is present."
            )

        if model.stale_evidence_count:
            caveats.append(
                "Stale evidence is present."
            )

        caveats.extend(
            (
                "Temporal association does not establish causation.",
                "No prediction probability or edge score is produced.",
                "Read-only explanation; no trade authorization.",
            )
        )

        body = {
            "query_id": query.query_id,
            "title": title,
            "summary_lines": summary_lines,
            "timeline_lines": timeline_lines,
            "caveat_lines": tuple(caveats),
            "read_only": True,
            "predictive": False,
            "causal_claim_allowed": False,
        }

        return EvidenceExplanationView(
            query_id=query.query_id,
            title=title,
            summary_lines=summary_lines,
            timeline_lines=timeline_lines,
            caveat_lines=tuple(caveats),
            view_hash=deterministic_sha256(body),
            read_only=True,
            predictive=False,
            causal_claim_allowed=False,
        )


def verify_evidence_explanation_formatter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-026 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
            CAUSAL_CLAIM_ALLOWED,
            PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,
        )
    ):
        raise AssertionError("OI-026 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_026_REVISION",
    "EvidenceExplanationFormatterError",
    "EvidenceExplanationView",
    "EvidenceExplanationFormatter",
    "verify_evidence_explanation_formatter",
]
