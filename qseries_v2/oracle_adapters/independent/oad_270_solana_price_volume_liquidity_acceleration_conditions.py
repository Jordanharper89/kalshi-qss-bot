from __future__ import annotations
from dataclasses import dataclass
from .oad_268_solana_liquidity_add_remove_change_detection import build_pool_liquidity_deltas
from .oad_269_solana_buy_sell_volume_pressure_history import build_pool_pressure_history

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaAccelerationCondition:
    source_id:str
    pair_address:str
    observed_at:str
    conditions:tuple
    evidence_count:int
    state:str
    probability:None=None
    direction:None=None
    execution_authority:bool=False

def _sign(v,pos,neg,zero="FLAT",unknown="UNKNOWN"):
    if v is None:return unknown
    if v>0:return pos
    if v<0:return neg
    return zero

def build_solana_acceleration_conditions(records):
    liq={(x.source_id,x.pair_address):x for x in build_pool_liquidity_deltas(records)}
    pressure={(x.source_id,x.pair_address):x for x in build_pool_pressure_history(records)}
    out=[]
    for key in sorted(set(liq)&set(pressure)):
        l=liq[key]; p=pressure[key]
        conditions=(
            ("liquidity",_sign(l.liquidity_change_usd,"RISING","FALLING")),
            ("volume",_sign(p.volume_change,"RISING","FALLING")),
            ("price",_sign(p.price_change_fraction,"RISING","FALLING")),
            ("order_flow",p.state),
        )
        known=sum(1 for _,v in conditions if v!="UNKNOWN")
        state="COMPOSITE_READY" if known>=3 else "PARTIAL"
        out.append(SolanaAccelerationCondition(l.source_id,l.pair_address,p.current_observed_at,conditions,known,state,None,None,False))
    return tuple(out)
