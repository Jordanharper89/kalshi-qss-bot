from __future__ import annotations
from dataclasses import dataclass
from .oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class PoolLiquidityDelta:
    source_id:str
    token_address:str
    pair_address:str
    previous_observed_at:str
    current_observed_at:str
    previous_liquidity_usd:float|None
    current_liquidity_usd:float|None
    liquidity_change_usd:float|None
    liquidity_change_fraction:float|None
    state:str
    execution_authority:bool=False

def _num(v):
    try:
        return float(v)
    except (TypeError,ValueError):
        return None

def build_pool_liquidity_deltas(records):
    grouped={}
    for r in tuple(records):
        if r.observation_type!="solana_token_pool_identity_liquidity":
            continue
        grouped.setdefault(r.source_id,[]).append(r)

    out=[]
    for source_id,rows in grouped.items():
        rows=sorted(rows,key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id))
        if len(rows)<2:
            continue
        a,b=rows[-2],rows[-1]
        pa={str(x.get("pair_address")):x for x in tuple(a.payload.get("pools") or ()) if x.get("pair_address")}
        pb={str(x.get("pair_address")):x for x in tuple(b.payload.get("pools") or ()) if x.get("pair_address")}
        for pair in sorted(set(pa)&set(pb)):
            av=_num(pa[pair].get("liquidity_usd")); bv=_num(pb[pair].get("liquidity_usd"))
            delta=None if av is None or bv is None else bv-av
            frac=None if delta is None or not av else delta/av
            state="UNKNOWN" if delta is None else ("LIQUIDITY_ADDED" if delta>0 else "LIQUIDITY_REMOVED" if delta<0 else "UNCHANGED")
            out.append(PoolLiquidityDelta(
                source_id,
                str(b.payload.get("token_address") or ""),
                pair,
                a.observed_at,b.observed_at,
                av,bv,delta,frac,state,False,
            ))
    return tuple(out)
