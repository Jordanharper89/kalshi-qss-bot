from __future__ import annotations
import json
PROGRAM_FAMILIES = (('PUMP_FUN', '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'), ('PUMP_SWAP', 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'), ('RAYDIUM_LAUNCHLAB', 'LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj'), ('RAYDIUM_V4', '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'), ('RAYDIUM_CLMM', 'CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK'), ('RAYDIUM_CPMM', 'CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C'), ('METEORA_DBC', 'dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN'), ('METEORA_DAMM', 'cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG'), ('METEORA_DLMM', 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'), ('METEORA_DYN', 'Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB'), ('ORCA', 'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc'), ('MOONIT', 'MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG'), ('BOOP_FUN', 'boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4'), ('HEAVEN', 'HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o'))
PROGRAM_IDS = tuple(pid for _, pid in PROGRAM_FAMILIES)
DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
PROGRAMS=PROGRAM_IDS

def contract(root):
 t=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/solana_rpc_transport_contract.json").read_text(encoding="utf-8"))
 subs=[]
 for i,pid in enumerate(PROGRAMS,1):
  subs.append({"jsonrpc":"2.0","id":i,"method":"logsSubscribe",
   "params":[{"mentions":[pid]},{"commitment":"confirmed"}]})
 return {"revision":"SULS_074","ws_url":t["derived_ws"],"programs":list(PROGRAMS),"subscriptions":subs,
  "birth_log_requirements":["Program log: Create Pool","Instruction: InitializePoolWithDynamicConfig"],
  "execution_authority":False,"read_only":True}
def write(root):
 d=contract(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
