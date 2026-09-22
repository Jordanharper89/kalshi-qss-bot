from __future__ import annotations
from dataclasses import dataclass
from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_055_terminal_explanation_session_adapter import TerminalExplanationSessionTurn

BUILD_ID="OI-056"
OI_056_REVISION="OI_056_EXPLANATION_CONVERSATION_CONTEXT_V1"
READ_ONLY=True
NETWORK_ALLOWED=PERSISTENCE_ALLOWED=PUBLICATION_ALLOWED=False
EXECUTION_ALLOWED=QSERIES_EXECUTION_ALLOWED=False
PREDICTION_ALLOWED=EDGE_SCORE_ALLOWED=PROBABILITY_ALLOWED=False
CAUSAL_CLAIM_ALLOWED=TERMINAL_MUTATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ExplanationConversationContext:
    session_id:str
    turns:tuple[TerminalExplanationSessionTurn,...]
    turn_count:int
    latest_query_id:str|None
    latest_subject_hint:str|None
    latest_completeness_status:str|None
    context_hash:str
    read_only:bool

class ExplanationConversationContextBuilder:
    read_only=True
    network_allowed=persistence_allowed=publication_allowed=False
    execution_allowed=qseries_execution_allowed=False
    prediction_allowed=edge_score_allowed=probability_allowed=False
    causal_claim_allowed=terminal_mutation_allowed=False

    def build(self,*,session_id:str,turns:tuple[TerminalExplanationSessionTurn,...])->ExplanationConversationContext:
        sid=str(session_id).strip()
        if not sid: raise ValueError("session_id must not be empty")
        values=tuple(turns)
        if any(not isinstance(x,TerminalExplanationSessionTurn) for x in values):
            raise TypeError("all turns must be TerminalExplanationSessionTurn")
        if any(x.session_id!=sid for x in values):
            raise ValueError("all turns must belong to the requested session_id")
        if values!=tuple(sorted(values,key=lambda x:x.turn_number)):
            raise ValueError("turns must be supplied in deterministic turn order")
        nums=tuple(x.turn_number for x in values)
        if len(nums)!=len(set(nums)): raise ValueError("duplicate turn_number in conversation context")
        latest=values[-1] if values else None
        body={
            "session_id":sid,"turn_hashes":tuple(x.turn_hash for x in values),
            "turn_count":len(values),
            "latest_query_id":latest.query_id if latest else None,
            "latest_subject_hint":latest.subject_hint if latest else None,
            "latest_completeness_status":latest.completeness_status if latest else None,
            "read_only":True,
        }
        return ExplanationConversationContext(
            session_id=sid,turns=values,turn_count=len(values),
            latest_query_id=latest.query_id if latest else None,
            latest_subject_hint=latest.subject_hint if latest else None,
            latest_completeness_status=latest.completeness_status if latest else None,
            context_hash=deterministic_sha256(body),read_only=True)

def verify_explanation_conversation_context()->bool:
    if READ_ONLY is not True: raise AssertionError("OI-056 must remain read-only")
    if any((NETWORK_ALLOWED,PERSISTENCE_ALLOWED,PUBLICATION_ALLOWED,EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,PREDICTION_ALLOWED,EDGE_SCORE_ALLOWED,
            PROBABILITY_ALLOWED,CAUSAL_CLAIM_ALLOWED,TERMINAL_MUTATION_ALLOWED)):
        raise AssertionError("OI-056 forbidden capability enabled")
    return True

__all__=["BUILD_ID","OI_056_REVISION","ExplanationConversationContext",
         "ExplanationConversationContextBuilder","verify_explanation_conversation_context"]
