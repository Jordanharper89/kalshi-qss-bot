\

from __future__ import annotations
from dataclasses import dataclass
from .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaLiveDexPoolRegistry:
    query:str; pools:int; dexes:tuple; by_pair:tuple; provider:str; execution_authority:bool=False
def build_live_solana_dex_pool_registry(query="SOL/USDC",limit=100,timeout_seconds=20.0):
    x=acquire_solana_dex_liquidity(query=query,limit=limit,timeout=timeout_seconds)
    rows=tuple(x.payload.get("pairs") or ())
    by={}
    for r in rows:
        pair=str(r.get("pair_address") or "").strip(); dex=str(r.get("dex_id") or "unknown").strip().lower()
        if pair: by[pair]=dex
    if not by: raise RuntimeError("live Solana DEX registry contained no pair identities")
    return SolanaLiveDexPoolRegistry(str(query),len(by),tuple(sorted(set(by.values()))),tuple(sorted(by.items())),str(x.provider),False)
def dex_by_pair(registry):
    return dict(registry.by_pair)

