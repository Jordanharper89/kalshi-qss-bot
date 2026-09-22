from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False
DIRECTION_ENABLED=False

DEFAULT_MAX_ALIGNMENT_SPAN_SECONDS=1800.0

@dataclass(frozen=True,slots=True)
class CryptoEvidenceComparisonState:
    asset:str
    state:str
    market_observation_count:int
    chain_observation_count:int
    observation_time_span_seconds:float|None
    independent_chain_evidence:bool
    market_native_reference:bool
    ready_for_evidence_comparison:bool
    ready_for_prediction:bool=False
    direction:None=None
    probability:None=None

def build_crypto_evidence_comparison_states(alignments,max_alignment_span_seconds=DEFAULT_MAX_ALIGNMENT_SPAN_SECONDS):
    out=[]
    for a in tuple(alignments):
        span=a.observation_time_span_seconds
        fresh=(span is None or (0.0 <= span <= float(max_alignment_span_seconds)))
        ready=bool(a.evidence_comparison_possible and fresh)
        if ready:
            state="READY_FOR_EVIDENCE_COMPARISON"
        elif a.market_source_present or a.chain_source_present:
            state="OBSERVE"
        else:
            state="NO_CURRENT_EVIDENCE"
        out.append(CryptoEvidenceComparisonState(
            a.asset,state,len(a.market_observations),len(a.chain_observations),span,
            bool(a.chain_source_present),bool(a.market_source_present),ready,
            False,None,None
        ))
    return tuple(out)
