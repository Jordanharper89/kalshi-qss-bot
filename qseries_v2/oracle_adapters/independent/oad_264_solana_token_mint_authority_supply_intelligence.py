import json,urllib.request
from .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
RPC="https://api.mainnet.solana.com"
def _rpc(method,params,timeout=20.0):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(); req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r:d=json.loads(r.read().decode())
 if d.get("error"): raise RuntimeError("Solana RPC error: "+str(d["error"]))
 return d.get("result")
def acquire_solana_token_mint_state(token_address=None,timeout_seconds=20.0,rpc=_rpc):
 if token_address is None: token_address=expand_live_solana_token_pools(timeout_seconds=timeout_seconds).payload["token_address"]
 res=rpc("getAccountInfo",[str(token_address),{"encoding":"jsonParsed","commitment":"finalized"}],timeout_seconds); value=(res or {}).get("value")
 if not value: raise RuntimeError("mint account unavailable")
 data=value.get("data") or {}; parsed=data.get("parsed") if isinstance(data,dict) else None; info=(parsed or {}).get("info") or {}
 if not info: raise RuntimeError("mint account not JSON parsed")
 payload={"token_address":str(token_address),"slot":(res or {}).get("context",{}).get("slot"),"program":data.get("program"),"owner_program":value.get("owner"),"decimals":info.get("decimals"),"supply_raw":info.get("supply"),"mint_authority":info.get("mintAuthority"),"freeze_authority":info.get("freezeAuthority"),"is_initialized":info.get("isInitialized")}
 return build_independent_crypto_observation(source_id="source.onchain.solana.mint."+str(token_address),provider="solana_mainnet_rpc",source_class="token_mint_state",subject=str(token_address),observation_type="solana_token_mint_authority_supply",payload=payload)
