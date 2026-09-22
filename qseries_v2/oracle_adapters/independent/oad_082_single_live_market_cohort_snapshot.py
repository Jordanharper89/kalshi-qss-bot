from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib,json

from qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _freeze(v):
    if isinstance(v,dict):
        return tuple((str(k),_freeze(v[k])) for k in sorted(v))
    if isinstance(v,list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v,tuple):
        return tuple(_freeze(x) for x in v)
    return v

def thaw_market(v):
    if isinstance(v,tuple) and all(isinstance(x,tuple) and len(x)==2 for x in v):
        return {k:thaw_market(x) for k,x in v}
    if isinstance(v,tuple):
        return tuple(thaw_market(x) for x in v)
    return v

@dataclass(frozen=True,slots=True)
class CurrentMarketCohortSnapshot:
    snapshot_id:str
    captured_at:str
    market_count:int
    markets:tuple

def capture_current_market_cohort(limit=1000):
    markets,_=fetch_current_open_kalshi_market_index(limit=limit)
    frozen=tuple(_freeze(m) for m in markets)
    payload=json.dumps(frozen,sort_keys=True,default=str,separators=(",",":"))
    sid=hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return CurrentMarketCohortSnapshot(
        sid,datetime.now(timezone.utc).isoformat(),len(frozen),frozen
    )

def snapshot_markets(snapshot):
    return tuple(thaw_market(x) for x in snapshot.markets)
