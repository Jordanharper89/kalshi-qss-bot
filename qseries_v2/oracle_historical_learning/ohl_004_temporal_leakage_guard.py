from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .ohl_003_settled_market_evidence_reconstruction import SettledMarketTimeline,verify_ohl_003_settled_market_evidence_reconstruction

OHL_004_BUILD_ID="OHL-004"
OHL_004_REVISION="OHL_004_TEMPORAL_LEAKAGE_GUARD_V1"

@dataclass(frozen=True)
class LeakageGuardResult:
    admitted:bool
    reason:str
    evidence_count:int

def _dt(v):
    s=str(v).replace("Z","+00:00")
    x=datetime.fromisoformat(s)
    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)

def guard_historical_timeline(timeline:SettledMarketTimeline):
    if not verify_ohl_003_settled_market_evidence_reconstruction():
        raise RuntimeError("OHL-003 verification failed")
    if not timeline.outcome:
        return LeakageGuardResult(False,"MISSING_SETTLED_OUTCOME",len(timeline.evidence))
    if not timeline.evidence:
        return LeakageGuardResult(False,"NO_PRE_SETTLEMENT_EVIDENCE",0)
    cutoff=_dt(timeline.settled_at)
    if any(_dt(o.observed_at) >= cutoff for o in timeline.evidence):
        return LeakageGuardResult(False,"POST_SETTLEMENT_LEAKAGE",len(timeline.evidence))
    return LeakageGuardResult(True,"TEMPORALLY_CLEAN",len(timeline.evidence))

def verify_ohl_004_temporal_leakage_guard():
    from .ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline
    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[
        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}
    ])
    g=guard_historical_timeline(x)
    return g.admitted and g.reason=="TEMPORALLY_CLEAN"
