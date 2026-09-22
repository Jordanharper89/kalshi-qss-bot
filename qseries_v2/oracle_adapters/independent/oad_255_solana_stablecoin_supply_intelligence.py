import json, urllib.request
from .oad_252_crypto_independent_source_expansion_foundation import build_independent_crypto_observation
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
RPC="https://api.mainnet.solana.com"
MINTS={"USDC":"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v","USDT":"Es9vMFrzaCERmJfrF4H2FYD1zJ9xZK9gP8VfQJ7i2gX"}
def _rpc(method,params,timeout=15.0):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-Q-Series/1.0"})
 with urllib.request.urlopen(req,timeout=float(timeout)) as r: return json.loads(r.read().decode())
def acquire_solana_stablecoin_supply(symbol="USDC",timeout=15.0,rpc=_rpc):
 s=str(symbol).upper()
 if s not in MINTS: raise ValueError("unsupported certified stablecoin mint")
 d=rpc("getTokenSupply",[MINTS[s],{"commitment":"finalized"}],timeout)
 v=((d.get("result") or {}).get("value") or {})
 if not v.get("amount"): raise RuntimeError("Solana token supply unavailable")
 payload={"symbol":s,"mint":MINTS[s],"amount_raw":v.get("amount"),"decimals":v.get("decimals"),"ui_amount_string":v.get("uiAmountString")}
 return build_independent_crypto_observation(source_id="source.onchain.solana.stablecoin."+s.lower(),provider="solana_mainnet_rpc",source_class="stablecoin_supply",subject=s,observation_type="finalized_token_supply",payload=payload)
