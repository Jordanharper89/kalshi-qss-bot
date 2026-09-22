from dataclasses import dataclass
from .oad_254_solana_dex_liquidity_intelligence import acquire_solana_dex_liquidity
from .oad_252_crypto_independent_source_expansion_foundation import verify_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaDexPhysicalCertification:
    query:str; pair_count:int; pair_addresses:tuple; dex_ids:tuple; provider:str; provenance_hash:str; certified:bool; execution_authority:bool=False
def certify_live_solana_dex_liquidity(query="SOL/USDC",limit=25,timeout_seconds=20.0):
    x=acquire_solana_dex_liquidity(query=query,limit=limit,timeout=timeout_seconds)
    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")
    rows=tuple(x.payload.get("pairs") or ())
    if not rows: raise RuntimeError("live Solana DEX response contained no pairs")
    addresses=tuple(str(r.get("pair_address") or "") for r in rows)
    if not any(addresses): raise RuntimeError("live Solana DEX pair identities missing")
    dexes=tuple(sorted({str(r.get("dex_id") or "") for r in rows if r.get("dex_id")}))
    return SolanaDexPhysicalCertification(str(query),len(rows),addresses,dexes,x.provider,x.provenance_hash,True,False)
