from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_054_explanation_terminal_handoff_boundary import ExplanationTerminalHandoff
from .oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionAdapter,TerminalExplanationSessionTurn
from .oi_056_explanation_conversation_context import ExplanationConversationContext,ExplanationConversationContextBuilder

BUILD_ID="OI-057"
OI_057_REVISION="OI_057_EXPLANATION_RESPONSE_COORDINATOR_V1"
READ_ONLY=True
NETWORK_ALLOWED=PERSISTENCE_ALLOWED=PUBLICATION_ALLOWED=False
EXECUTION_ALLOWED=QSERIES_EXECUTION_ALLOWED=False
PREDICTION_ALLOWED=EDGE_SCORE_ALLOWED=PROBABILITY_ALLOWED=False
CAUSAL_CLAIM_ALLOWED=TERMINAL_MUTATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class OracleExplanationCoordinatedResponse:
    session_id:str
    turn:TerminalExplanationSessionTurn
    context:ExplanationConversationContext
    response_hash:str
    read_only:bool

class OracleExplanationResponseCoordinator:
    read_only=True
    network_allowed=persistence_allowed=publication_allowed=False
    execution_allowed=qseries_execution_allowed=False
    prediction_allowed=edge_score_allowed=probability_allowed=False
    causal_claim_allowed=terminal_mutation_allowed=False

    def __init__(self):
        self._adapter=TerminalExplanationSessionAdapter()
        self._context=ExplanationConversationContextBuilder()

    def coordinate(self,*,session_id:str,prior_turns:tuple[TerminalExplanationSessionTurn,...],
                   handoff:ExplanationTerminalHandoff,received_at:datetime)->OracleExplanationCoordinatedResponse:
        sid=str(session_id).strip()
        if not sid: raise ValueError("session_id must not be empty")
        prior=tuple(prior_turns)
        if any(not isinstance(x,TerminalExplanationSessionTurn) for x in prior):
            raise TypeError("all prior_turns must be TerminalExplanationSessionTurn")
        if any(x.session_id!=sid for x in prior):
            raise ValueError("all prior_turns must belong to session_id")
        if prior!=tuple(sorted(prior,key=lambda x:x.turn_number)):
            raise ValueError("prior_turns must be supplied in turn order")
        next_number=(prior[-1].turn_number+1) if prior else 1
        turn=self._adapter.adapt(session_id=sid,turn_number=next_number,handoff=handoff,received_at=received_at)
        context=self._context.build(session_id=sid,turns=prior+(turn,))
        body={"session_id":sid,"turn_hash":turn.turn_hash,"context_hash":context.context_hash,"read_only":True}
        return OracleExplanationCoordinatedResponse(
            session_id=sid,turn=turn,context=context,
            response_hash=deterministic_sha256(body),read_only=True)

def verify_explanation_response_coordinator()->bool:
    if READ_ONLY is not True: raise AssertionError("OI-057 must remain read-only")
    if any((NETWORK_ALLOWED,PERSISTENCE_ALLOWED,PUBLICATION_ALLOWED,EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,PREDICTION_ALLOWED,EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,CAUSAL_CLAIM_ALLOWED,TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-057 forbidden capability enabled")
    return True

__all__=["BUILD_ID","OI_057_REVISION","OracleExplanationCoordinatedResponse",
         "OracleExplanationResponseCoordinator","verify_explanation_response_coordinator"]
