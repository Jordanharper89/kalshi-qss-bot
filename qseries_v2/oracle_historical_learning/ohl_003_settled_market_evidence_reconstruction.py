from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .ohl_002_postgresql_historical_observation_read_boundary import verify_ohl_002_postgresql_historical_observation_read_boundary

OHL_003_BUILD_ID="OHL-003"
OHL_003_REVISION="OHL_003_SETTLED_MARKET_EVIDENCE_RECONSTRUCTION_V1"

@dataclass(frozen=True)
class HistoricalObservation:
    observation_id:str
    market_id:str
    observed_at:str
    payload:dict

@dataclass(frozen=True)
class SettledMarketTimeline:
    market_id:str
    settled_at:str
    outcome:str
    evidence:tuple
    rejected_post_settlement:int

def _dt(v):
    if isinstance(v,datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    s=str(v).replace("Z","+00:00")
    x=datetime.fromisoformat(s)
    return x if x.tzinfo else x.replace(tzinfo=timezone.utc)

def reconstruct_settled_market_timeline(market_id,settled_at,outcome,observations):
    if not verify_ohl_002_postgresql_historical_observation_read_boundary():
        raise RuntimeError("OHL-002 verification failed")
    cutoff=_dt(settled_at)
    accepted=[]; rejected=0
    for raw in observations:
        o=raw if isinstance(raw,HistoricalObservation) else HistoricalObservation(
            str(raw["observation_id"]),str(raw["market_id"]),str(raw["observed_at"]),dict(raw.get("payload") or {}))
        if o.market_id != str(market_id):
            continue
        if _dt(o.observed_at) < cutoff:
            accepted.append(o)
        else:
            rejected += 1
    accepted.sort(key=lambda x:(_dt(x.observed_at),x.observation_id))
    return SettledMarketTimeline(str(market_id),str(settled_at),str(outcome),tuple(accepted),rejected)

def verify_ohl_003_settled_market_evidence_reconstruction():
    x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[
        {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}},
        {"observation_id":"2","market_id":"M","observed_at":"2026-01-03T00:00:00Z","payload":{}},
    ])
    return len(x.evidence)==1 and x.rejected_post_settlement==1 and x.outcome=="YES"
