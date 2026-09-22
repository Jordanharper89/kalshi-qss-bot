from __future__ import annotations
from dataclasses import dataclass
from .oad_299_gmgn_solana_trader_intelligence import acquire_current_gmgn_holder_and_trader_pair
READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class ProviderClaim:
    wallet_address:str|None
    claim_kind:str
    provider:str
    claim_payload:dict
    oracle_verified:bool=False
@dataclass(frozen=True,slots=True)
class WalletTraderIntelligence:
    token_address:str
    holder_rows:int
    trader_rows:int
    provider_claims:tuple
    execution_authority:bool=False
def _resource(x):
    if isinstance(x,dict) and "data" in x: return x.get("data")
    return x
def _rows(x):
    x=_resource(x)
    if isinstance(x,list): return tuple(y for y in x if isinstance(y,dict))
    if isinstance(x,dict):
        for key in ("holders","traders","list","items","rank"):
            v=x.get(key)
            if isinstance(v,list): return tuple(y for y in v if isinstance(y,dict))
        return (x,)
    return ()
def _wallet(row):
    for k in ("address","wallet_address","wallet","owner","maker"):
        v=row.get(k)
        if v: return str(v)
    return None
def normalize_current_gmgn_wallet_trader_intelligence(timeout_seconds=30.0):
    h,t=acquire_current_gmgn_holder_and_trader_pair(timeout_seconds)
    hr=_rows(h.raw); tr=_rows(t.raw); claims=[]
    for kind,rows in (("holder",hr),("trader",tr)):
        for row in rows: claims.append(ProviderClaim(_wallet(row),kind,"gmgn",dict(row),False))
    return WalletTraderIntelligence(h.token_address,len(hr),len(tr),tuple(claims),False)
