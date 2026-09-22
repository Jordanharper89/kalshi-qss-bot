
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import find_historical_market_evidence
from .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline
from .ohl_004_temporal_leakage_guard import guard_historical_timeline
from .ohl_005_historical_learning_candidate_gate import build_historical_learning_candidate
from .ohl_007_historical_evidence_coverage_scanner import verify_ohl_007_historical_evidence_coverage_scanner

OHL_008_BUILD_ID="OHL-008"
OHL_008_REVISION="OHL_008_SETTLED_MARKET_ELIGIBILITY_EVALUATOR_V1"

@dataclass(frozen=True)
class SettledMarketEligibility:
    ticker:str
    eligible:bool
    reason:str
    evidence_count:int
    candidate_id:str

def _row_to_observation(m,ticker):
    row=getattr(m,"row",{}) or {}
    observed_at=(row.get("observed_at") or row.get("timestamp") or row.get("created_at")
                 or row.get("event_ts") or row.get("received_at"))
    if not observed_at:
        return None
    return {
        "observation_id":str(getattr(m,"observation_id","")),
        "market_id":str(ticker),
        "observed_at":str(observed_at),
        "payload":dict(row),
    }

def evaluate_settled_market_eligibility(root,outcome,evidence_limit=50):
    if not verify_ohl_007_historical_evidence_coverage_scanner():
        raise RuntimeError("OHL-007 verification failed")
    ticker=str(getattr(outcome,"ticker",""))
    settled_at=str(getattr(outcome,"settlement_ts",""))
    result=str(getattr(outcome,"result",""))
    if not ticker or not settled_at or not result:
        return SettledMarketEligibility(ticker,False,"MISSING_SETTLEMENT_IDENTITY",0,"")
    matches=tuple(find_historical_market_evidence(Path(root).resolve(),ticker,limit=int(evidence_limit)))
    observations=[]
    for m in matches:
        obs=_row_to_observation(m,ticker)
        if obs is not None:observations.append(obs)
    timeline=reconstruct_settled_market_timeline(ticker,settled_at,result,observations)
    guard=guard_historical_timeline(timeline)
    if not guard.admitted:
        return SettledMarketEligibility(ticker,False,guard.reason,len(timeline.evidence),"")
    candidate=build_historical_learning_candidate(timeline)
    if candidate is None:
        return SettledMarketEligibility(ticker,False,"CANDIDATE_REJECTED",len(timeline.evidence),"")
    return SettledMarketEligibility(ticker,True,"ELIGIBLE",len(timeline.evidence),candidate.candidate_id)

def verify_ohl_008_settled_market_eligibility_evaluator():
    x=SettledMarketEligibility("KX",False,"NO_PRE_SETTLEMENT_EVIDENCE",0,"")
    return not x.eligible and x.evidence_count==0
