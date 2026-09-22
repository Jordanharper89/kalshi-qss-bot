\

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_313_solana_outcome_pending_temporal_cases import SolanaOutcomePendingCase

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaVerifiedForwardOutcome:
    experience_id:str; token_address:str; pair_address:str; horizon_seconds:int
    anchor_at:str; outcome_at:str; anchor_price:float; outcome_price:float
    return_fraction:float; outcome_class:str; evidence_observation_ids:tuple
    verified:bool=True; execution_authority:bool=False

def _dt(v): return datetime.fromisoformat(str(v).replace("Z","+00:00"))
def _price_for_pair(record,pair):
    for p in tuple(record.payload.get("pools") or ()):
        if str(p.get("pair_address") or "")==str(pair):
            try:return float(p.get("price_usd"))
            except (TypeError,ValueError):return None
    return None

def attribute_forward_outcomes(cases,records,tolerance_seconds=8.0):
    rows=tuple(sorted(records,key=lambda r:_dt(r.observed_at)))
    out=[]
    for c in cases:
        anchor_t=_dt(c.snapshot_at); target=anchor_t.timestamp()+c.horizon_seconds
        anchor_candidates=[r for r in rows if r.observation_id in set(c.evidence_observation_ids)]
        if not anchor_candidates: continue
        anchor=anchor_candidates[-1]; ap=_price_for_pair(anchor,c.pair_address)
        candidates=[r for r in rows if _dt(r.observed_at).timestamp()>=target and _dt(r.observed_at).timestamp()<=target+float(tolerance_seconds)]
        for r in candidates:
            op=_price_for_pair(r,c.pair_address)
            if ap is None or op is None or ap==0: continue
            ret=(op-ap)/ap
            cls="UP" if ret>0 else "DOWN" if ret<0 else "FLAT"
            out.append(SolanaVerifiedForwardOutcome(c.experience_id,c.token_address,c.pair_address,c.horizon_seconds,c.snapshot_at,r.observed_at,ap,op,ret,cls,tuple(c.evidence_observation_ids)+(r.observation_id,),True,False))
            break
    return tuple(out)

