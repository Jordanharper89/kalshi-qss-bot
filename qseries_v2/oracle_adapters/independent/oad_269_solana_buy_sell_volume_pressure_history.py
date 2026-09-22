from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class PoolPressureDelta:
    source_id:str
    pair_address:str
    previous_observed_at:str
    current_observed_at:str
    buys_h24:int|None
    sells_h24:int|None
    buy_sell_imbalance:int|None
    volume_h24:float|None
    volume_change:float|None
    price_usd:float|None
    price_change_fraction:float|None
    state:str
    execution_authority:bool=False

def _num(v):
    try:return float(v)
    except (TypeError,ValueError):return None

def _int(v):
    try:return int(v)
    except (TypeError,ValueError):return None

def build_pool_pressure_history(records):
    grouped={}
    for r in tuple(records):
        if r.observation_type=="solana_token_pool_identity_liquidity":
            grouped.setdefault(r.source_id,[]).append(r)
    out=[]
    for source_id,rows in grouped.items():
        rows=sorted(rows,key=lambda x:(-1 if x.sequence_number is None else int(x.sequence_number),x.observed_at,x.observation_id))
        if len(rows)<2: continue
        a,b=rows[-2],rows[-1]
        pa={str(x.get("pair_address")):x for x in tuple(a.payload.get("pools") or ()) if x.get("pair_address")}
        pb={str(x.get("pair_address")):x for x in tuple(b.payload.get("pools") or ()) if x.get("pair_address")}
        for pair in sorted(set(pa)&set(pb)):
            old,new=pa[pair],pb[pair]
            buys=_int(new.get("buys_h24")); sells=_int(new.get("sells_h24"))
            imbalance=None if buys is None or sells is None else buys-sells
            vold=_num(old.get("volume_h24")); vnew=_num(new.get("volume_h24"))
            vdelta=None if vold is None or vnew is None else vnew-vold
            pold=_num(old.get("price_usd")); pnew=_num(new.get("price_usd"))
            pfrac=None if pold is None or pnew is None or not pold else (pnew-pold)/pold
            if imbalance is None: state="UNKNOWN"
            elif imbalance>0: state="BUY_PRESSURE"
            elif imbalance<0: state="SELL_PRESSURE"
            else: state="BALANCED"
            out.append(PoolPressureDelta(source_id,pair,a.observed_at,b.observed_at,buys,sells,imbalance,vnew,vdelta,pnew,pfrac,state,False))
    return tuple(out)
