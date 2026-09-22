from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class SportsReasoningReadiness:
    market_id: str
    state: str
    independent_evidence_count: int
    independent_source_count: int
    ready_for_evidence_comparison: bool
    ready_for_prediction: bool
    direction: None=None
    probability: None=None
    execution_authority: bool=False

def evaluate_sports_reasoning_readiness(inputs):
    out=[]
    for x in tuple(inputs):
        evidence_count=int(x.independent_evidence_count)
        source_count=len(tuple(x.independent_source_ids))
        ready=evidence_count>0 and source_count>0
        out.append(SportsReasoningReadiness(
            market_id=x.market_id,
            state="READY_FOR_EVIDENCE_COMPARISON" if ready else "OBSERVE",
            independent_evidence_count=evidence_count,
            independent_source_count=source_count,
            ready_for_evidence_comparison=ready,
            ready_for_prediction=False,
            direction=None,
            probability=None,
            execution_authority=False,
        ))
    return tuple(out)
