from __future__ import annotations
import hashlib,json
from pathlib import Path

PROGRAMS={
 "METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "METEORA_DAMM":"cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
 "METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "METEORA_DYN":"Eo7WjKq67jJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
 "ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"}

NAMES={
 "METEORA_DBC":["swap","swap2"],
 "METEORA_DAMM":["swap","swap2"],
 "METEORA_DLMM":["swap2","swap_exact_out2"],
 "METEORA_DYN":[],
 "ORCA":["swap","swap_v2"]}

def disc(name):return hashlib.sha256(("global:"+name).encode()).digest()[:8]
DISC={v:{disc(n):n.upper() for n in ns} for v,ns in NAMES.items()}

def classify(venue,raw):
 name=DISC.get(venue,{}).get(raw[:8])
 return {"is_exact_swap":name is not None,"instruction_name":name,
  "discriminator_hex":raw[:8].hex() if len(raw)>=8 else raw.hex()}

def write(root):
 d={"revision":"USLS_065","programs":PROGRAMS,"instruction_names":NAMES,
  "dyn_policy":"OBSERVE_ONLY_UNTIL_CURRENT_OFFICIAL_SWAP_SCHEMA_IS_PHYSICALLY_VERIFIED",
  "unknown_retention":True,"execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_official_swap_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
