from __future__ import annotations

from dataclasses import dataclass

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_053_explanation_query_response_package import (
    ExplanationQueryResponsePackage,
)

BUILD_ID = "OI-054"
OI_054_REVISION = "OI_054_EXPLANATION_TERMINAL_HANDOFF_BOUNDARY_V1"

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
class ExplanationTerminalHandoff:
    response_id: str
    query_id: str
    subject_hint: str
    completeness_status: str
    display_payload: tuple[str, ...]
    handoff_hash: str
    read_only: bool
    terminal_mutation_allowed: bool


class ExplanationTerminalHandoffBoundary:
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

    def handoff(
        self,
        package: ExplanationQueryResponsePackage,
    ) -> ExplanationTerminalHandoff:
        if not isinstance(
            package,
            ExplanationQueryResponsePackage,
        ):
            raise TypeError(
                "package must be ExplanationQueryResponsePackage"
            )

        lines = [
            "=" * 64,
            package.title,
            f"STATUS: {package.completeness_status.upper()}",
            "",
        ]

        lines.extend(package.body_lines)

        if package.caveat_lines:
            lines.append("")
            lines.append("CAVEATS:")
            lines.extend(
                f"- {item}"
                for item in package.caveat_lines
            )

        lines.append("")
        lines.append(package.footer)
        lines.append("=" * 64)

        display_payload = tuple(lines)

        body = {
            "response_id": package.response_id,
            "query_id": package.query_id,
            "subject_hint": package.subject_hint,
            "completeness_status": package.completeness_status,
            "display_payload": display_payload,
            "read_only": True,
            "terminal_mutation_allowed": False,
        }

        return ExplanationTerminalHandoff(
            response_id=package.response_id,
            query_id=package.query_id,
            subject_hint=package.subject_hint,
            completeness_status=package.completeness_status,
            display_payload=display_payload,
            handoff_hash=deterministic_sha256(body),
            read_only=True,
            terminal_mutation_allowed=False,
        )


def verify_explanation_terminal_handoff_boundary() -> bool:
    if READ_ONLY is not True:
        raise AssertionError(
            "OI-054 must remain read-only"
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
            "OI-054 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_054_REVISION",
    "ExplanationTerminalHandoff",
    "ExplanationTerminalHandoffBoundary",
    "verify_explanation_terminal_handoff_boundary",
]
