from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_instruction_transfer_evidence.json").read_text(encoding="utf-8"))
 rows=[];account_positions=Counter()
 for x in src["rows"]:
  if x["venue"]!="METEORA_DBC":continue
  ac=x["accounts"];aset=set(ac)
  touched=set()
  for t in x["transfers"]:
   if t.get("source") in aset:touched.add(t["source"])
   if t.get("destination") in aset:touched.add(t["destination"])
  positions=[i for i,a in enumerate(ac) if a in touched]
  for i in positions:account_positions[i]+=1
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],
   "account_count":len(ac),"transfer_count":x["transfer_count"],"transfer_touched_account_positions":positions,
   "transfer_touched_accounts":[ac[i] for i in positions],"execution_authority":False})
 return {"revision":"USLS_073","dbc_row_count":len(rows),
  "recurrent_transfer_touched_positions":[{"index":i,"count":c} for i,c in account_positions.most_common()],
  "rows":rows,"role_certified":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_dbc_physical_role_discovery.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
