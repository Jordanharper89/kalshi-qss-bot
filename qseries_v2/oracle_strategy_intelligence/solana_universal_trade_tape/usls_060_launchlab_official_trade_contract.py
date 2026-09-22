from __future__ import annotations
import json
from pathlib import Path

PROGRAM="LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
BUY_EXACT_IN=bytes([250,234,13,123,213,156,19,236])
BUY_EXACT_OUT=bytes([24,211,116,40,105,3,153,56])

ROLE_NAMES=("payer","authority","global_config","platform_config","pool_state",
"user_base_token","user_quote_token","base_vault","quote_vault","base_token_mint",
"quote_token_mint","base_token_program","quote_token_program","event_authority","program")

DISC={BUY_EXACT_IN:"BUY_EXACT_IN",BUY_EXACT_OUT:"BUY_EXACT_OUT"}

def classify(raw):
 name=DISC.get(raw[:8])
 return {"is_exact_trade":name is not None,"instruction_name":name,
  "discriminator_hex":raw[:8].hex() if len(raw)>=8 else raw.hex()}

def roles(accounts):
 return {name:(accounts[i] if i<len(accounts) else None) for i,name in enumerate(ROLE_NAMES)}

def write(root):
 d={"revision":"USLS_060","program_id":PROGRAM,
  "instructions":{"BUY_EXACT_IN":BUY_EXACT_IN.hex(),"BUY_EXACT_OUT":BUY_EXACT_OUT.hex()},
  "role_names":ROLE_NAMES,"official_idl_version":"0.2.0",
  "official_trade_surface":"BUY_ONLY_IN_CURRENT_IDL",
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_official_trade_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
