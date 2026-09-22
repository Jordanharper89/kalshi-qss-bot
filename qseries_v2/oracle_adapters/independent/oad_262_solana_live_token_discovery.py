import json,urllib.request
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation,verify_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
ENDPOINTS=("https://api.dexscreener.com/token-profiles/latest/v1","https://api.dexscreener.com/token-boosts/latest/v1","https://api.dexscreener.com/token-boosts/top/v1")
def _get(url,timeout=20.0):
 req=urllib.request.Request(url,headers={"User-Agent":"Oracle-Q-Series/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r:return json.loads(r.read().decode())
def discover_live_solana_tokens(timeout_seconds=20.0,fetch=_get):
 seen={}; failures=[]
 for url in ENDPOINTS:
  try:
   d=fetch(url,timeout_seconds); rows=d if isinstance(d,list) else [d]
   for x in rows:
    if isinstance(x,dict) and str(x.get("chainId") or "").lower()=="solana" and x.get("tokenAddress"):
     a=str(x["tokenAddress"]); seen.setdefault(a,{"token_address":a,"profile_url":x.get("url"),"description":x.get("description"),"links":x.get("links") or [],"discovery_endpoint":url})
  except Exception as e: failures.append((url,type(e).__name__))
 if not seen: raise RuntimeError("no live Solana token identities discovered")
 o=build_independent_crypto_observation(source_id="source.dex.solana.token_discovery.latest",provider="dexscreener",source_class="token_discovery",subject="SOLANA",observation_type="solana_live_token_discovery",payload={"tokens":tuple(seen.values()),"token_count":len(seen),"endpoint_failures":tuple(failures)})
 if not verify_independent_crypto_observation(o): raise RuntimeError("provenance verification failed")
 return o
