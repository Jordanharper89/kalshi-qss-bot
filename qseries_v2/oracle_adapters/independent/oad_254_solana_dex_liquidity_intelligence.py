import json, urllib.parse, urllib.request
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
BASE="https://api.dexscreener.com/latest/dex/search"
def _get(url,timeout=15.0):
 req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())
def acquire_solana_dex_liquidity(query="SOL/USDC",limit=25,timeout=15.0,fetch=_get):
 d=fetch(BASE+"?q="+urllib.parse.quote(str(query)),timeout)
 pairs=[p for p in (d.get("pairs") or []) if str(p.get("chainId") or "").lower()=="solana"][:max(1,int(limit))]
 if not pairs: raise RuntimeError("no Solana DEX pairs returned")
 rows=[]
 for p in pairs:
  liq=p.get("liquidity") or {}; vol=p.get("volume") or {}; tx=p.get("txns") or {}
  rows.append({"dex_id":p.get("dexId"),"pair_address":p.get("pairAddress"),"base":(p.get("baseToken") or {}).get("address"),"quote":(p.get("quoteToken") or {}).get("address"),"price_usd":p.get("priceUsd"),"liquidity_usd":liq.get("usd"),"volume_h24":vol.get("h24"),"txns_h24":tx.get("h24"),"pair_created_at":p.get("pairCreatedAt")})
 return build_independent_crypto_observation(source_id="source.dex.solana.search."+str(query).lower().replace("/","_"),provider="dexscreener",source_class="dex_liquidity",subject=str(query),observation_type="solana_dex_pairs",payload={"pairs":rows,"pair_count":len(rows)})
