from __future__ import annotations
from dataclasses import dataclass
from .oad_262_solana_live_token_discovery import discover_live_solana_tokens
from .oad_288_gmgn_clean_acquisition_boundary import acquire_current_gmgn_token
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaUniverseCandidate:
    token_address:str
    sources:tuple
    dexscreener_payload:dict|None
    gmgn_payload:dict|None

@dataclass(frozen=True,slots=True)
class SolanaBoundedUniverse:
    candidates:tuple
    dexscreener_count:int
    gmgn_count:int
    unique_tokens:int
    source_failures:tuple
    execution_authority:bool=False

def discover_bounded_multisource_solana_universe(timeout_seconds=30.0):
    merged={}; failures=[]; dex_count=0; gmgn_count=0
    try:
        d=discover_live_solana_tokens(timeout_seconds)
        for row in tuple(d.payload.get("tokens") or ()):
            a=str(row.get("token_address") or "").strip()
            if not a: continue
            dex_count+=1
            x=merged.setdefault(a,{"sources":set(),"dex":None,"gmgn":None})
            x["sources"].add("dexscreener"); x["dex"]=dict(row)
    except Exception as e:
        failures.append(("dexscreener",type(e).__name__,str(e)[:240]))
    try:
        g=acquire_current_gmgn_token(timeout_seconds=timeout_seconds,candidate_limit=5)
        a=str(getattr(g,"token_address","") or "").strip()
        if a:
            gmgn_count=1
            x=merged.setdefault(a,{"sources":set(),"dex":None,"gmgn":None})
            x["sources"].add("gmgn"); x["gmgn"]=dict(getattr(g,"payload",{}) or {})
    except Exception as e:
        failures.append(("gmgn",type(e).__name__,str(e)[:240]))
    if not merged: raise RuntimeError("no Solana universe candidates from certified sources")
    rows=tuple(SolanaUniverseCandidate(a,tuple(sorted(v["sources"])),v["dex"],v["gmgn"]) for a,v in sorted(merged.items()))
    return SolanaBoundedUniverse(rows,dex_count,gmgn_count,len(rows),tuple(failures),False)
