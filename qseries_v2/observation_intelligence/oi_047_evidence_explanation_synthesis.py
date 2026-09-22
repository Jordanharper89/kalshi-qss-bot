from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_045_oracle_reasoning_read_model import OracleReasoningReadModel
from .oi_046_explanation_candidate_resolution import (
    ExplanationCandidateResolution,
)

BUILD_ID = "OI-047"
OI_047_REVISION = "OI_047_EVIDENCE_EXPLANATION_SYNTHESIS_V1"

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


class EvidenceExplanationSynthesisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvidenceExplanationStatement:
    subject: str
    status: str
    statement: str
    caveats: tuple[str, ...]
    statement_hash: str


@dataclass(frozen=True, slots=True)
class EvidenceExplanationSynthesis:
    query_id: str
    read_model_hash: str
    resolution_hash: str
    statements: tuple[EvidenceExplanationStatement, ...]
    statement_count: int
    synthesis_hash: str
    read_only: bool
    causal_claim_allowed: bool


class EvidenceExplanationSynthesizer:
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
        read_model: OracleReasoningReadModel,
        resolution: ExplanationCandidateResolution,
    ) -> EvidenceExplanationSynthesis:
        if not isinstance(
            read_model,
            OracleReasoningReadModel,
        ):
            raise TypeError(
                "read_model must be OracleReasoningReadModel"
            )

        if not isinstance(
            resolution,
            ExplanationCandidateResolution,
        ):
            raise TypeError(
                "resolution must be ExplanationCandidateResolution"
            )

        if resolution.read_model_hash != read_model.read_model_hash:
            raise EvidenceExplanationSynthesisError(
                "resolution does not belong to read model"
            )

        read_by_subject = {
            item.subject: item
            for item in read_model.items
        }

        statements = []

        for candidate in resolution.items:
            read_item = read_by_subject.get(
                candidate.subject
            )

            if read_item is None:
                raise EvidenceExplanationSynthesisError(
                    f"read model missing resolved subject: "
                    f"{candidate.subject}"
                )

            context_text = ", ".join(
                read_item.context_roles
            ) or "no structural context"

            relationship_text = ", ".join(
                read_item.relationship_types
            ) or "no structural relationships"

            statement = (
                f"{candidate.subject}: "
                f"{candidate.evidence_count} evidence item(s) "
                f"provide {candidate.support_class} with context "
                f"[{context_text}] and relationships "
                f"[{relationship_text}]."
            )

            caveats = list(candidate.reason_codes)

            caveats.append(
                "structural association does not establish causation"
            )

            if candidate.status != "supported":
                caveats.append(
                    "explanation is incomplete"
                )

            caveats = tuple(
                sorted(set(caveats))
            )

            body = {
                "subject": candidate.subject,
                "status": candidate.status,
                "statement": statement,
                "caveats": caveats,
            }

            statements.append(
                EvidenceExplanationStatement(
                    subject=candidate.subject,
                    status=candidate.status,
                    statement=statement,
                    caveats=caveats,
                    statement_hash=deterministic_sha256(body),
                )
            )

        statements = tuple(
            sorted(
                statements,
                key=lambda item: item.subject,
            )
        )

        body = {
            "query_id": read_model.query_id,
            "read_model_hash": read_model.read_model_hash,
            "resolution_hash": resolution.resolution_hash,
            "statement_hashes": tuple(
                item.statement_hash
                for item in statements
            ),
            "statement_count": len(statements),
            "read_only": True,
            "causal_claim_allowed": False,
        }

        return EvidenceExplanationSynthesis(
            query_id=read_model.query_id,
            read_model_hash=read_model.read_model_hash,
            resolution_hash=resolution.resolution_hash,
            statements=statements,
            statement_count=len(statements),
            synthesis_hash=deterministic_sha256(body),
            read_only=True,
            causal_claim_allowed=False,
        )


def verify_evidence_explanation_synthesis() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-047 must remain read-only"
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
            "OI-047 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_047_REVISION",
    "EvidenceExplanationSynthesisError",
    "EvidenceExplanationStatement",
    "EvidenceExplanationSynthesis",
    "EvidenceExplanationSynthesizer",
    "verify_evidence_explanation_synthesis",
]
