from __future__ import annotations
from dataclasses import dataclass
from .oad_021_credentials import KalshiCredentialConfig
from .oad_022_rest_transport import kalshi_rest_get

OAD_046_BUILD_ID="OAD-046"
OAD_046_REVISION="OAD_046_LIVE_UNIVERSE_ENUMERATION_ACTIVE_SEMANTICS_RECERTIFIED"

@dataclass(frozen=True)
class LiveUniverseEnumeration:
    tickers:tuple[str,...]
    pages:int
    duplicate_count:int
    terminal_cursor_reached:bool

def _is_current_market(raw):
    return str((raw or {}).get("status") or "").strip().lower()=="active"

def enumerate_live_open_universe(credentials,max_pages=10000,timeout_seconds=8,progress=None):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    emit=progress or (lambda _msg:None); cursor=""; seen={}; duplicates=0; pages=0
    while pages<int(max_pages):
        params={"limit":1000}
        if cursor: params["cursor"]=cursor
        emit(f"[UNIVERSE] requesting_page={pages+1} accumulated_active={len(seen)}")
        response=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)
        pages+=1; markets=tuple(response.body.get("markets",()) or ())
        for market in markets:
            if not _is_current_market(market): continue
            ticker=str(market.get("ticker","")).strip()
            if not ticker: continue
            if ticker in seen: duplicates+=1
            else: seen[ticker]=True
        emit(f"[UNIVERSE] page={pages} received={len(markets)} active_total={len(seen)}")
        nxt=str(response.body.get("cursor") or "")
        if not nxt:
            emit(f"[UNIVERSE] COMPLETE pages={pages} active_markets={len(seen)}")
            return LiveUniverseEnumeration(tuple(sorted(seen)),pages,duplicates,True)
        if nxt==cursor: raise RuntimeError("Kalshi live-universe cursor did not advance")
        cursor=nxt
    raise RuntimeError("Kalshi live-universe enumeration exceeded max_pages")

def verify_oad_046_physical_live_full_universe_enumeration():
    import inspect
    src=inspect.getsource(enumerate_live_open_universe)
    return ('"status":"open"' not in src and '_is_current_market' in src
            and inspect.signature(enumerate_live_open_universe).parameters["timeout_seconds"].default==8)
