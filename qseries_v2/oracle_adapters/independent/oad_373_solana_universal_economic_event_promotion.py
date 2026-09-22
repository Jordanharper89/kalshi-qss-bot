\

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PROMOTABLE_BEHAVIORS=frozenset({
    "DEX_SWAP","ASSET_EXCHANGE_FLOW","TOKEN_FLOW","FINAL_VERIFIED_ASSET_EXCHANGE_FLOW",
    "FINAL_VERIFIED_TOKEN_FLOW","FINAL_VERIFIED_INTERACTION_UNRESOLVED",
    "PROTOCOL_ASSET_EXCHANGE_FLOW","ORDERBOOK_TRADE","ROUTED_SWAP"
})

@dataclass(frozen=True, slots=True)
class SolanaPromotedEconomicEvent:
    event_id:str
    slot:int
    block_time:float|None
    signature:str|None
    behavior_type:str
    protocol:str|None
    primary_asset:str|None
    secondary_asset:str|None
    wallet:str|None
    magnitude:float|None
    source:str
    promotable:bool
    execution_authority:bool=False

def _get(x,*names,default=None):
    for n in names:
        if isinstance(x,dict) and n in x:
            return x[n]
        if hasattr(x,n):
            return getattr(x,n)
    return default

def promote_economic_behavior(x:Any):
    behavior=str(_get(x,"behavior_type","event_type","type","kind",default="UNKNOWN"))
    slot=int(_get(x,"slot","block_slot",default=0) or 0)
    sig=_get(x,"signature","transaction_signature",default=None)
    eid=str(_get(x,"event_id","observation_id","id",default=f"{slot}:{sig}:{behavior}"))
    protocol=_get(x,"protocol","protocol_id","dex_id","program_name",default=None)
    asset=_get(x,"primary_asset","mint","asset","token_mint",default=None)
    secondary=_get(x,"secondary_asset","quote_asset","counter_asset","other_mint",default=None)
    wallet=_get(x,"wallet","owner","authority",default=None)
    magnitude=_get(x,"magnitude","amount","notional","delta",default=None)
    try:
        magnitude=None if magnitude is None else float(magnitude)
    except Exception:
        magnitude=None
    promotable=behavior.upper() in {x.upper() for x in PROMOTABLE_BEHAVIORS} or any(k in behavior.upper() for k in ("SWAP","FLOW","TRADE"))
    return SolanaPromotedEconomicEvent(
        eid,slot,_get(x,"block_time","timestamp",default=None),sig,behavior,
        None if protocol is None else str(protocol),
        None if asset is None else str(asset),
        None if secondary is None else str(secondary),
        None if wallet is None else str(wallet),
        magnitude,"SOLANA_UNIVERSAL_CHAIN",promotable,False
    )

def promote_economic_behaviors(items):
    return tuple(y for y in (promote_economic_behavior(x) for x in items) if y.promotable)

