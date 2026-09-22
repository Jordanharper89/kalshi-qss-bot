import json,urllib.request,urllib.parse
from .oad_262_solana_live_token_discovery import discover_live_solana_tokens
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
BASE="https://api.dexscreener.com/token-pairs/v1/solana/"
def _get(url,timeout=20.0):
 req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r:return json.loads(r.read().decode())
def expand_live_solana_token_pools(token_address=None,timeout_seconds=20.0,fetch=_get):
 if token_address is None: token_address=discover_live_solana_tokens(timeout_seconds).payload["tokens"][0]["token_address"]
 rows=fetch(BASE+urllib.parse.quote(str(token_address),safe=""),timeout_seconds)
 if not isinstance(rows,list): raise RuntimeError("token-pairs response invalid")
 pools=[]
 for p in rows:
  if str(p.get("chainId") or "").lower()!="solana" or not p.get("pairAddress"): continue
  tx=p.get("txns") or {}; h24=tx.get("h24") or {}; liq=p.get("liquidity") or {}; vol=p.get("volume") or {}; pc=p.get("priceChange") or {}
  pools.append({"pair_address":p.get("pairAddress"),"dex_id":p.get("dexId"),"base_address":(p.get("baseToken") or {}).get("address"),"base_symbol":(p.get("baseToken") or {}).get("symbol"),"quote_address":(p.get("quoteToken") or {}).get("address"),"quote_symbol":(p.get("quoteToken") or {}).get("symbol"),"price_usd":p.get("priceUsd"),"liquidity_usd":liq.get("usd"),"volume_h24":vol.get("h24"),"buys_h24":h24.get("buys"),"sells_h24":h24.get("sells"),"price_change_h24":pc.get("h24"),"fdv":p.get("fdv"),"market_cap":p.get("marketCap"),"pair_created_at":p.get("pairCreatedAt")})
 if not pools: raise RuntimeError("no live Solana pools for discovered token")
 return build_independent_crypto_observation(source_id="source.dex.solana.token_pools."+str(token_address),provider="dexscreener",source_class="token_pool_liquidity",subject=str(token_address),observation_type="solana_token_pool_identity_liquidity",payload={"token_address":str(token_address),"pools":tuple(pools),"pool_count":len(pools)})
