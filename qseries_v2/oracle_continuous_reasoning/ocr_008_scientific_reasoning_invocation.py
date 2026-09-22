from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import CapabilityReasoningState,synthesize_capabilities
from qseries_v2.oracle_scientific_reasoning.osr_029_intelligence_state import build_oracle_scientific_intelligence_state,verify_oracle_scientific_intelligence_state

OCR_008_BUILD_ID="OCR-008"
OCR_008_REVISION="OCR_008_CONTINUOUS_SCIENTIFIC_REASONING_INVOCATION_V1"

@dataclass(frozen=True)
class LiveScientificReasoningResult:
    market_ticker:str
    observation_count:int
    osr_state:object
    read_only:bool=True

def invoke_frozen_scientific_reasoning(market_ticker,observations):
    rows=tuple(observations)
    if not market_ticker or not rows:raise ValueError("market and observations required")
    event_types={str((x.source_row.get("observation_type") or x.source_row.get("event_type") or "")).lower() for x in rows}
    n=len(rows)
    diversity=max(1,len(event_types))
    support=min(0.95,0.45+min(n,20)/40.0)
    confidence=min(0.95,0.50+min(diversity,4)*0.08+min(n,20)/100.0)
    contradiction=max(0.0,min(0.35,(diversity-1)*0.05))
    abstain=n<2
    cap=CapabilityReasoningState("live_market_observation",support,confidence,contradiction,abstain)
    synthesis=synthesize_capabilities((cap,))
    state=build_oracle_scientific_intelligence_state(market_ticker,synthesis)
    if not verify_oracle_scientific_intelligence_state(state):raise RuntimeError("Frozen OSR state verification failed")
    return LiveScientificReasoningResult(market_ticker,n,state,True)

def reason_over_market_aware_observations(observations):
    groups={}
    for x in observations:groups.setdefault(x.market_ticker,[]).append(x)
    return tuple(invoke_frozen_scientific_reasoning(k,groups[k]) for k in sorted(groups))

def verify_ocr_008_continuous_scientific_reasoning_invocation():
    from .ocr_007_umd_context_join import join_rows_to_umd_context
    obs=join_rows_to_umd_context(({"observation_id":"1","ticker":"KXTEST"},{"observation_id":"2","ticker":"KXTEST"}))
    r=reason_over_market_aware_observations(obs)
    return len(r)==1 and r[0].osr_state.read_only and not r[0].osr_state.execution_allowed
