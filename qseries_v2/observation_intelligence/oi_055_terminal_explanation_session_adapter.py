from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff

BUILD_ID = "OI-055"
OI_055_REVISION = "OI_055_TERMINAL_EXPLANATION_SESSION_ADAPTER_V1"
READ_ONLY = True
NETWORK_ALLOWED = PERSISTENCE_ALLOWED = PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = QSERIES_EXECUTION_ALLOWED = False
PREDICTION_ALLOWED = EDGE_SCORE_ALLOWED = PROBABILITY_ALLOWED = False
CAUSAL_CLAIM_ALLOWED = TERMINAL_MUTATION_ALLOWED = False

@dataclass(frozen=True, slots=True)
class TerminalExplanationSessionTurn:
    session_id: str
    turn_number: int
    query_id: str
    response_id: str
    subject_hint: str
    completeness_status: str
    display_payload: tuple[str, ...]
    received_at: datetime
    turn_hash: str
    read_only: bool

class TerminalExplanationSessionAdapter:
    read_only = True
    network_allowed = persistence_allowed = publication_allowed = False
    execution_allowed = qseries_execution_allowed = False
    prediction_allowed = edge_score_allowed = probability_allowed = False
    causal_claim_allowed = terminal_mutation_allowed = False

    def adapt(self, *, session_id: str, turn_number: int,
              handoff: ExplanationTerminalHandoff,
              received_at: datetime) -> TerminalExplanationSessionTurn:
        sid = str(session_id).strip()
        if not sid:
            raise ValueError("session_id must not be empty")
        if not isinstance(turn_number, int) or turn_number < 1:
            raise ValueError("turn_number must be a positive integer")
        if not isinstance(handoff, ExplanationTerminalHandoff):
            raise TypeError("handoff must be ExplanationTerminalHandoff")
        if not isinstance(received_at, datetime):
            raise TypeError("received_at must be datetime")
        if received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")
        received_at = received_at.astimezone(timezone.utc)
        body = {
            "session_id": sid, "turn_number": turn_number,
            "query_id": handoff.query_id, "response_id": handoff.response_id,
            "subject_hint": handoff.subject_hint,
            "completeness_status": handoff.completeness_status,
            "display_payload": handoff.display_payload,
            "received_at": received_at, "read_only": True,
        }
        return TerminalExplanationSessionTurn(
            session_id=sid, turn_number=turn_number,
            query_id=handoff.query_id, response_id=handoff.response_id,
            subject_hint=handoff.subject_hint,
            completeness_status=handoff.completeness_status,
            display_payload=handoff.display_payload,
            received_at=received_at,
            turn_hash=deterministic_sha256(body),
            read_only=True,
        )

def verify_terminal_explanation_session_adapter() -> bool:
    if READ_ONLY is not True:
        raise AssertionError("OI-055 must remain read-only")
    if any((NETWORK_ALLOWED, PERSISTENCE_ALLOWED, PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED, QSERIES_EXECUTION_ALLOWED, PREDICTION_ALLOWED,
            EDGE_SCORE_ALLOWED, PROBABILITY_ALLOWED, CAUSAL_CLAIM_ALLOWED,
            TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-055 forbidden capability enabled")
    return True

__all__ = [
    "BUILD_ID","OI_055_REVISION","TerminalExplanationSessionTurn",
    "TerminalExplanationSessionAdapter",
    "verify_terminal_explanation_session_adapter",
]
