from __future__ import annotations
from dataclasses import dataclass
from .oad_292_solana_bounded_multisource_token_universe import discover_bounded_multisource_solana_universe
from .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class TokenPoolIdentity:
 token_address:str; pair_address:str; dex_id:str|None; base_address:str|None; quote_address:str|None; sources:tuple
@dataclass(frozen=True,slots=True)
class SolanaIdentityRegistry:
 tokens:int; pools:int; identities:tuple; acquisition_failures:tuple; execution_authority:bool=False
def build_solana_token_pool_identity_registry(timeout_seconds=30.0,max_tokens=12):
 u=discover_bounded_multisource_solana_universe(timeout_seconds); identities={}; failures=[]
 for c in u.candidates[:max(1,int(max_tokens))]:
  try:
   o=expand_live_solana_token_pools(token_address=c.token_address,timeout_seconds=timeout_seconds)
   if str(o.payload.get("token_address"))!=c.token_address: raise RuntimeError("token identity mismatch")
   for p in tuple(o.payload.get("pools") or ()):
    pair=str(p.get("pair_address") or "").strip()
    if not pair: continue
    key=(c.token_address,pair)
    identities[key]=TokenPoolIdentity(c.token_address,pair,p.get("dex_id"),p.get("base_address"),p.get("quote_address"),c.sources)
  except Exception as e: failures.append((c.token_address,type(e).__name__,str(e)[:200]))
 if not identities: raise RuntimeError("no exact Solana token/pool identities resolved")
 rows=tuple(identities[k] for k in sorted(identities))
 return SolanaIdentityRegistry(len({x.token_address for x in rows}),len(rows),rows,tuple(failures),False)
