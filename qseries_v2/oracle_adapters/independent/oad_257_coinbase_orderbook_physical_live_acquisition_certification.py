from dataclasses import dataclass
from .oad_253_coinbase_exchange_liquidity_orderbook_intelligence import acquire_coinbase_orderbook
from .oad_252_crypto_independent_source_expansion_foundation import verify_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class CoinbaseOrderbookPhysicalCertification:
    product_id:str; best_bid:float; best_ask:float; spread:float; bid_levels:int; ask_levels:int
    provider:str; provenance_hash:str; certified:bool; execution_authority:bool=False
def certify_live_coinbase_orderbook(product_id="BTC-USD",timeout_seconds=20.0):
    x=acquire_coinbase_orderbook(product_id=product_id,level=2,timeout=timeout_seconds)
    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")
    p=x.payload; bid=float(p["best_bid"]); ask=float(p["best_ask"])
    if bid<=0 or ask<=0 or ask<bid: raise RuntimeError("invalid live Coinbase order book")
    return CoinbaseOrderbookPhysicalCertification(p["product_id"],bid,ask,float(p["spread"]),int(p["bid_levels"]),int(p["ask_levels"]),x.provider,x.provenance_hash,True,False)
