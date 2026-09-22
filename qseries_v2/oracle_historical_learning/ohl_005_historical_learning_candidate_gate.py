from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .ohl_004_temporal_leakage_guard import guard_historical_timeline,verify_ohl_004_temporal_leakage_guard

OHL_005_BUILD_ID="OHL-005"
OHL_005_REVISION="OHL_005_HISTORICAL_LEARNING_CANDIDATE_GATE_V1"

@dataclass(frozen=True)
class HistoricalLearningCandidate:
    candidate_id:str
    market_id:str
    outcome:str
    settled_at:str
    evidence_ids:tuple
    admission_reason:str
    execution_authority:bool=False

def build_historical_learning_candidate(timeline):
    if not verify_ohl_004_temporal_leakage_guard():
        raise RuntimeError("OHL-004 verification failed")
    guard=guard_historical_timeline(timeline)
    if not guard.admitted:
        return None
    evidence_ids=tuple(o.observation_id for o in timeline.evidence)
    payload={"market_id":timeline.market_id,"outcome":timeline.outcome,
             "settled_at":timeline.settled_at,"evidence_ids":evidence_ids}
    cid=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return HistoricalLearningCandidate(cid,timeline.market_id,timeline.outcome,timeline.settled_at,
                                       evidence_ids,"TEMPORALLY_CLEAN_SETTLED_HISTORY",False)

def verify_ohl_005_historical_learning_candidate_gate():
    from .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline
    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[
        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}
    ])
    c=build_historical_learning_candidate(x)
    return c is not None and len(c.candidate_id)==64 and not c.execution_authority
