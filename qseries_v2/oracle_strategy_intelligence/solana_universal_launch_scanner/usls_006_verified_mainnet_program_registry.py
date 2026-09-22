from __future__ import annotations
import json,urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAMS={
 "PUMP_FUN":("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P","OFFICIAL"),
 "PUMP_SWAP":("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA","OFFICIAL"),
 "RAYDIUM_LAUNCHLAB":("LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj","OFFICIAL"),
 "RAYDIUM_V4":("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8","OFFICIAL"),
 "RAYDIUM_CLMM":("CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK","OFFICIAL"),
 "RAYDIUM_CPMM":("CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C","OFFICIAL"),
 "METEORA_DBC":("dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN","OFFICIAL"),
 "METEORA_DAMM":("cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG","OFFICIAL"),
 "METEORA_DLMM":("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo","OFFICIAL"),
 "METEORA_DYN":("Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB","OFFICIAL"),
 "ORCA":("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc","OFFICIAL"),
 "MOONIT":("MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG","EXECUTABLE_CANDIDATE"),
 "BOOP_FUN":("boop8hVGQGqehUK2iVEMEnMrL5E7ZbEYKRBBRCkjGrf","EXECUTABLE_CANDIDATE"),
 "HEAVEN":("HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o","EXECUTABLE_CANDIDATE"),
}

def _rpc(method,params):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
 with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read())

def verify():
 ids=[v[0] for v in PROGRAMS.values()]
 d=_rpc("getMultipleAccounts",[ids,{"encoding":"base64","commitment":"confirmed"}])
 vals=(d.get("result") or {}).get("value") or []
 rows=[]
 for (fam,(pid,tier)),v in zip(PROGRAMS.items(),vals):
  rows.append({"family":fam,"program_id":pid,"source_tier":tier,
   "account_exists":v is not None,"executable":bool(v and v.get("executable")),
   "owner":v.get("owner") if v else None})
 return {"revision":"USLS_006","rpc":RPC,"programs":rows,
  "verified_executable_count":sum(1 for x in rows if x["executable"]),
  "execution_authority":False,"read_only":True}

def write(root):
 d=verify();p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/verified_mainnet_program_registry.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
