from dataclasses import dataclass
import json, urllib.request
from .oad_256_crypto_derivatives_open_interest_funding_intelligence import acquire_derivatives_state
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation,verify_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
HYPERLIQUID_INFO="https://api.hyperliquid.xyz/info"
def _hyperliquid_info(timeout_seconds=20.0):
    body=json.dumps({"type":"metaAndAssetCtxs"}).encode()
    req=urllib.request.Request(HYPERLIQUID_INFO,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})
    with urllib.request.urlopen(req,timeout=float(timeout_seconds)) as r: return json.loads(r.read().decode())
def acquire_hyperliquid_derivatives_state(asset="BTC",timeout_seconds=20.0):
    d=_hyperliquid_info(timeout_seconds)
    if not isinstance(d,list) or len(d)<2: raise RuntimeError("Hyperliquid meta/context response invalid")
    meta,ctxs=d[0],d[1]; universe=(meta or {}).get("universe") or []
    idx=next((i for i,x in enumerate(universe) if str(x.get("name") or "").upper()==str(asset).upper()),None)
    if idx is None or idx>=len(ctxs): raise RuntimeError("Hyperliquid asset context unavailable")
    c=ctxs[idx] or {}
    payload={"symbol":str(asset).upper(),"mark_price":c.get("markPx"),"index_price":c.get("oraclePx"),"open_interest":c.get("openInterest"),"funding_rate":c.get("funding"),"volume_24h":c.get("dayNtlVlm"),"provider_path":"hyperliquid_metaAndAssetCtxs"}
    if payload["open_interest"] is None or payload["funding_rate"] is None: raise RuntimeError("Hyperliquid derivatives fields missing")
    return build_independent_crypto_observation(source_id="source.derivatives.hyperliquid."+str(asset).lower(),provider="hyperliquid_public_info",source_class="derivatives_state",subject=str(asset).upper(),observation_type="open_interest_funding",payload=payload)
@dataclass(frozen=True,slots=True)
class DerivativesPhysicalCertification:
    provider:str; symbol:str; open_interest:str; funding_rate:str; provenance_hash:str; primary_provider_succeeded:bool; fallback_used:bool; certified:bool; execution_authority:bool=False
def acquire_resilient_derivatives_state(symbol="BTCUSDT",timeout_seconds=20.0):
    try:
        return acquire_derivatives_state(symbol=symbol,timeout=timeout_seconds),True,False
    except Exception as primary_error:
        asset=str(symbol).upper()
        if asset.endswith("USDT"): asset=asset[:-4]
        try:
            return acquire_hyperliquid_derivatives_state(asset,timeout_seconds),False,True
        except Exception as fallback_error:
            raise RuntimeError(f"all certified derivatives providers unavailable; primary={type(primary_error).__name__}; fallback={type(fallback_error).__name__}") from fallback_error
def certify_live_derivatives_state(symbol="BTCUSDT",timeout_seconds=20.0):
    x,primary,fallback=acquire_resilient_derivatives_state(symbol,timeout_seconds)
    if not verify_independent_crypto_observation(x): raise RuntimeError("OAD-252 provenance verification failed")
    p=x.payload
    if p.get("open_interest") is None or p.get("funding_rate") is None: raise RuntimeError("live derivatives state incomplete")
    return DerivativesPhysicalCertification(x.provider,str(p.get("symbol") or symbol),str(p["open_interest"]),str(p["funding_rate"]),x.provenance_hash,primary,fallback,True,False)
