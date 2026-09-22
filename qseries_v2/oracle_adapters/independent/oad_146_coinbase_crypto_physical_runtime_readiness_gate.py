from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_143_coinbase_public_product_universe_discovery import discover_coinbase_public_products
from .oad_145_coinbase_market_native_canonical_persistence import persist_current_coinbase_market_native

READ_ONLY=True
PROBABILITY_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CoinbasePhysicalRuntimeGate:
    state:str
    discovered_products:int
    acquired_observations:int
    canonical_observations:int
    committed_new:int
    exact_readback:int
    market_native_reference:bool
    independent_evidence:bool
    runtime_ready:bool
    certified_at:str
    read_only:bool=True
    probability_enabled:bool=False
    execution_authority:bool=False

def run_coinbase_crypto_physical_runtime_readiness_gate(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,max_products=25):
    products=discover_coinbase_public_products(acquisition_timeout_seconds,limit=max_products)
    if not products: raise RuntimeError("Coinbase public product discovery returned zero usable products")
    p=persist_current_coinbase_market_native(root,timeout_seconds,acquisition_timeout_seconds,max_products)
    ready=p.raw_observations>0 and p.canonical_observations==p.raw_observations and p.exact_readback==p.canonical_observations
    if not ready: raise RuntimeError("Coinbase physical runtime readiness failed")
    return CoinbasePhysicalRuntimeGate("READY",len(products),p.raw_observations,p.canonical_observations,p.committed_new,p.exact_readback,True,False,True,datetime.now(timezone.utc).isoformat(),True,False,False)
