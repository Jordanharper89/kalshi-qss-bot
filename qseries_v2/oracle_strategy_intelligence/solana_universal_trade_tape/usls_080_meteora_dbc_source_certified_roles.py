from __future__ import annotations
import json
from pathlib import Path
ROLE={"pool_authority":0,"config":1,"pool":2,"user_in":3,"user_out":4,
      "base_vault":5,"quote_vault":6,"base_mint":7,"quote_mint":8,"trader":9}
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="METEORA_DBC":continue
  a=x["accounts"];r={k:(a[i] if i<len(a) else None) for k,i in ROLE.items()}
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],"roles":r,
   "role_state":"SOURCE_CERTIFIED_DBC_SWAPCTX_ROLES","execution_authority":False})
 return {"revision":"USLS_080","row_count":len(rows),"roles":ROLE,"rows":rows,
  "source_contract":"Meteora DBC SwapCtx","execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_dbc_source_certified_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
