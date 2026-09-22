from dataclasses import dataclass
from decimal import Decimal
from .oad_255_solana_stablecoin_supply_intelligence import acquire_solana_stablecoin_supply
from .oad_252_crypto_independent_source_expansion_foundation import verify_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaStablecoinPhysicalCertification:
    symbol:str; mint:str; amount_raw:str; decimals:int; ui_amount_string:str; provider:str; provenance_hash:str; certified:bool; execution_authority:bool=False
def certify_live_solana_stablecoin_supply(symbol="USDC",timeout_seconds=20.0):
    x=acquire_solana_stablecoin_supply(symbol=symbol,timeout=timeout_seconds)
    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")
    p=x.payload
    if Decimal(str(p["amount_raw"]))<=0: raise RuntimeError("invalid finalized stablecoin supply")
    return SolanaStablecoinPhysicalCertification(str(p["symbol"]),str(p["mint"]),str(p["amount_raw"]),int(p["decimals"]),str(p.get("ui_amount_string") or ""),x.provider,x.provenance_hash,True,False)
